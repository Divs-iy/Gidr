import pandas as pd

def export_to_excel(data, output_path="output.xlsx"):
    """
    data = {
        'invoice_number': str,
        'invoice_date': str,
        'due_date': str,
        'total': float,
        'items': list of dicts
    }
    """

    # -------- Invoice Summary --------
    summary_data = {
        "Field": ["Invoice Number", "Invoice Date", "Due Date", "Total"],
        "Value": [
            data.get("invoice_number"),
            data.get("invoice_date"),
            data.get("due_date"),
            data.get("total"),
        ],
    }

    df_summary = pd.DataFrame(summary_data)

    # -------- Line Items --------
    df_items = pd.DataFrame(data.get("items", []))

    # Ensure columns exist
    for col in ["description", "quantity", "unit_price", "amount"]:
        if col not in df_items.columns:
            df_items[col] = None

    df_items = df_items[["description", "quantity", "unit_price", "amount"]]

    # -------- Write to Excel --------
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Summary", index=False)
        df_items.to_excel(writer, sheet_name="Line Items", index=False)

    print(f"Excel exported to {output_path}")