
from app.ingestion.matching_engine import RuleMatchingEngine
from app.ingestion.rule_precedence import RulePrecedenceEngine


class RatingRulePipeline:

    def __init__(self):
        self.matcher = RuleMatchingEngine()
        self.precedence = RulePrecedenceEngine()

    def evaluate(
        self,
        rules: list[dict],
        policy: dict,
    ) -> dict:

        matching_result = self.matcher.match(
            rules=rules,
            policy=policy,
        )

        selection_result = self.precedence.select(
            matching_result
        )

        return {
            "matching": matching_result,
            "selection": selection_result,
        }
