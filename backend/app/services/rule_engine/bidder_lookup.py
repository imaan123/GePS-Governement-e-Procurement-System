from services.normalization.canonical_mapper import canonicalize_field
from services.normalization.value_normalizer import normalize_value
from services.normalization.field_registry import FIELD_REGISTRY


def build_bidder_lookup(bidder_fields):

    lookup = {}
    source_lookup = {}

    for row in bidder_fields:

        raw_field = row.field_name
        raw_type = row.field_type
        raw_value = row.value

        canonical_field = canonicalize_field(raw_field)

        if not canonical_field:
            canonical_field = raw_field.lower().strip()
            normalized_value = normalize_value(raw_type, raw_value)
            lookup[canonical_field] = normalized_value
            continue

        field_type = FIELD_REGISTRY[canonical_field]["type"]

        normalized_value = normalize_value(
            field_type,
            raw_value
        )

        lookup[canonical_field] = normalized_value
        source_lookup[canonical_field] = {
            "original_text": row.original_text,
            "source_document": row.source_document,
            "source_page": row.source_page,
            "source_section": row.source_section,
            "confidence": row.confidence
        }

    return lookup, source_lookup