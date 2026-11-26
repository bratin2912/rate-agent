
from app.policy_extraction.schemas.normalized_policy import NormalizedPolicy


class PolicyAttributeResolver:
    """
    Converts normalized policy facts into canonical grid criteria.

    Product-specific configuration determines which attributes
    are required. No vehicle segment is guessed from make or model.
    """

    def resolve(
        self,
        policy: NormalizedPolicy,
        required_fields: tuple[str, ...],
        resolved_cluster: str | None = None,
        vehicle_segment: str | None = None,
    ) -> dict:
        vehicle = policy.vehicle

        available = {
            "geographic_cluster": resolved_cluster,
            "vehicle_segment": vehicle_segment,
            "vehicle_make": vehicle.make,
            "fuel_type": vehicle.fuel_type,
            "engine_cc": vehicle.engine_cc,
            "vehicle_age": vehicle.vehicle_age,
        }

        criteria = {}
        missing_fields = []

        for field_name in required_fields:
            value = available.get(field_name)

            if value is None or value == "unknown":
                missing_fields.append(field_name)
                continue

            criteria[field_name] = value

        return {
            "status": (
                "resolved" if not missing_fields
                else "insufficient_data"
            ),
            "criteria": criteria,
            "missing_fields": missing_fields,
            "available_attributes": {
                key: value
                for key, value in available.items()
                if value is not None
            },
        }
