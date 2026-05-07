# from .semantic_matcher import match_field
# from .evaluator import DeterministicEvaluator
# from .confidence_calc import compute_confidence
# from .logic_graph import build_rule_graph, execution_order


# class RuleEvaluator:

#     def __init__(self, rules, bidder_data):

#         self.rules = rules
#         self.bidder_data = bidder_data
#         self.bidder_records = self._normalize_bidder_data(bidder_data)

#         self.results = {}
#         self.outputs = []

#         self.disabled_rules = set()
#         self.evaluator = DeterministicEvaluator()


#     def _normalize_record(self, record):

#         if record is None:
#             return {}

#         if isinstance(record, dict):
#             return dict(record)

#         return {
#             "field_name": getattr(record, "field_name", None),
#             "value": getattr(record, "value", None),
#             "document": getattr(record, "document", None),
#             "page": getattr(record, "page", None),
#             "snippet": getattr(record, "snippet", None),
#             "confidence": getattr(record, "confidence", None),
#         }


#     def _normalize_bidder_data(self, bidder_data):

#         normalized = {}

#         if bidder_data is None:
#             return normalized

#         if isinstance(bidder_data, dict):
#             items = bidder_data.items()
#         else:
#             items = enumerate(bidder_data)

#         for key, record in items:
#             normalized_record = self._normalize_record(record)

#             normalized_key = key

#             if not isinstance(normalized_key, str):
#                 normalized_key = (
#                     normalized_record.get("field_name")
#                     or normalized_record.get("name")
#                     or f"field_{key}"
#                 )

#             normalized[normalized_key] = normalized_record

#         return normalized


#     def _record_value(self, record):

#         if not record:
#             return None

#         return record.get("value")


#     def _record_confidence(self, record):

#         if not record:
#             return 0.0

#         confidence = record.get("confidence")

#         if confidence is None:
#             return 0.0

#         return confidence


#     def _candidate_texts(self):

#         candidate_texts = {}

#         for field_name, record in self.bidder_records.items():
#             parts = [
#                 field_name,
#                 record.get("field_name"),
#                 record.get("document"),
#                 record.get("snippet"),
#                 record.get("value"),
#             ]

#             candidate_texts[field_name] = " ".join(
#                 str(part) for part in parts if part not in (None, "")
#             )

#         return candidate_texts


#     def check_condition(self, rule):

#         condition = rule.get("condition")

#         if not condition:
#             return True

#         field = condition["field"]
#         value = condition["value"]

#         bidder_value = self.bidder_records.get(field)

#         if not bidder_value:
#             return False

#         return self._record_value(bidder_value) == value


#     def find_value(self, rule):

#         rule_field = rule["rule_definition"]["field"]

#         bidder_fields = self._candidate_texts()

#         matched_field, similarity = match_field(rule_field, bidder_fields)

#         bidder_value = self.bidder_records.get(matched_field)

#         return bidder_value, matched_field, similarity


#     def evaluate_rule(self, rule):

#         rule_id = rule["rule_id"]

#         if rule_id in self.disabled_rules:
#             return

#         if not self.check_condition(rule):
#             return

#         definition = rule["rule_definition"]

#         bidder_value, matched_field, similarity = self.find_value(rule)
        
#         if not bidder_value:
#             result = "UNKNOWN"
#             confidence = 0.0

#         else:

#             operator = definition["operator"]
#             threshold = definition["value"]

#             evaluation = self.evaluator.evaluate(
#                 self._record_value(bidder_value),
#                 operator,
#                 threshold,
#             )

#             if evaluation == "PASS":
#                 result = "PASS"
#             elif evaluation == "FAIL":
#                 result = "FAIL"
#             else:
#                 result = "UNKNOWN"

#             confidence = (
#                 compute_confidence(
#                     self._record_confidence(bidder_value),
#                     similarity,
#                 )
#                 if result in {"PASS", "FAIL"}
#                 else 0.0
#             )

#         output = {

#             "rule_id": rule_id,
#             "criterion": definition["field"],
#             "extracted_value": self._record_value(bidder_value) if bidder_value else None,
#             "result": result,
#             "confidence": confidence,
#             "evidence": {
#                 "matched_field": matched_field if bidder_value else None
#             }
#         }

#         self.results[rule_id] = result == "PASS"

#         self.outputs.append(output)


#     def handle_override(self, rule):

#         if rule["category"] != "OVERRIDE":
#             return

#         target = rule.get("overrides")

#         if target:
#             self.disabled_rules.add(target)


#     def evaluate(self):

#         graph = build_rule_graph(self.rules)

#         order = execution_order(graph)

#         rule_map = {r["rule_id"]: r for r in self.rules}

#         for rid in order:

#             rule = rule_map[rid]

#             self.handle_override(rule)

#             self.evaluate_rule(rule)

#         return self.outputs

