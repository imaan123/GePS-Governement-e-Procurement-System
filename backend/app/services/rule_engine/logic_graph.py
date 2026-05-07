import networkx as nx

def build_rule_tree(node):
    """
    Converts PostgreSQL JSONB into executable tree.
    Leaf nodes are strings (rule_ids).
    """

    # Leaf node
    if isinstance(node, str):
        return node

    # Group node
    return {
        "operator": node["operator"],
        "rules": [
            build_rule_tree(child)
            for child in node["rules"]
        ]
    }

def tri_and(values):
    if "FAIL" in values:
        return "FAIL"
    if "NEEDS_REVIEW" in values:
        return "NEEDS_REVIEW"
    return "PASS"

def tri_or(values):
    if "PASS" in values:
        return "PASS"
    if "NEEDS_REVIEW" in values:
        return "NEEDS_REVIEW"
    return "FAIL"

def tri_not(value):
    if value == "PASS":
        return "PASS"
    if value == "FAIL":
        return "FAIL"
    return "NEEDS_REVIEW"

def evaluate_tree(node, rule_results):
    """
    node: rule tree (built from JSONB)
    rule_results: dict like { "R1": "PASS", "R2": "FAIL" }
    """
    print(node)
    # -------------------------
    # LEAF NODE
    # -------------------------
    if isinstance(node, str):
        return rule_results.get(node, "NEEDS_REVIEW")

    operator = node["operator"]
    children = node["rules"]

    values = [
        evaluate_tree(child, rule_results)
        for child in children
    ]

    # -------------------------
    # LOGIC DISPATCH
    # -------------------------
    if operator == "AND":
        return tri_and(values)

    elif operator == "OR":
        return tri_or(values)

    elif operator == "NOT":
        return tri_not(values[0])

    else:
        raise ValueError(f"Unknown operator: {operator}")
