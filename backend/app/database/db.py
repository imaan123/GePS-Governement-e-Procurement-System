import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.rule_schema import Rule
from models.bidder_schema import BidderField
from models.evaluation_schema import EvaluationResult, EvaluationSummary


DATABASE_URL = "postgresql://postgres:password@localhost:5432/db"

engine = create_engine(DATABASE_URL)

def init_tables():

    with engine.begin() as conn:

        conn.execute(text("""
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

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS bidder_fields (
            bidder_id TEXT,
            field_name TEXT,
            field_type TEXT,
            value JSONB,
            source_document TEXT,
            source_page INT,
            source_section TEXT,
            original_text TEXT,
            confidence FLOAT
        )
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS evaluation_results (
            id SERIAL PRIMARY KEY,
            bidder_id TEXT NOT NULL,
            rule_id TEXT NOT NULL,
            field TEXT,
            bidder_value TEXT,
            expected_value TEXT,
            result TEXT NOT NULL,
            rule_type TEXT,
            confidence FLOAT,
            source_document TEXT,
            source_page INT,
            source_section TEXT,
            bidder_original_text TEXT,
            bidder_confidence FLOAT,
            rule_original_text TEXT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS evaluation_summary (
            id SERIAL PRIMARY KEY,
            bidder_id TEXT NOT NULL,
            verdict TEXT NOT NULL,
            mandatory_count INT,
            total_rules INT,
            passed_count INT,
            failed_count INT,
            needs_review_count INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class DBManager:

    def __init__(self):
        self.session = SessionLocal()

    # -----------------------------
    # FETCH RULES
    # -----------------------------
    def fetch_rules(self):

        query = text("""
            SELECT
                rule_id,
                rule_type,
                category,
                priority,
                dependencies,
                rule_definition,
                original_text,
                source_page,
                source_section,
                confidence
            FROM rules
            ORDER BY priority ASC
        """)

        rows = self.session.execute(query)

        rules = []

        for row in rows:

            rule = Rule(
                rule_id=row.rule_id,
                rule_type=row.rule_type,
                category=row.category,
                priority=row.priority,
                dependencies=row.dependencies,
                rule_definition=row.rule_definition,
                original_text=row.original_text,
                source_page=row.source_page,
                source_section=row.source_section,
                confidence=row.confidence
            )

            rules.append(rule)

        return rules

    # -----------------------------
    # FETCH BIDDER FIELDS
    # -----------------------------
    def fetch_bidder_fields(self, bidder_id):

        query = text("""
            SELECT
                field_name,
                field_type,
                value,
                source_document,
                source_page,
                source_section,
                original_text,

                confidence

            FROM bidder_fields
            WHERE bidder_id = :bidder_id
        """)

        rows = self.session.execute(
            query,
            {"bidder_id": bidder_id}
        )

        bidder_fields = []

        for row in rows:

            field = BidderField(

                field_name=row.field_name,
                field_type=row.field_type,

                value=row.value,

                source_document=row.source_document,
                source_page=row.source_page,
                source_section=row.source_section,
                original_text=row.original_text,

                confidence=row.confidence
            )

            bidder_fields.append(field)

        return bidder_fields

    # -----------------------------
    # STORE EVALUATION RESULTS
    # -----------------------------
    def store_evaluation_results(self, bidder_id, results):

        summary_entry = None
        evaluation_records = []

        for result in results:
            if "summary" in result:
                summary_entry = result["summary"]
                continue

            eval_result = EvaluationResult(
                bidder_id=bidder_id,
                rule_id=result.get("rule_id"),
                field=result.get("field"),
                bidder_value=str(result.get("bidder_value")),
                expected_value=str(result.get("expected_value")),
                result=result.get("result"),
                rule_type=result.get("Rule type"),
                confidence=result.get("Confidence", 0.0),
                source_document=result.get("Bidder source document"),
                source_page=result.get("Bidder source page"),
                source_section=result.get("Bidder source section"),
                bidder_original_text=result.get("Bidder original text"),
                bidder_confidence=result.get("Bidder confidence"),
                rule_original_text=result.get("Original rule"),
                metadata={"full_result": result}
            )
            evaluation_records.append(eval_result)

        # Insert individual evaluation results
        for record in evaluation_records:
            query = text("""
                INSERT INTO evaluation_results (
                    bidder_id, rule_id, field, bidder_value, expected_value,
                    result, rule_type, confidence, source_document, source_page,
                    source_section, bidder_original_text, bidder_confidence,
                    rule_original_text, metadata
                ) VALUES (
                    :bidder_id, :rule_id, :field, :bidder_value, :expected_value,
                    :result, :rule_type, :confidence, :source_document, :source_page,
                    :source_section, :bidder_original_text, :bidder_confidence,
                    :rule_original_text, :metadata
                )
            """)

            self.session.execute(
                query,
                {
                    "bidder_id": record.bidder_id,
                    "rule_id": record.rule_id,
                    "field": record.field,
                    "bidder_value": record.bidder_value,
                    "expected_value": record.expected_value,
                    "result": record.result,
                    "rule_type": record.rule_type,
                    "confidence": record.confidence,
                    "source_document": record.source_document,
                    "source_page": record.source_page,
                    "source_section": record.source_section,
                    "bidder_original_text": record.bidder_original_text,
                    "bidder_confidence": record.bidder_confidence,
                    "rule_original_text": record.rule_original_text,
                    "metadata": json.dumps(record.metadata) if record.metadata else None,
                }
            )

        # Insert summary if available
        if summary_entry:
            passed = sum(1 for r in evaluation_records if r.result == "PASS")
            failed = sum(1 for r in evaluation_records if r.result == "FAIL")
            needs_review = sum(1 for r in evaluation_records if r.result in {"NEEDS_REVIEW", "UNKNOWN"})

            summary_query = text("""
                INSERT INTO evaluation_summary (
                    bidder_id, verdict, mandatory_count, total_rules,
                    passed_count, failed_count, needs_review_count
                ) VALUES (
                    :bidder_id, :verdict, :mandatory_count, :total_rules,
                    :passed_count, :failed_count, :needs_review_count
                )
            """)

            self.session.execute(
                summary_query,
                {
                    "bidder_id": bidder_id,
                    "verdict": summary_entry.get("verdict"),
                    "mandatory_count": summary_entry.get("mandatory_count"),
                    "total_rules": len(evaluation_records),
                    "passed_count": passed,
                    "failed_count": failed,
                    "needs_review_count": needs_review,
                }
            )

        self.session.commit()

    # -----------------------------
    # CLOSE SESSION
    # -----------------------------
    def close(self):
        self.session.close()

# def store_results(bidder_id, results):

#     cur = conn.cursor()

#     for r in results:

#         cur.execute("""
#         INSERT INTO evaluation_results
#         (bidder_id, rule_id, result, confidence, evidence)
#         VALUES (%s,%s,%s,%s,%s)
#         """,
#         (
#             bidder_id,
#             r["rule_id"],
#             r["result"],
#             r["confidence"],
#             json.dumps(r["evidence"])
#         ))

#     conn.commit()