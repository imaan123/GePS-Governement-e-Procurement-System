# from sentence_transformers import SentenceTransformer, util

# model = SentenceTransformer("all-MiniLM-L6-v2")


# def _candidate_text(candidate, fallback_label=""):

#     if isinstance(candidate, str):
#         return candidate

#     if isinstance(candidate, dict):
#         parts = [
#             fallback_label,
#             candidate.get("field_name"),
#             candidate.get("name"),
#             candidate.get("document"),
#             candidate.get("snippet"),
#             candidate.get("value"),
#         ]

#         return " ".join(str(part) for part in parts if part not in (None, ""))

#     return str(candidate)

# def match_field(rule_field, bidder_fields):

#     if isinstance(bidder_fields, dict):
#         candidate_keys = list(bidder_fields.keys())
#         candidate_texts = [
#             _candidate_text(bidder_fields[key], key)
#             for key in candidate_keys
#         ]
#     else:
#         candidate_keys = list(bidder_fields)
#         candidate_texts = [
#             _candidate_text(candidate)
#             for candidate in candidate_keys
#         ]

#     if not candidate_keys:
#         return None, 0.0

#     texts = [rule_field] + candidate_texts

#     embeddings = model.encode(texts)

#     rule_embedding = embeddings[0]
#     field_embeddings = embeddings[1:]

#     scores = util.cos_sim(rule_embedding, field_embeddings)

#     best_index = int(scores.argmax().item())

#     best_field = candidate_keys[best_index]

#     similarity = scores[0][best_index].item()

#     return best_field, similarity

import json
from typing import Dict, Optional
import re
from models.bidder_schema import BidderField


class SemanticMatchService:

    def __init__(self, model_client):
        self.model = model_client

    def find_semantic_match(
        self,
        rule_field: str,
        bidder_fields: Dict[str, BidderField]
    ) -> Optional[BidderField]:

        evidence_snippets = []

        for field in bidder_fields.values():
            if field.original_text:
                evidence_snippets.append({
                    "field_name": field.field_name,
                    "text": field.source_section + "-" + field.original_text
                })

        prompt = self._build_prompt(rule_field, evidence_snippets)

        response = self.model.generate(prompt)

        result = self._parse_response(response)

        if result["matched"]:

            matched_field_name = result["matched_field"]

            if matched_field_name in bidder_fields:
                return bidder_fields[matched_field_name], result["confidence"]

        return 0, 1.0

    def _build_prompt(self, rule_field, evidence):

        evidence_text = "\n".join([
            f"{i+1}. {e['field_name']} : {e['text']}"
            for i, e in enumerate(evidence)
        ])

        return f"""
Rule field: {rule_field}
Below are extracted bidder evidence snippets.
Determine if any evidence corresponds to the rule field.
Evidence:
{evidence_text}
Return only JSON:
{{
"matched": true/false,
"matched_field": "field_name (from bidder evidence) that matches rule field)",
"confidence": float
}}
"""

    def _parse_response(self, response):
        try:
            cleaned = re.sub(r"```json|```", "", response).strip()
            print(cleaned)
            return json.loads(cleaned)
        except:
            return {"matched": False}