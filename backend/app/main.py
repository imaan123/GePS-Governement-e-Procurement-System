import json
import uuid
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from services.rule_engine.rule_engine_core import evaluate_bidder
from services.rule_engine.bidder_lookup import build_bidder_lookup
from database.db import DBManager, init_tables
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from services.Tender_extraction.tender_extraction import process_tender_pdf
from services.Tender_extraction.extract_eligibility_rules import (
    LLM_API_KEY,
    collect_pages,
    assign_ids,
    llm_extract,
    merge_and_dedup,
    rule_based_extract,
    upload_rules_to_db,
)

app = FastAPI()
db = DBManager()
UPLOAD_ROOT = Path(__file__).resolve().parents[1] / "uploads" / "tenders"
_tender_registry: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup"""
    init_tables()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000"],
  allow_credentials=True,



   allow_methods=["*"],
  allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


# In-memory job store for evaluation jobs. Replace with persistent queue for production.
_jobs: Dict[str, Dict[str, Any]] = {}


def _create_job_record() -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "results": None, "error": None}
    return job_id


def _set_job_status(job_id: str, status: str, results=None, error: str = None):
    rec = _jobs.get(job_id)
    if not rec:
        return
    rec["status"] = status
    if results is not None:
        rec["results"] = results
    if error is not None:
        rec["error"] = error


def _get_job(job_id: str):
    return _jobs.get(job_id)


def _get_tender_dir(tender_id: str) -> Path:
    return UPLOAD_ROOT / tender_id


def _run_tender_extraction_pipeline(tender_id: str, pdf_path: Path) -> Dict[str, Any]:
    tender_dir = _get_tender_dir(tender_id)
    tender_dir.mkdir(parents=True, exist_ok=True)

    extracted_document = process_tender_pdf(str(pdf_path))
    extracted_path = tender_dir / "tender_extracted.json"
    extracted_path.write_text(
        json.dumps(extracted_document, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    pages = collect_pages(extracted_document)
    rb_rules = rule_based_extract(pages)
    llm_rules: List[Dict[str, Any]] = []
    if LLM_API_KEY:
        try:
            llm_rules = llm_extract(pages)
        except Exception:
            llm_rules = []

    final_rules = assign_ids(merge_and_dedup(llm_rules, rb_rules))
    rules_path = tender_dir / "eligibility_rules.json"
    rules_path.write_text(
        json.dumps({"tender_id": tender_id, "rules": final_rules}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    upload_rules_to_db(final_rules)

    record = {
        "tender_id": tender_id,
        "pdf_path": str(pdf_path),
        "tender_dir": str(tender_dir),
        "extracted_document_path": str(extracted_path),
        "rules_path": str(rules_path),
        "rules_count": len(final_rules),
    }
    _tender_registry[tender_id] = record
    return record


def _process_single_bidder(bidder_id: str):
    """Synchronous helper to evaluate one bidder and persist results."""
    local_db = DBManager()
    try:
        rules = local_db.fetch_rules()
        bidder_fields = local_db.fetch_bidder_fields(bidder_id=bidder_id)
        bidder_lookup, source_lookup = build_bidder_lookup(bidder_fields)
        results = evaluate_bidder(rules, bidder_lookup, bidder_fields, source_lookup)
        local_db.store_evaluation_results(bidder_id, results)
        return {"bidder_id": bidder_id, "results": results}
    finally:
        local_db.close()


async def _run_evaluation_job(job_id: str, tender_id: str, bidder_ids: List[str]):
    _set_job_status(job_id, "running")
    all_results = []
    try:
        for bidder_id in bidder_ids:
            # run CPU/IO work in thread to avoid blocking event loop
            res = await asyncio.to_thread(_process_single_bidder, bidder_id)
            all_results.append(res)

        _set_job_status(job_id, "completed", results={"tender_id": tender_id, "bidders": all_results})
    except Exception as e:
        _set_job_status(job_id, "failed", error=str(e))

@app.post("/evaluate/{bidder_id}")
def evaluate_bidder_endpoint(bidder_id: str):
    """
    Evaluate a bidder against all rules
    
    Args:
        bidder_id: The bidder identifier
        
    Returns:
        dict with evaluation results and verdict
    """
    try:
        rules = db.fetch_rules()
        bidder_fields = db.fetch_bidder_fields(bidder_id=bidder_id)
        
        if not bidder_fields:
            return {
                "error": f"No bidder fields found for {bidder_id}",
                "bidder_id": bidder_id
            }
        
        bidder_lookup, source_lookup = build_bidder_lookup(bidder_fields)
        results = evaluate_bidder(rules, bidder_lookup, bidder_fields, source_lookup)
        
        # Store results in database
        db.store_evaluation_results(bidder_id, results)
        
        return {
            "bidder_id": bidder_id,
            "results": results
        }
    except Exception as e:
        return {
            "error": str(e),
            "bidder_id": bidder_id
        }
    finally:
        db.close()


@app.get("/rules")
def get_all_rules():
    """Get all rules"""
    try:
        rules = db.fetch_rules()
        return {
            "total_rules": len(rules),
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "rule_type": r.rule_type,
                    "category": r.category,
                    "priority": r.priority
                }
                for r in rules
            ]
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@app.post("/api/tender/upload")
async def upload_tender(tender_file: UploadFile = File(...)):
    """Upload a tender PDF, extract eligibility rules, store only the final rules in DB, and keep the raw extraction locally."""
    safe_name = Path(tender_file.filename or "tender.pdf").name
    if not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    tender_id = f"T-{uuid.uuid4().hex[:12].upper()}"
    tender_dir = _get_tender_dir(tender_id)
    tender_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = tender_dir / safe_name
    contents = await tender_file.read()
    pdf_path.write_bytes(contents)

    try:
        record = _run_tender_extraction_pipeline(tender_id, pdf_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Tender extraction failed: {exc}")

    return {
        "message": "Tender uploaded and rules extracted",
        **record,
    }


@app.get("/api/tender/{tender_id}/rules")
def get_tender_rules(tender_id: str):
    """Return the locally stored final rules for a tender."""
    record = _tender_registry.get(tender_id)
    rules_path = Path(record["rules_path"]) if record else (_get_tender_dir(tender_id) / "eligibility_rules.json")

    if not rules_path.exists():
        raise HTTPException(status_code=404, detail=f"No extracted rules found for tender {tender_id}")

    payload = json.loads(rules_path.read_text(encoding="utf-8"))
    rules = payload.get("rules", []) if isinstance(payload, dict) else []
    return {
        "tender_id": tender_id,
        "total_rules": len(rules),
        "rules": rules,
    }


@app.post("/evaluate")
async def evaluate_tender_endpoint(payload: Dict[str, Any]):
    """Start evaluation job for one or more bidders.

    Payload should be: { "tender_id": "T-...", "bidder_ids": ["BID-1", "BID-2"] }
    Returns a `job_id` which can be used to query status/results.
    """
    tender_id = payload.get("tender_id")
    bidder_ids = payload.get("bidder_ids") or []
    if not bidder_ids:
        return {"error": "No bidder_ids provided"}

    job_id = _create_job_record()
    # schedule background evaluation
    asyncio.create_task(_run_evaluation_job(job_id, tender_id, bidder_ids))
    return {"job_id": job_id}


@app.get("/evaluate/{job_id}/status")
def get_evaluation_status(job_id: str):
    job = _get_job(job_id)
    if not job:
        return {"error": "job not found"}
    return {"job_id": job_id, "status": job["status"], "error": job.get("error")}


@app.get("/evaluate/{job_id}/results")
def get_evaluation_results(job_id: str):
    job = _get_job(job_id)
    if not job:
        return {"error": "job not found"}
    if job["status"] != "completed":
        return {"job_id": job_id, "status": job["status"], "results": job.get("results")}
    return {"job_id": job_id, "status": job["status"], "results": job.get("results")}
