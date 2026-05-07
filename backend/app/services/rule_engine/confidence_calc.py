def compute_confidence(
    extraction_conf,
    semantic_score,
    extraction_weight=0.65,
    semantic_weight=0.35,
):

    extraction_conf = max(0.0, min(1.0, extraction_conf or 0.0))
    semantic_score = max(0.0, min(1.0, semantic_score or 0.0))

    weight_total = extraction_weight + semantic_weight

    if weight_total <= 0:
        return 0.0

    base_confidence = (
        extraction_weight * extraction_conf +
        semantic_weight * semantic_score
    ) / weight_total

    agreement = 1.0 - abs(extraction_conf - semantic_score)
    confidence = base_confidence * (0.75 + 0.25 * agreement)

    return round(max(0.0, min(1.0, confidence)), 3)