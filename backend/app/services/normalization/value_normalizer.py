def normalize_number(value):

    if isinstance(value, (int, float)):
        return value

    value = str(value).replace(",", "").strip()

    return float(value)

def normalize_boolean(value):

    value = str(value).lower().strip()

    if value in ["yes", "true", "available"]:
        return True

    if value in ["no", "false"]:
        return False

    return None

def normalize_value(field_type, value):

    if field_type == "number":
        return normalize_number(value)

    if field_type == "boolean":
        return normalize_boolean(value)

    return value