from .evaluator import DeterministicEvaluator
from services.normalization.canonical_mapper import canonicalize_rule
from llm.model_client import QwenClient
from services.rule_engine.semantic_matcher import SemanticMatchService
from services.rule_engine.confidence_calc import compute_confidence
from services.rule_engine.logic_graph import build_rule_tree, evaluate_tree

def evaluate_rule(rule, bidder_lookup, source_lookup):

    field = canonicalize_rule(rule.rule_definition["field"])
    operator = rule.rule_definition["operator"]
    threshold = rule.rule_definition["value"]

    bidder_value = bidder_lookup.get(field)

    result = DeterministicEvaluator.evaluate(
        bidder_value,
        operator,
        threshold
    )

    return {
        "rule_id": rule.rule_id,
        "field": field,
        "bidder_value": bidder_value,
        "expected_value": threshold,
        "result": result,
        "Bidder source document": source_lookup.get(field, {}).get("source_document"),
        "Bidder source page": source_lookup.get(field, {}).get("source_page"),
        "Bidder source section": source_lookup.get(field, {}).get("source_section"),
        "Bidder original text": source_lookup.get(field, {}).get("original_text"),
        "Bidder confidence": source_lookup.get(field, {}).get("confidence"),
    }

def evaluate_bidder(rules, bidder_lookup, bidder_fields, source_lookup):

    results = []
    rule_results = {}
    rule_logic ={}
    semantic_confidence = 1.0
    for rule in rules:

        result = evaluate_rule(rule, bidder_lookup, source_lookup)
        result["Rule type"] = rule.category
        print(f"Deterministic Evaluated Rule {rule.rule_id}: {result['result']}")

        if result["result"] == "NEEDS_REVIEW":
            mapped_field = {bidder_field.field_name: bidder_field for bidder_field in bidder_fields}
            model = QwenClient(mode="private")
            matching_service = SemanticMatchService(model)
            match_field, semantic_confidence = matching_service.find_semantic_match(rule.rule_definition["field"], mapped_field)
            if match_field:
                result["result"] = "PASS"
                print(f"Semantic Match found for Rule {rule.rule_id}, in {match_field} overriding to PASS")
            else:
                print(f"No Semantic Match found for Rule {rule.rule_id}, still needs review.")
        
        rule_results[rule.rule_id] = result["result"]
        if rule.category.lower() == "mandatory" and result["result"] == "FAIL":
            rule_logic[rule.rule_id] = rule.dependencies
        result["Original rule"] = rule.original_text
        if result['Bidder confidence'] is not None:
            result["Confidence"] = compute_confidence(min(rule.confidence, result["Bidder confidence"]), semantic_confidence)
        else:
            result["Confidence"] = compute_confidence(rule.confidence, semantic_confidence)
        results.append(result)
    # compute eligibility for mandatory rules

    mandatory_results = [r for r in results if str(r.get("Rule type", "")).upper() == "MANDATORY"]

    final_verdict = "ELIGIBLE"

    if any(r.get("result") == "FAIL" for r in mandatory_results):
        final_verdict = "NOT_ELIGIBLE"
    elif any(r.get("result") in {"NEEDS_REVIEW", "UNKNOWN"} for r in mandatory_results):
        final_verdict = "NEEDS_REVIEW"
    else:
        final_verdict = "ELIGIBLE"

    print(f"Eligibility verdict based on mandatory rules: {final_verdict}")

    # Modify verdict based on rule graph for failed rules only
    for rule_id, dependencies in rule_logic.items():
        if not dependencies:
            continue
        rule_tree = build_rule_tree(dependencies)
        print(f"Processing dependencies for rule: {rule_id}")
        rule_result = evaluate_tree(rule_tree, rule_results)
        if rule_result == "PASS":
            print(f"Rule {rule_id} originally failed but passed based on dependencies, updating result to PASS.")
            # Update results list more reliably
            updated = False
            for i, r in enumerate(results):
                if isinstance(r, dict) and r.get("rule_id") == rule_id:
                    print(f"Before update: {r}")
                    results[i]["result"] = "PASS"
                    print(f"After update: {results[i]}")
                    updated = True
                    break
            if not updated:
                print(f"WARNING: Could not find rule {rule_id} in results to update")

    # Re-check eligibility after dependency overrides if verdict was NOT_ELIGIBLE
    print(results)
    if final_verdict == "NOT_ELIGIBLE":
        mandatory_results_updated = [r for r in results if str(r.get("Rule type", "")).upper() == "MANDATORY"]
        
        if any(r.get("result") == "FAIL" for r in mandatory_results_updated):
            final_verdict = "NOT_ELIGIBLE"
        elif any(r.get("result") in {"NEEDS_REVIEW", "UNKNOWN"} for r in mandatory_results_updated):
            final_verdict = "NEEDS_REVIEW"
        else:
            final_verdict = "ELIGIBLE"
        
        print(f"Re-checked eligibility after dependency overrides: {final_verdict}")

    # Append summary with final verdict
    summary = {
        "summary": {
            "verdict": final_verdict,
            "mandatory_count": len(mandatory_results)
        }
    }
    results.append(summary)

    return results