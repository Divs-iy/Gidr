import streamlit as st
from pipeline.ocr import OCRProcessor
from pipeline.layout import LayoutParser
from pipeline.extractor import Extractor
from utils.excel_exporter import export_to_excel
import tempfile
import os
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Gidr | Intelligent Document Processing",
    page_icon="📄",
    layout="wide"
)

# ---------------- CACHE HEAVY PROCESSORS ----------------
@st.cache_resource
def load_processors():
    ocr = OCRProcessor()
    layout = LayoutParser()
    extractor = Extractor()
    return ocr, layout, extractor

# ---------------- SIDEBAR ----------------
st.sidebar.title("📄 Gidr Platform")
st.sidebar.markdown("### Intelligent Document Processing Suite")

module = st.sidebar.radio(
    "Navigation",
    [
        "Invoice Extraction",
        "Workflow Overview",
        "Roadmap"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Baseline Ready: OCR + Rule-Based Extraction + Excel Export\n\n"
    "In Progress: ML validation + LLM reasoning + Advanced analytics"
)

# ---------------- WORKFLOW PAGE ----------------
if module == "Workflow Overview":
    st.title("⚙️ Gidr Processing Workflow")

    st.markdown("""
    ### Current Product Pipeline
    **Invoice/Bill Image → OCR → Layout Parsing → Field Extraction → Confidence Scoring → Excel Export**
    """)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Step 1", "Upload")
    col2.metric("Step 2", "OCR")
    col3.metric("Step 3", "Extract")
    col4.metric("Step 4", "Validate")
    col5.metric("Step 5", "Excel")

    st.success("Baseline system is fully functional and client-demo ready.")

# ---------------- ROADMAP PAGE ----------------
elif module == "Roadmap":
    st.title("🚀 Gidr Product Roadmap")

    st.subheader("Current Version (V1)")
    st.write("- OCR Pipeline")
    st.write("- Layout Parsing")
    st.write("- Rule-Based Field Extraction")
    st.write("- Confidence Scoring")
    st.write("- Excel Export")

    st.subheader("Next Version (V2)")
    st.write("- ML-based invoice understanding")
    st.write("- LLM-assisted field inference")
    st.write("- Fraud detection")
    st.write("- Batch processing")
    st.write("- Analytics dashboard")

    st.warning("Client Note: Core infrastructure is complete. AI intelligence and product expansion are actively under development.")

# ---------------- MAIN INVOICE EXTRACTION ----------------
else:
    st.title("📄 Gidr: Intelligent Invoice Extraction System")
    st.caption("Convert bills and invoices into structured Excel data in seconds")

    uploaded_file = st.file_uploader(
        "Upload Invoice / Bill Image",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_path = tmp_file.name

        # Image Preview
        st.subheader("Uploaded Document")
        st.image(temp_path, use_container_width=True)

        # Load processors
        ocr, layout, extractor = load_processors()

        # Processing spinner
        with st.spinner("Processing invoice through Gidr pipeline..."):
            result = ocr.run_ocr(temp_path)
            lines = layout.group_by_lines(result)

            clean_lines = [
                " ".join([item["text"] for item in line])
                for line in lines
            ]

            fields = extractor.extract_fields(clean_lines)

        # ---------------- EXTRACTED FIELDS ----------------
        st.subheader("Extracted Invoice Fields")

        total_data = fields.get("total", {})

        with st.form("invoice_form"):
            col1, col2 = st.columns(2)

            with col1:
                invoice_number = st.text_input(
                    "Invoice Number",
                    value=fields.get("invoice_number", "")
                )

                invoice_date = st.text_input(
                    "Invoice Date",
                    value=fields.get("invoice_date", "")
                )

            with col2:
                due_date = st.text_input(
                    "Due Date",
                    value=fields.get("due_date", "")
                )

                total_value = st.text_input(
                    "Total Amount",
                    value=total_data.get("value", "")
                )

            st.info(f"Confidence Score: {total_data.get('confidence', 'N/A')}")

            submit = st.form_submit_button("Update Fields")

        # ---------------- LINE ITEMS ----------------
        st.subheader("Line Items Table")
        items = fields.get("items", [])

        if items:
            df_items = pd.DataFrame(items)
            st.dataframe(df_items, use_container_width=True)
        else:
            st.warning("No line items detected.")

        # ---------------- RAW OCR EXPANDER ----------------
        with st.expander("View OCR Text Output"):
            for line in clean_lines:
                st.write(line)

        # ---------------- EXPORT ----------------
        st.subheader("Export")

        if st.button("Generate Excel Output"):
            export_data = {
                "invoice_number": invoice_number,
                "invoice_date": invoice_date,
                "due_date": due_date,
                "total": total_data,
                "items": items
            }

            export_to_excel(export_data)

            st.success("Excel generated successfully.")

            with open("output.xlsx", "rb") as f:
                st.download_button(
                    label="⬇ Download Excel File",
                    data=f,
                    file_name="output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        # Cleanup
        os.unlink(temp_path)