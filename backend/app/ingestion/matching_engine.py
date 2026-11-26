
from typing import Any


class RuleMatchingEngine:
    """
    Finds rules matching supplied policy details.

    Does not calculate or interpret commission values.
    """

    WILDCARD_VALUES = {"all"}

    def _normalize(self, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().casefold()
        return value

    def _evaluate_condition(
        self,
        condition: dict,
        policy: dict,
    ) -> tuple[str, str]:

        field = condition["field"]
        operator = condition.get("operator", "equals")
        rule_value = condition.get("value")

        if field not in policy or policy[field] is None:
            return "missing", f"Missing policy field: {field}"

        policy_value = policy[field]

        if (
            isinstance(rule_value, str)
            and rule_value.strip().casefold()
            in self.WILDCARD_VALUES
        ):
            return "match", f"{field}: wildcard match"

        if operator == "equals":
            matched = (
                self._normalize(policy_value)
                == self._normalize(rule_value)
            )

            if matched:
                return "match", f"{field}: exact match"

            return "mismatch", (
                f"{field}: policy value {policy_value!r} "
                f"does not match rule value {rule_value!r}"
            )

        return "unsupported", f"Unsupported operator: {operator}"

    def match_with_rto_resolution(
        self,
        rules: list[dict],
        policy: dict,
        rto_resolver,
    ) -> dict:
    
        resolved = rto_resolver.resolve(
            rto_code=policy["rto_code"],
            vehicle_category=policy["vehicle_category"],
        )
    
        if resolved["status"] != "resolved":
            return {
                "status": "unable_to_resolve_rto",
                "rto_resolution": resolved,
                "matching_result": None,
            }
    
        enriched_policy = {
            **policy,
            "geographic_cluster": resolved["cluster"],
        }
    
        matching_result = self.match(
            rules=rules,
            policy=enriched_policy,
        )
    
        return {
            "status": "completed",
            "rto_resolution": resolved,
            "matching_result": matching_result,
        }


    def match(
        self,
        rules: list[dict],
        policy: dict,
    ) -> dict:

        matched_rules = []
        unmatched_rules = []
        incomplete_rules = []
        unmatchable_rules = []
        excluded_rules = []

        requested_product_line = policy.get("product_line")

        for rule in rules:

            # Filter rules belonging to other product lines.
            if (
                requested_product_line
                and rule.get("product_line") != requested_product_line
            ):
                excluded_rules.append(rule["rule_id"])
                continue

            conditions = rule.get("conditions", [])

            if not conditions:
                unmatchable_rules.append({
                    "rule_id": rule["rule_id"],
                    "reason": "No matching conditions extracted",
                })
                continue

            statuses = []
            explanations = []

            for condition in conditions:
                status, explanation = self._evaluate_condition(
                    condition,
                    policy,
                )

                statuses.append(status)
                explanations.append(explanation)

            if "mismatch" in statuses:
                unmatched_rules.append({
                    "rule_id": rule["rule_id"],
                    "reasons": explanations,
                })

            elif any(
                status in {"missing", "unsupported"}
                for status in statuses
            ):
                incomplete_rules.append({
                    "rule_id": rule["rule_id"],
                    "reasons": explanations,
                })

            else:
                matched_rules.append({
                    "rule_id": rule["rule_id"],
                    "source_sheet": rule["source_sheet"],
                    "source_row": rule["source_row"],
                    "conditions_matched": explanations,
                    "rule": rule,
                })

        return {
            "policy": policy,
            "summary": {
                "total_rules_checked": len(rules),
                "eligible_rules": (
                    len(rules) - len(excluded_rules)
                ),
                "excluded_rules": len(excluded_rules),
                "matched_count": len(matched_rules),
                "unmatched_count": len(unmatched_rules),
                "incomplete_count": len(incomplete_rules),
                "unmatchable_count": len(unmatchable_rules),
            },
            "matched_rules": matched_rules,
            "incomplete_rules": incomplete_rules,
            "unmatched_rules": unmatched_rules,
            "unmatchable_rules": unmatchable_rules,
        }
        
        
