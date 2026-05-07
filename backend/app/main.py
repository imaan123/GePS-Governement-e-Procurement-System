from fastapi import FastAPI
from services.rule_engine.rule_engine_core import evaluate_bidder
from services.rule_engine.bidder_lookup import build_bidder_lookup
from database.db import DBManager, init_tables

app = FastAPI()
db = DBManager()


@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup"""
    init_tables()

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

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
