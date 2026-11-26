
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
    
    "4W  RTO": {
        "RTO Code": "rto_code",
        "4WTP": "four_wheeler_tp_cluster",
        "4W Package": "four_wheeler_package_cluster",
        "4WSAOD": "four_wheeler_saod_cluster",
        "PLR Cluster": "plr_cluster",
    },
    "2W RTO's": {
        "RTO_Code": "rto_code",
        "2W_1+1 & SATP | Clusters": "two_wheeler_1plus1_satp_cluster",
        "2W 1+5 & 5+5 | Clusters": "two_wheeler_1plus5_5plus5_cluster",
        "2W_SAOD | Clusters": "two_wheeler_saod_cluster",
    },
    
    "4W SATP": {
        "Cluster": "geographic_cluster",
        "Segment": "vehicle_segment",
        "Age": "vehicle_age_eligibility",
        "Note": "underwriting_note",
    },
    
    "4W  RTO": {
        "RTO Code": "rto_code",
        "4WTP": "four_wheeler_tp_cluster",
        "4W Package": "four_wheeler_package_cluster",
        "4WSAOD": "four_wheeler_saod_cluster",
        "PLR Cluster": "plr_cluster",
    },


}
