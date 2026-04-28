import pandas as pd
from typing import Dict

def export_to_excel(data: Dict, output_path: str = "output.xlsx"):
    """
    Export invoice data into structured Excel with multiple sheets
    """

    # --- Sheet 1: Summary ---
    summary_data = {
        "invoice_number": data.get("invoice_number"),
        "invoice_date": data.get("invoice_date"),
        "due_date": data.get("due_date"),
        "total": data.get("total")
    }

    df_summary = pd.DataFrame([summary_data])

    # --- Sheet 2: Line Items ---
    items = data.get("items", [])

    if items:
        df_items = pd.DataFrame(items)
    else:
        df_items = pd.DataFrame(columns=["description", "quantity", "unit_price", "amount"])

    # --- Write to Excel ---
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Summary", index=False)
        df_items.to_excel(writer, sheet_name="Line Items", index=False)

    print(f"Excel file saved at: {output_path}")