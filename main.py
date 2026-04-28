from pipeline.preprocess import Preprocessor
from pipeline.ocr import OCRProcessor
from pipeline.layout import LayoutParser
from pipeline.extractor import Extractor
from utils.excel_exporter import export_to_excel

if __name__ == "__main__":
    pre = Preprocessor()
    ocr = OCRProcessor()
    layout = LayoutParser()
    extractor = Extractor()

    path = "data/raw/invoice11.jpeg"

    # Step 1: preprocess
    #image = pre.preprocess(path)

    # Step 2: OCR
    result = ocr.run_ocr(path)

    print("Number of detections:", len(result))

    # Step 3: Layout (NOW actually used)
    lines = layout.group_by_lines(result)

    print("\n--- LAYOUT SAMPLE ---")
    for i, line in enumerate(lines[:5]):
        print(" | ".join([x["text"] for x in line]))

    # Step 4: extraction (still raw OCR for now)
    clean_lines = [
    " ".join([item["text"] for item in line])
    for line in lines
]
    fields = extractor.extract_fields(clean_lines)
    for l in clean_lines:
        print(l)

    print("\n---Extracted Fields---")
    print(f"Invoice Number: {fields['invoice_number']}")
    print(f"Invoice Date: {fields['invoice_date']}")
    print(f"Due Date: {fields['due_date']}")
    print(f"Total: {fields['total']}")
    print("\n--- LINE ITEMS ---")
    for item in fields["items"]:
        print(item)
    # Step 5: Export to Excel
    export_to_excel(fields)