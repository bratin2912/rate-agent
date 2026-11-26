
import json
from pathlib import Path

from app.ingestion.matching_engine import RuleMatchingEngine


RULES_PATH = Path("data/rules/godigit_mar_2026.json")


def main():
    with RULES_PATH.open("r", encoding="utf-8") as file:
        document = json.load(file)

    rules = document["rules"]

    policy = {
        "product_line": "commercial_vehicle",
        "geographic_cluster": "UP Cluster 1",
        "vehicle_segment": "GCV4 upto 1.6T 6+ years",
        "vehicle_make": "TATA",
    }

    engine = RuleMatchingEngine()

    result = engine.match(
        rules=rules,
        policy=policy,
    )

    print("=" * 60)
    print("GODIGIT RULE MATCHING")
    print("=" * 60)

    print("\nPOLICY:")
    print(json.dumps(policy, indent=2))

    print("\nSUMMARY:")
    print(json.dumps(result["summary"], indent=2))

    print("\nMATCHED RULES:")

    for match in result["matched_rules"][:10]:
        print(
            f'{match["rule_id"]} | '
            f'Sheet: {match["source_sheet"]} | '
            f'Row: {match["source_row"]}'
        )

    print("\nINCOMPLETE RULES:")
    for rule in result["incomplete_rules"][:5]:
        print(rule)


if __name__ == "__main__":
    main()
