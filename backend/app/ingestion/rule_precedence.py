
from typing import Any


class RulePrecedenceEngine:
    """
    Ranks matching rules based on condition specificity.

    More specific conditions receive a higher score.

    If multiple rules have the same highest score, the result
    is ambiguous. We never select an arbitrary rule.
    """

    WILDCARD_VALUES = {"all", "*"}

    def _is_specific(self, value: Any) -> bool:
        if value is None:
            return False

        if isinstance(value, str):
            return value.strip().casefold() not in self.WILDCARD_VALUES

        return True

    def _calculate_specificity(self, rule: dict) -> int:
        conditions = rule.get("conditions", [])

        return sum(
            1
            for condition in conditions
            if self._is_specific(condition.get("value"))
        )

    def select(self, matching_result: dict) -> dict:

        candidates = matching_result.get("matched_rules", [])

        if not candidates:
            return {
                "status": "no_match",
                "selected_rule": None,
                "candidates": [],
                "reason": "No matching commission rules found",
            }

        ranked_candidates = []

        for candidate in candidates:
            rule = candidate["rule"]

            specificity = self._calculate_specificity(rule)

            ranked_candidates.append({
                "rule_id": candidate["rule_id"],
                "source_sheet": candidate["source_sheet"],
                "source_row": candidate["source_row"],
                "specificity": specificity,
                "rule": rule,
            })

        ranked_candidates.sort(
            key=lambda item: item["specificity"],
            reverse=True,
        )

        highest_score = ranked_candidates[0]["specificity"]

        best_candidates = [
            candidate
            for candidate in ranked_candidates
            if candidate["specificity"] == highest_score
        ]

        if len(best_candidates) > 1:
            return {
                "status": "ambiguous",
                "selected_rule": None,
                "candidates": best_candidates,
                "reason": (
                    "Multiple matching rules have equal specificity. "
                    "Source-specific precedence is not established."
                ),
            }

        return {
            "status": "selected",
            "selected_rule": best_candidates[0],
            "candidates": ranked_candidates,
            "reason": "Selected the most specific matching rule",
        }
