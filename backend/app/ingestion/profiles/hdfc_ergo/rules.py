HDFC_ERGO_RULES = {
    "slab_calculation": {
        "included_components": [
            "comprehensive_gwp",
            "saod_gwp",
        ],
        "excluded_components": [
            "satp_premium",
        ],
    },
    "fuel_mapping": {
        "non_petrol": [
            "diesel",
            "cng",
            "lpg",
        ],
        "petrol_grid": [
            "petrol",
            "electric",
            "hybrid",
        ],
    },
    "business_type_mapping": {
        "new_business_uses_ncb": True,
    },
}
