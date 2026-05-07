class DeterministicEvaluator:

    @staticmethod
    def evaluate(value, operator, threshold):

        if value is None:
            return "NEEDS_REVIEW"

        if operator == ">=":
            return "PASS" if value >= threshold else "FAIL"

        if operator == "<=":
            return "PASS" if value <= threshold else "FAIL"

        if operator == ">":
            return "PASS" if value > threshold else "FAIL"

        if operator == "<":
            return "PASS" if value < threshold else "FAIL"

        if operator == "=" or operator == "==":
            return "PASS" if value == threshold else "FAIL"

        if operator == "!=":
            return "PASS" if value != threshold else "FAIL"

        return "NEEDS_REVIEW"