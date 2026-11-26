
from app.policy_extraction.schemas.normalized_policy import NormalizedPolicy


class ProductResolver:
    """
    Identifies candidate insurer grid worksheets.

    These mappings are candidates only. Final product selection
    requires additional matching against policy tenure and
    insurer-specific eligibility conditions.
    """

    CANDIDATE_SHEETS = {
        ("private_car", "comprehensive"): [],
        ("private_car", "standalone_od"): [],
        ("private_car", "standalone_tp"): [
            "4W SATP",
        ],
        ("two_wheeler", "comprehensive"): [
            "TW 1+1 & SATP",
            "TW 1+5",
            "2W Grid 5+5",
        ],
        ("two_wheeler", "standalone_od"): [
            "TW SAOD with Flexi Options",
        ],
        ("two_wheeler", "standalone_tp"): [
            "TW 1+1 & SATP",
        ],
        ("commercial_vehicle", "comprehensive"): [
            "CV Grid (excl. HCV)",
            "HCV GRID",
            "TAXI Segments and Location wise",
            "School & Staff Bus ",
        ],
    }

    def resolve(self, policy: NormalizedPolicy) -> dict:
        vehicle_category = policy.vehicle.vehicle_category
        policy_type = policy.policy_type

        if (
            vehicle_category == "unknown"
            or policy_type == "unknown"
        ):
            return {
                "status": "insufficient_data",
                "candidate_sheets": [],
                "reason": (
                    "Vehicle category or policy type is missing."
                ),
            }

        key = (vehicle_category, policy_type)

        candidates = self.CANDIDATE_SHEETS.get(key)

        if candidates is None:
            return {
                "status": "no_mapping",
                "candidate_sheets": [],
                "reason": (
                    "No product mapping configured for "
                    f"{vehicle_category} and {policy_type}."
                ),
            }

        if not candidates:
            return {
                "status": "no_mapping",
                "candidate_sheets": [],
                "reason": (
                    "No verified worksheet mapping is configured "
                    "for this product."
                ),
            }

        return {
            "status": "candidates_identified",
            "vehicle_category": vehicle_category,
            "policy_type": policy_type,
            "candidate_sheets": candidates,
            "requires_further_matching": True,
        }
