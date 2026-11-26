
import json
from pathlib import Path
from collections import Counter


RULES_PATH = Path("data/rules/godigit_mar_2026.json")


def main():
    if not RULES_PATH.exists():
        raise FileNotFoundError(
            f"Rules file not found: {RULES_PATH.resolve()}"
        )

    with RULES_PATH.open("r", encoding="utf-8") as file:
        document = json.load(file)

    rules = document.get("rules", [])

    if not rules:
        raise ValueError("No rules found in the output file")

    rule_ids = [rule["rule_id"] for rule in rules]
    duplicate_ids = [
        rule_id
        for rule_id, count in Counter(rule_ids).items()
        if count > 1
    ]

    missing_source = []
    missing_evidence = []
    empty_rules = []
    unresolved_values = 0

    for rule in rules:
        if not all([
            rule.get("source_id"),
            rule.get("source_sheet"),
            rule.get("source_row"),
        ]):
            missing_source.append(rule["rule_id"])

        if not rule.get("source_evidence"):
            missing_evidence.append(rule["rule_id"])

        if not rule.get("conditions") and not rule.get("rule_values"):
            empty_rules.append(rule["rule_id"])

        for value in rule.get("rule_values", []):
            if value.get("interpretation_status") == "unresolved":
                unresolved_values += 1

    print("=" * 60)
    print("GODIGIT RULE VALIDATION")
    print("=" * 60)

    print(f"Total rules: {len(rules)}")
    print(f"Unique rule IDs: {len(set(rule_ids))}")
    print(f"Duplicate rule IDs: {len(duplicate_ids)}")
    print(f"Rules missing source: {len(missing_source)}")
    print(f"Rules missing evidence: {len(missing_evidence)}")
    print(f"Empty rules: {len(empty_rules)}")
    print(f"Unresolved source values: {unresolved_values}")

    if duplicate_ids:
        print("\nDuplicate IDs:", duplicate_ids[:10])

    if missing_source:
        print("\nMissing source:", missing_source[:10])

    if missing_evidence:
        print("\nMissing evidence:", missing_evidence[:10])

    if empty_rules:
        print("\nEmpty rules:", empty_rules[:10])

    if any([
        duplicate_ids,
        missing_source,
        missing_evidence,
        empty_rules,
    ]):
        raise ValueError("Rule validation failed")

    print("\nVALIDATION PASSED")


if __name__ == "__main__":
    main()
