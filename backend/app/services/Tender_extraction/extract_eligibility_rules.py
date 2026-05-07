from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── config ────────────────────────────────────────────────────────────────────
INPUT_JSON = "tender_extracted.json"
OUTPUT_JSON = "eligibility_rules_qwen.json"

# Support both local Qwen/LM-Studio (set by run_with_qwen.sh) and OpenRouter
LLM_API_KEY  = os.getenv("QWEN_API_KEY")  or os.getenv("OPENROUTER_API_KEY", "")
LLM_BASE_URL = os.getenv("QWEN_BASE_URL") or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL    = os.getenv("QWEN_MODEL")    or os.getenv("LLM_MODEL", "qwen/qwen-2.5-7b-instruct")

# Keep legacy name so upload_rules_to_db / other references still compile
OPENROUTER_API_KEY  = LLM_API_KEY
OPENROUTER_BASE_URL = LLM_BASE_URL

LLM_CHUNK_CHARS = 12000

# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Rule:
    rule_id: str
    rule_type: str                     # deterministic | boolean
    category: str                      # mandatory | optional
    priority: int
    dependencies: Optional[Dict[str, Any]]
    rule_definition: Dict[str, Any]    # {field, operator, value}
    confidence: float
    original_text: Optional[str] = None
    source_page: Optional[int] = None
    status: str = "extracted"


# ── I/O ───────────────────────────────────────────────────────────────────────

