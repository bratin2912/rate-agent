
import json
from pathlib import Path

from app.ingestion.rule_extractor import CommissionRuleExtractor


INPUT_PATH = Path("data/mapped/godigit_mar_2026.json")
OUTPUT_PATH = Path("data/rules/godigit_mar_2026.json")


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Mapped file not found: {INPUT_PATH.resolve()}"
        )

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        document = json.load(file)

    extractor = CommissionRuleExtractor()

    rules = extractor.extract(document)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "source": document["source"],
        "extraction": {
            "total_rules": len(rules),
            "rule_type": "commission_grid",
        },
        "rules": [
            rule.model_dump(mode="json")
            for rule in rules
        ],
    }

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("RULE EXTRACTION COMPLETED")
    print(f"Total rules: {len(rules)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
