from services.normalization.field_registry import FIELD_REGISTRY

def canonicalize_rule(raw_rule):

    normalized = (
        raw_rule
        .lower()
        .replace("_", " ")
        .replace("-", " ")
        .strip()
    )

    for canonical_name, metadata in FIELD_REGISTRY.items():

        aliases = metadata["aliases"]

        if normalized == canonical_name:
            return canonical_name

        if normalized in aliases:
            return canonical_name

    return raw_rule.lower().strip()

def canonicalize_field(raw_field):

    normalized = (
        raw_field
        .lower()
        .replace("_", " ")
        .replace("-", " ")
        .strip()
    )

    for canonical_name, metadata in FIELD_REGISTRY.items():

        aliases = metadata["aliases"]

        if normalized == canonical_name:
            return canonical_name

        if normalized in aliases:
            return canonical_name

    return None