def load_input(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def collect_pages(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    pages: List[Dict[str, Any]] = []

    for page in data.get("pages", []):
        parts = [page.get(k, "") for k in ("text", "ocr_text") if page.get(k)]

        ocr_field = page.get("ocr")
        if not parts and isinstance(ocr_field, list):
            for ocr_entry in ocr_field:
                if isinstance(ocr_entry, dict):
                    res = ocr_entry.get("res", {})
                    rec_texts = res.get("rec_texts", [])
                    if rec_texts:
                        parts.append(" ".join(t for t in rec_texts if t and t.strip()))

        chunk = page.get("chunk") or {}
        if isinstance(chunk, dict) and chunk.get("text"):
            parts.append(chunk["text"])

        combined = "\n".join(parts).strip()
        if combined:
            pages.append({"page": page.get("page"), "text": combined})

    if not pages and data.get("combined_text"):
        pages.append({"page": None, "text": data["combined_text"]})

    return pages


# ── signals ───────────────────────────────────────────────────────────────────

ELIGIBILITY_SECTION_PATTERNS = [
    r"eligibility\s+criter",
    r"pre[\s-]?qualification",
    r"qualifying\s+criter",
    r"qualification\s+criter",
    r"bid\s+qualification",
    r"technical\s+qualification",
    r"financial\s+qualification",
    r"minimum\s+eligibility",
    r"bidder.*eligib",
]

STRONG_RULE_PATTERNS = [
    r"\b(shall|must|required|should)\b.{0,80}(submit|provide|furnish|have|possess|demonstrate)",
    r"\b(minimum|at\s+least|not\s+less\s+than)\b.{0,60}(crore|lakh|year|project|experience|turnover|work)",
    r"\bturnover\b.{0,60}(crore|lakh|rs\.?|inr)",
    r"\bexperience\b.{0,60}\d+\s*(year|project|work)",
    r"\b(gst|pan|emd|epf|esic|iso|msme|nsic)\b.{0,40}(number|certificate|registration|required)",
    r"\bbid\s+security\b",
    r"\bearnest\s+money\b",
    r"\bsimilar\s+(work|project)",
    r"\baverage\s+annual\s+turnover",
    r"\bnet\s+worth\b",
    r"\bsolvency\b",
    r"\bwork\s+order.{0,40}(value|amount|worth)",
]


def is_eligibility_section(text: str) -> bool:
    lower = text[:500].lower()
    return any(re.search(p, lower) for p in ELIGIBILITY_SECTION_PATTERNS)


def has_strong_rule(text: str) -> bool:
    lower = text.lower()
    return any(re.search(p, lower) for p in STRONG_RULE_PATTERNS)


# ── helpers ──────────────────────────────────────────────────────────────────

def normalize_currency(text: str) -> Tuple[Optional[int], Optional[str]]:
    lower = text.lower().replace(",", " ")
    m = re.search(r"(?:rs\.?|inr|₹)?\s*([\d.]+)\s*(crore|cr|lakh|lac|lakhs|lacs)\b", lower)
    if m:
        num = float(m.group(1))
        if m.group(2) in {"crore", "cr"}:
            return int(num * 10000000), "INR"
        return int(num * 100000), "INR"
    return None, None


def extract_time_period(text: str) -> Optional[str]:
    lower = text.lower()
    for pat, fmt in [
        (r"last\s+(\d+)\s+financial\s+years?", "last_{}_financial_years"),
        (r"previous\s+(\d+)\s+financial\s+years?", "previous_{}_financial_years"),
        (r"last\s+(\d+)\s+years?", "last_{}_years"),
        (r"within.{0,10}last\s+(\d+)\s+years?", "last_{}_years"),
    ]:
        m = re.search(pat, lower)
        if m:
            return fmt.format(m.group(1))
    return None


def infer_rule_category(text: str) -> str:
    """
    Your requested 'category' is mandatory/optional.
    """
    lower = text.lower()
    if any(w in lower for w in ["optional", "may ", "preferred", "desirable"]):
        return "optional"
    return "mandatory"


def infer_rule_type(text: str) -> str:
    """
    Your requested 'rule_type' is deterministic/boolean.
    """
    lower = text.lower()

    if any(w in lower for w in ["gst", "pan", "emd", "iso", "certificate", "registration", "affidavit", "declaration"]):
        return "boolean"

    if any(w in lower for w in ["turnover", "experience", "project", "work", "years", "lakh", "crore", "net worth", "solvency"]):
        return "deterministic"

    return "deterministic"


def infer_field(text: str) -> str:
    lower = text.lower()

    if "turnover" in lower:
        return "average_turnover"
    if "net worth" in lower:
        return "net_worth"
    if "solvency" in lower:
        return "solvency"
    if "similar" in lower and ("project" in lower or "work" in lower):
        return "similar_projects_completed"
    if "experience" in lower:
        return "experience_years"
    if "gst" in lower:
        return "gst_registration"
    if "pan" in lower:
        return "pan_registration"
    if "emd" in lower:
        return "emd_payment"
    if "iso" in lower:
        return "iso_certification"
    if "certificate" in lower:
        return "certificate_required"

    return "eligibility_criterion"


def infer_operator_and_value(text: str) -> Tuple[str, Any, Optional[str], Optional[str]]:
    """
    Returns: operator, value, unit, time_period
    """
    lower = text.lower()
    time_period = extract_time_period(text)

    currency_val, currency_unit = normalize_currency(text)
    if currency_val is not None:
        return ">=", currency_val, currency_unit, time_period

    m = re.search(r"(?:at\s+least|minimum|not\s+less\s+than|>=)\s*([0-9]+(?:\.[0-9]+)?)", lower)
    if m:
        n = float(m.group(1))
        value = int(n) if n.is_integer() else n
        if "project" in lower or "work" in lower:
            return ">=", value, "projects", time_period
        if "year" in lower:
            return ">=", value, "years", time_period
        return ">=", value, None, time_period

    if any(w in lower for w in ["gst", "pan", "emd", "iso", "certificate", "registration", "affidavit", "declaration"]):
        return "required", True, None, time_period

    return "text", text.strip(), None, time_period


# ── rule-based fallback ──────────────────────────────────────────────────────

def rule_based_extract(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rules: List[Dict[str, Any]] = []
    seen = set()
    idx = 1

    for page in pages:
        page_no = page["page"]
        for sent in re.split(r"(?<=[.;])\s+|\n+", page["text"]):
            sent = sent.strip()
            if len(sent) < 25 or not has_strong_rule(sent):
                continue

            key = re.sub(r"\s+", " ", sent.lower())
            if key in seen:
                continue
            seen.add(key)

            category = infer_rule_category(sent)
            rule_type = infer_rule_type(sent)
            operator, value, unit, time_period = infer_operator_and_value(sent)
            field = infer_field(sent)

            if operator == "text" and len(str(value).strip()) < 15:
                continue

            rule = Rule(
                rule_id=f"R{idx}",
                rule_type=rule_type,
                category=category,
                priority=1 if category == "mandatory" else 2,
                dependencies=None,
                rule_definition={
                    "field": field,
                    "operator": operator,
                    "value": value,
                    "unit": unit,
                    "time_period": time_period,
                },
                confidence=0.80 if rule_type == "boolean" else 0.88,
                original_text=sent,
                source_page=page_no,
            )
            rules.append(asdict(rule))
            idx += 1

    return rules


# ── Qwen via OpenRouter ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an expert in government tender analysis.

Extract ONLY real eligibility / pre-qualification criteria from the tender text.

Return ONLY valid JSON with this schema:
{
  "rules": [
    {
      "rule_type": "deterministic|boolean",
      "category": "mandatory|optional",
      "priority": 1,
      "dependencies": {
        "operator": "AND|OR|NOT",
        "rules": []
      },
      "rule_definition": {
        "field": "short_snake_case_name",
        "operator": ">=|<=|<|>|==|required|text",
        "value": "number|boolean|string",
        "unit": "INR|years|projects|null",
        "time_period": "string|null"
      },
      "confidence": 0.0,
      "original_text": "exact sentence from the tender",
      "source_page": 1
    }
  ]
}

Rules:
- Include ONLY eligibility / qualification requirements.
- Exclude scope of work, payment terms, schedule, contact details, and general headings.
- For money, convert crore/lakh to integers in INR.
- For compliance items like GST/ISO/PAN/EMD, use operator "required" and value true.
- For quantified criteria, use deterministic rules.
- For conditionals, encode logic in dependencies when needed.
- If no rules exist, return {"rules": []}.
"""


def _call_llm(text_chunk: str) -> List[Dict[str, Any]]:
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("Run: pip install openai")

    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text_chunk},
                ],
                temperature=0,
                extra_headers={
                    "HTTP-Referer": "https://github.com/local",
                    "X-Title": "TenderRulesExtractor",
                },
            )
            content = (resp.choices[0].message.content or "{}").strip()
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content)
            return json.loads(content).get("rules", [])
        except json.JSONDecodeError as e:
            print(f"  [LLM] JSON parse error (attempt {attempt + 1}): {e}")
            time.sleep(2)
        except Exception as e:
            print(f"  [LLM] Error (attempt {attempt + 1}): {e}")
            time.sleep(3)

    return []


def llm_extract(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    relevant = [p for p in pages if len(p.get("text", "").strip()) > 50]
    print(f"  [LLM] {len(relevant)} pages to process.")

    batches: List[str] = []
    current = ""

    for p in relevant:
        snippet = f"[Page {p['page']}]\n{p['text'][:3000]}\n\n"
        if current and len(current) + len(snippet) > LLM_CHUNK_CHARS:
            batches.append(current)
            current = snippet
        else:
            current += snippet

    if current:
        batches.append(current)

    print(f"  [LLM] {len(batches)} batch(es)...")

    all_rules: List[Dict[str, Any]] = []
    for i, batch in enumerate(batches, 1):
        print(f"  [LLM] Batch {i}/{len(batches)}...", end=" ", flush=True)
        rules = _call_llm(batch)
        print(f"got {len(rules)} rules")
        all_rules.extend(rules)
        if i < len(batches):
            time.sleep(1)

    return all_rules


# ── post-processing ──────────────────────────────────────────────────────────

def _is_garbage(rule: Dict[str, Any]) -> bool:
    rd = rule.get("rule_definition", {})
    if not isinstance(rd, dict):
        return True

    field = str(rd.get("field", "")).strip()
    operator = str(rd.get("operator", "")).strip()
    value = rd.get("value", None)

    if not field:
        return True

    if operator == "text":
        val = str(value).strip()
        if len(val) < 15:
            return True
        if re.match(r"^\d+\.\d+", val):
            return True
        if rule.get("confidence", 1.0) < 0.65:
            return True

    return False


def assign_ids(rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for i, rule in enumerate(rules, start=1):
        rule["rule_id"] = f"R{i}"
        rule.setdefault("status", "extracted")
        rule.setdefault("dependencies", None)
        rule.setdefault("original_text", None)
        rule.setdefault("source_page", None)
        rule.setdefault("priority", 1 if rule.get("category") == "mandatory" else 2)
    return rules


def merge_and_dedup(llm_rules: List[Dict], rb_rules: List[Dict]) -> List[Dict]:
    seen = set()
    merged: List[Dict] = []

    for rule in llm_rules + rb_rules:
        if _is_garbage(rule):
            continue

        rd = rule.get("rule_definition", {})
        key = (
            str(rd.get("field", "")).lower().strip(),
            str(rd.get("operator", "")).lower().strip(),
            str(rd.get("value", "")).lower().strip() if not isinstance(rd.get("value"), (int, float, bool)) else str(rd.get("value")),
            str(rule.get("original_text", "")).lower().strip(),
            str(rule.get("source_page", "")),
        )

        if key in seen:
            continue
        seen.add(key)
        merged.append(rule)

    return merged


# ── database upload ───────────────────────────────────────────────────────────

def upload_rules_to_db(rules: List[Dict[str, Any]], db_url: str = "postgresql://postgres:password@localhost:5432/db") -> None:
    """
    Upload extracted eligibility rules to the PostgreSQL `rules` table.
    Creates the table if it does not exist.
    """
    try:
        from sqlalchemy import create_engine, text as sa_text
    except ImportError:
        raise RuntimeError("Run: pip install sqlalchemy psycopg2-binary")

    engine = create_engine(db_url)

    with engine.begin() as conn:
        conn.execute(sa_text("""
            CREATE TABLE IF NOT EXISTS rules (
                rule_id TEXT PRIMARY KEY,
                rule_type TEXT,
                category TEXT,
                priority INT,
                dependencies JSONB,
                rule_definition JSONB,
                original_text TEXT,
                source_page INT,
                source_section TEXT,
                confidence FLOAT
            )
        """))

    insert_sql = sa_text("""
        INSERT INTO rules (
            rule_id, rule_type, category, priority,
            dependencies, rule_definition, original_text,
            source_page, source_section, confidence
        ) VALUES (
            :rule_id, :rule_type, :category, :priority,
            :dependencies, :rule_definition, :original_text,
            :source_page, :source_section, :confidence
        )
        ON CONFLICT (rule_id) DO UPDATE SET
            rule_type       = EXCLUDED.rule_type,
            category        = EXCLUDED.category,
            priority        = EXCLUDED.priority,
            dependencies    = EXCLUDED.dependencies,
            rule_definition = EXCLUDED.rule_definition,
            original_text   = EXCLUDED.original_text,
            source_page     = EXCLUDED.source_page,
            source_section  = EXCLUDED.source_section,
            confidence      = EXCLUDED.confidence
    """)

    uploaded = 0
    skipped = 0

    with engine.begin() as conn:
        for rule in rules:
            try:
                conn.execute(insert_sql, {
                    "rule_id":         rule.get("rule_id"),
                    "rule_type":       rule.get("rule_type"),
                    "category":        rule.get("category"),
                    "priority":        rule.get("priority"),
                    "dependencies":    json.dumps(rule.get("dependencies")) if rule.get("dependencies") is not None else None,
                    "rule_definition": json.dumps(rule.get("rule_definition")),
                    "original_text":   rule.get("original_text"),
                    "source_page":     rule.get("source_page"),
                    "source_section":  rule.get("source_section"),
                    "confidence":      rule.get("confidence"),
                })
                uploaded += 1
            except Exception as e:
                print(f"  [DB] Failed to insert {rule.get('rule_id')}: {e}")
                skipped += 1

    print(f"  [DB] Uploaded {uploaded} rules, skipped {skipped}.")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"Loading {INPUT_JSON}...")
    data = load_input(INPUT_JSON)
    pages = collect_pages(data)
    print(f"  {len(pages)} pages loaded.")

    print("\nStep 1: Strict rule-based extraction...")
    rb_rules = rule_based_extract(pages)
    print(f"  {len(rb_rules)} rules found.")

    llm_rules: List[Dict[str, Any]] = []
    if LLM_API_KEY:
        print(f"\nStep 2: LLM extraction via {LLM_MODEL} ({LLM_BASE_URL})...")
        try:
            llm_rules = llm_extract(pages)
            print(f"  {len(llm_rules)} LLM rules found.")
        except Exception as e:
            print(f"  LLM failed: {e}. Using rule-based only.")
    else:
        print("\nStep 2: Skipped (no QWEN_API_KEY / OPENROUTER_API_KEY set).")

    print("\nStep 3: Merging + deduplicating...")
    final = merge_and_dedup(llm_rules, rb_rules)
    final = assign_ids(final)
    print(f"  Final: {len(final)} unique rules.")

    Path(OUTPUT_JSON).write_text(
        json.dumps({"rules": final}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nSaved to {OUTPUT_JSON}")

    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/db")
    print(f"\nStep 4: Uploading rules to database ({db_url})...")
    try:
        upload_rules_to_db(final, db_url=db_url)
    except Exception as e:
        print(f"  [DB] Upload failed: {e}")

    print("\n── Sample Rules ───────────────────────────────────────────────")
    for r in final[:10]:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        print("-" * 50)


if __name__ == "__main__":
    main()