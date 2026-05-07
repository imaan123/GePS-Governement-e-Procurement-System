from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.rule_schema import Rule
from models.bidder_schema import BidderField


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