
"""
Go Digit field mappings.

Mappings are intentionally sheet-specific.
Unverified source fields remain unmapped.
"""

GODIGIT_FIELD_MAPPINGS = {
    "4W SATP": {
        "Cluster": "geographic_cluster",
        "Segment": "vehicle_segment",
        "Age": "vehicle_age_eligibility",
        "Note": "underwriting_note",
    },

    "CV Grid (excl. HCV)": {
        "Cluster": "geographic_cluster",
        "Segment": "vehicle_segment",
        "Make": "vehicle_make",
        "Note": "underwriting_note",
    },

    "HCV GRID": {
        "Refer Addition Notes mentioned below the grid | Cluster":
            "geographic_cluster",
        "Refer Addition Notes mentioned below the grid | Segment":
            "vehicle_segment",
        "Make": "vehicle_make",
        "Age From": "vehicle_age_min",
        "Age To": "vehicle_age_max",
    },

    "TAXI Segments and Location wise": {
        "Cluster": "geographic_cluster",
        "Segment": "vehicle_segment",
        "Make": "vehicle_make",
        "Addon/without Addon": "addon_condition",
    },

    "CV RTO Mapping": {
        "RTO Code": "rto_code",
        "State": "state",
        "City": "city",
    },

    "2W RTO's": {
        "RTO_Code": "rto_code",
    },

    "4W  RTO": {
        "RTO Code": "rto_code",
    },
}
