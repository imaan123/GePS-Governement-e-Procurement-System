# Rule Evaluation Engine

## Overview

The Rule Evaluation Engine evaluates bidder-supplied fields against a set of rules stored in the database and produces per-rule evaluation results and a bidder-level verdict (ELIGIBLE / NOT_ELIGIBLE / NEEDS_REVIEW).

It follows a 3-stage evaluation pipeline:

1. Deterministic evaluation using explicit operators (>=, <=, ==, >, <).
2. Semantic fallback: when deterministic returns `NEEDS_REVIEW`, a semantic matching step attempts to find a matching bidder field using an embedding/LLM matcher.
3. Dependency resolution: failed mandatory rules may be re-evaluated using dependency trees (AND/OR style logic) to allow some failures to be overridden.

## Key components

- `evaluate_rule(rule, bidder_lookup, source_lookup)` — single-rule deterministic evaluation and packaging of result metadata.
- `DeterministicEvaluator` (`services/rule_engine/evaluator.py`) — performs typed comparisons; contains helpers to coerce strings to numbers.
- `SemanticMatchService` (`services/rule_engine/semantic_matcher.py`) — finds semantic matches using the LLM client (`llm/model_client.py`).
- `compute_confidence` (`services/rule_engine/confidence_calc.py`) — combines extraction and semantic confidences with a disagreement penalty.
- `build_rule_tree` / `evaluate_tree` (`services/rule_engine/logic_graph.py`) — builds dependency graph and evaluates it to determine if failed rules can be resolved.
- `evaluate_bidder(rules, bidder_lookup, bidder_fields, source_lookup)` — orchestrates evaluation across all rules and returns a list of per-rule results plus a `summary` entry.

## Data models and shapes

- `Rule` (DB model / `models/rule_schema.py`):
  - `rule_id` (str)
  - `rule_type` / `category` (e.g., "MANDATORY", "OPTIONAL", "OVERRIDE")
  - `rule_definition` (dict): expected shape depends on the rule engine; common keys: `field`, `operator`, `value`
  - `dependencies` (optional): rule dependency spec (could be list or nested JSON for AND/OR graphs)
  - `confidence` (float)

- `BidderField` (DB model / `models/bidder_schema.py`):
  - `field_name`, `field_type`, `value`, `source_document`, `source_page`, `source_section`, `original_text`, `confidence`

- Evaluation result (returned by `evaluate_bidder`) — each item is a dict containing keys such as:
  - `rule_id`, `field`, `bidder_value`, `expected_value`, `result` (PASS/FAIL/NEEDS_REVIEW/UNKNOWN), `Confidence`, `Bidder source document`, `Bidder source page`, `Bidder original text`, `Rule type`, `Original rule`.
  - Final element in the returned list is a `summary` dict: `{"summary": {"verdict": <str>, "mandatory_count": <int>}}`.

## Evaluation flow (detailed)

1. For each `rule`:
   - Canonicalize the rule field (`canonicalize_rule`) to match normalized bidder lookup keys.
   - Call `DeterministicEvaluator.evaluate(bidder_value, operator, threshold)`.
   - If deterministic result is `NEEDS_REVIEW`, attempt semantic match via `SemanticMatchService`. If a match is found, upgrade to `PASS` and compute combined confidence.
   - Compute `Confidence` using `compute_confidence(rule.confidence, extraction_confidence, semantic_confidence)` (implementation details in `confidence_calc.py`).
   - Append the result entry to the `results` list and record `rule_results[rule_id] = result`.
   - For mandatory rules that initially `FAIL`, add an entry to `rule_logic` mapping `rule_id` to its dependencies for later evaluation.

2. After initial pass, compute bidder-level verdict from mandatory rules:
   - If any mandatory rule has `result == 'FAIL'` → `NOT_ELIGIBLE`.
   - Else if any mandatory rule is `NEEDS_REVIEW` or `UNKNOWN` → `NEEDS_REVIEW`.
   - Else → `ELIGIBLE`.

3. Dependency resolution pass (only for failed mandatory rules that have dependencies):
   - For each failed rule with dependencies, build the dependency tree with `build_rule_tree()`.
   - Evaluate the tree using `evaluate_tree(rule_tree, rule_results)` — this uses the current `rule_results` map of rule_id -> result.
   - If the tree evaluation returns `PASS`, update the corresponding entry in the `results` list to `PASS` (the engine updates `results` in-place and logs before/after values).

4. Recompute bidder verdict if dependency overrides changed any mandatory `FAIL` to `PASS`.

5. Append a `summary` dict to `results` and return the list.

## Confidence calculation (summary)

- `compute_confidence` combines extraction confidence (how confident we are in the extracted bidder field) and semantic confidence (how strong the semantic match is), and penalizes disagreement:

  - base_confidence = 0.65 * extraction_conf + 0.35 * semantic_score
  - agreement = 1.0 - abs(extraction_conf - semantic_score)
  - confidence = base_confidence * (0.75 + 0.25 * agreement)
  - Final value clamped to [0.0, 1.0].

Refer to `services/rule_engine/confidence_calc.py` for the exact implementation.

## Example input and output

Input: list of `Rule` objects fetched via `db.fetch_rules()` and bidder fields via `db.fetch_bidder_fields(bidder_id)`.

Example output snippet (per-rule):

```
{
  "rule_id": "TECH-002",
  "field": "years_experience",
  "bidder_value": 7,
  "expected_value": 10,
  "result": "FAIL",
  "Confidence": 0.55,
  "Bidder source document": null
}
```

Final `summary` appended to `results`:

```
{"summary": {"verdict": "NOT_ELIGIBLE", "mandatory_count": 6}}
```

## How to run / test locally

1. Ensure database is running and `DATABASE_URL` (or DB config) in `database/db.py` points to a reachable Postgres instance.
2. Start the FastAPI server from the `backend/app` directory:

```bash
python -m uvicorn main:app --reload
```

3. Use `/evaluate/{bidder_id}` POST endpoint or call `evaluate_bidder(rules, bidder_lookup, bidder_fields, source_lookup)` directly from Python for unit-testing.

4. Use the `db.store_evaluation_results(bidder_id, results)` function (implemented in `database/db.py`) to persist results.

## Troubleshooting

- If rules are not matching fields, ensure `canonicalize_rule` produces keys that match the keys in `bidder_lookup`.
- If semantic fallback is always returning no-match, check LLM client credentials and whether `llm/model_client.py` is importable from the runtime path.
- If dependency overrides are not updating `results`, confirm the `rule_logic` map contains the expected dependency definitions and that `evaluate_tree()` returns `PASS`. The engine now updates `results` by index and logs before/after values.

## Extending the engine

- Add new deterministic operators in `services/rule_engine/evaluator.py`.
- Improve semantic matching by adding more context or switching to a larger embedding model in `llm/model_client.py`.
- Define a strict schema for `Rule.dependencies` (recommended: a small recursive JSON structure with `{"AND": [...]} / {"OR": [...]} / "rule_id"`) and update `logic_graph.py` to parse it deterministically.

---

File: `backend/app/services/rule_engine/rule_engine_core.py`
