
from app.ingestion.core.profile_models import SheetProfile


SHEET_PROFILES = {
    "CV Grid (excl. HCV)": SheetProfile(
        sheet_name="CV Grid (excl. HCV)",
        table_type="commission_grid",
        header_rows=(2, 3),
        data_start_row=4,
        product_line="commercial_vehicle",
        description="Commercial vehicle grid excluding HCV",
    ),

    "HCV GRID": SheetProfile(
        sheet_name="HCV GRID",
        table_type="commission_grid",
        header_rows=(1, 2, 3),
        data_start_row=4,
        product_line="heavy_commercial_vehicle",
        description="Heavy commercial vehicle commission grid",
    ),

    "TAXI Segments and Location wise": SheetProfile(
        sheet_name="TAXI Segments and Location wise",
        table_type="commission_grid",
        header_rows=(2, 3),
        data_start_row=4,
        product_line="taxi",
        description="Taxi commission grid by segment and location",
    ),

    "4W SATP": SheetProfile(
        sheet_name="4W SATP",
        table_type="commission_grid",
        header_rows=(2,),
        data_start_row=3,
        product_line="four_wheeler_satp",
        description="Four-wheeler standalone third-party grid",
    ),

    "4W New Business 1+3": SheetProfile(
        sheet_name="4W New Business 1+3",
        table_type="commission_grid",
        header_rows=(2, 3),
        data_start_row=4,
        product_line="four_wheeler_new_business",
        description="Four-wheeler new business 1+3 grid",
    ),

    "TW 1+1 & SATP": SheetProfile(
        sheet_name="TW 1+1 & SATP",
        table_type="commission_grid",
        header_rows=(3, 4),
        data_start_row=5,
        product_line="two_wheeler_1+1_satp",
        description="Two-wheeler 1+1 and SATP grid",
    ),

    "TW 1+5": SheetProfile(
        sheet_name="TW 1+5",
        table_type="commission_grid",
        header_rows=(1, 2),
        data_start_row=3,
        product_line="two_wheeler_1+5",
        description="Two-wheeler 1+5 grid",
    ),

    "2W Grid 5+5": SheetProfile(
        sheet_name="2W Grid 5+5",
        table_type="commission_grid",
        header_rows=(2,),
        data_start_row=3,
        product_line="two_wheeler_5+5",
        description="Two-wheeler 5+5 grid",
    ),

    "TW SAOD with Flexi Options": SheetProfile(
        sheet_name="TW SAOD with Flexi Options",
        table_type="commission_grid",
        header_rows=(5,),
        data_start_row=6,
        product_line="two_wheeler_saod",
        description="Two-wheeler standalone own-damage grid",
    ),

    "School & Staff Bus ": SheetProfile(
        sheet_name="School & Staff Bus ",
        table_type="commission_grid",
        header_rows=(3, 4, 5),
        data_start_row=6,
        product_line="school_staff_bus",
        description="School and staff bus commission grid",
    ),

    "School & Staff Bus RTO": SheetProfile(
        sheet_name="School & Staff Bus RTO",
        table_type="rto_mapping",
        header_rows=(1, 2),
        data_start_row=3,
        product_line="school_staff_bus",
        description="School and staff bus RTO mapping",
    ),

    "CV RTO Mapping": SheetProfile(
        sheet_name="CV RTO Mapping",
        table_type="rto_mapping",
        header_rows=(1, 2),
        data_start_row=3,
        product_line="commercial_vehicle",
        description="Commercial vehicle RTO and cluster mapping",
    ),

    "2W RTO's": SheetProfile(
        sheet_name="2W RTO's",
        table_type="rto_mapping",
        header_rows=(1, 2),
        data_start_row=3,
        product_line="two_wheeler",
        description="Two-wheeler RTO and cluster mapping",
    ),
    "4W  RTO": SheetProfile(
        sheet_name="4W  RTO",
        table_type="rto_mapping",
        header_rows=(2,),
        data_start_row=3,
        product_line="four_wheeler",
        description="Four-wheeler RTO and cluster mapping",
    ),
}
