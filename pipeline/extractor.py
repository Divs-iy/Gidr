# import os
# import json
# from typing import Any, Dict
# from groq import Groq
# from dotenv import load_dotenv

# load_dotenv()

# class AIExtractor:
#     def __init__(self):
#         api_key = os.getenv("GROQ_API_KEY")
#         if not api_key:
#             raise ValueError("GROQ_API_KEY not found in environment")
#         self.client = Groq(api_key=api_key)

#     def extract_with_groq(self, extracted_data: Any) -> Dict:
#         try:
#             if isinstance(extracted_data, dict):
#                 raw_text = extracted_data.get("raw_text", "")
#             elif isinstance(extracted_data, list):
#                 raw_text = "\n".join([item.get('text', '') for item in extracted_data])
#             else:
#                 raw_text = str(extracted_data)

#             # ✅ Hard cap the text to avoid token bloat and slowness
#             raw_text = raw_text[:4000]

#             prompt = f"""You are a document data extractor. Extract billing data from the OCR text below.

# RULES:
# 1. Only extract data that is EXPLICITLY present in the OCR text. Do NOT guess or invent values.
# 2. DOCUMENT TYPE: If the text contains words like "Premium", "Policy", "Insurance", "CGST", "SGST" — it is INSURANCE. Otherwise it is INVOICE.
# 3. INSURANCE documents: line_items must contain ONLY rows like Net Premium, CGST, SGST, IGST, Stamp Duty. Nothing else.
# 4. INVOICE documents: line_items must contain product/service rows only.
# 5. vendor_name = the company issuing the bill (top of document, not broker or agent).
# 6. total_amount = the final grand total number only.
# 7. date format = YYYY-MM-DD. If unclear, use "".
# 8. confidence_score = how confident you are based on text clarity (0.0 to 1.0).
# 9. If a field is not found in the text, use "" for strings and 0.0 for numbers.
# 10. Return ONLY a JSON object. No explanation, no markdown.

# OUTPUT FORMAT:
# {{
#     "document_type": "",
#     "invoice_number": "",
#     "vendor_name": "",
#     "buyer_name": "",
#     "date": "",
#     "gstin": "",
#     "currency": "INR",
#     "subtotal_amount": 0.0,
#     "tax_amount": 0.0,
#     "total_amount": 0.0,
#     "line_items": [
#         {{"description": "", "quantity": 1, "unit_price": 0.0, "amount": 0.0}}
#     ],
#     "confidence_score": 0.0
# }}

# OCR TEXT:
# {raw_text}"""

#             response = self.client.chat.completions.create(
#                 messages=[{"role": "user", "content": prompt}],
#                 model="llama-3.1-8b-instant",   # ✅ 8b is 10x faster than 70b, accurate enough
#                 temperature=0.0,
#                 response_format={"type": "json_object"},
#                 max_tokens=1000                  # ✅ cap output tokens — stops runaway responses
#             )

#             content = response.choices[0].message.content
#             return json.loads(content)

#         except Exception as e:
#             print(f"Extraction Error: {e}")
#             return {
#                 "invoice_number": "ERROR",
#                 "vendor_name": "Could not extract",
#                 "date": "",
#                 "gstin": "",
#                 "total_amount": 0.0,
#                 "tax_amount": 0.0,
#                 "line_items": [],
#                 "confidence_score": 0.0
#             }

import os
import json
import base64
from typing import Any, Dict
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class AIExtractor:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        self.client = Groq(api_key=api_key)

    def _build_prompt(self) -> str:
        return """You are a document data extractor. Extract billing data from this document image.

STEP 1 — IDENTIFY DOCUMENT TYPE:
- If you see "Premium", "Policy", "Insurance", "CGST", "SGST" → type is "INSURANCE"
- If you see section headers like "Section A", "Section B", SR.NO column, BOQ, WKR, project codes → type is "BOQ_INVOICE"
- Everything else → type is "INVOICE"

STEP 2 — EXTRACT BASED ON TYPE:

IF INSURANCE:
- line_items: ONLY rows like Net Premium, CGST, SGST, IGST, Stamp Duty
- vendor_name: insurance company name (not broker or agent)
- total_amount: final premium payable
- terms_and_conditions: key policy conditions in max 2 sentences

IF BOQ_INVOICE (construction/plumbing/electrical works):
- vendor_name: company name with stamp/letterhead (e.g. "Suryam Developers LLP")
- buyer_name: project name or client name from header
- invoice_number: the actual invoice number or bill number (e.g. "INV-001", "2024-156"). If no invoice number exists, use "".
- date: from header (format YYYY-MM-DD)
- total_amount: GRAND TOTAL of ALL sections combined. Look for a SUMMARY or GRAND TOTAL row at the very end of the document, NOT a section subtotal like "Total of Section A". If the document has sections A, B, C — add all section totals together. Never use a single section total.
- line_items: one row per SR.NO entry that has an amount. Rules:
    * description: SHORT name max 5 words (e.g. "Wall Hung WC", "CP Brass Faucet", "Concealed Cistern")
    * unit: extract unit as-is (No., Rmt., Set, etc.)
    * quantity: number from Qty. column
    * unit_price: number from Rate column
    * amount: number from Amount column
    * SKIP rows with no amount, header rows, note rows, and section total rows
    * SKIP rows that are just notes or conditions (lines starting with #)
- terms_and_conditions: extract ONLY the most important conditions, max 3 bullet points covering:
    * payment or rate inclusions (e.g. "Rates include labour, materials and transportation")
    * scope exclusions (e.g. "Electrical work not included")
    * key quality/compliance notes (e.g. "All fixtures as per IGBC guidelines")
    Format as plain text, no bullet symbols, separated by " | "

IF INVOICE:
- vendor_name: company issuing the bill
- invoice_number: invoice/bill number
- line_items: product/service rows, description max 6 words
- total_amount: final grand total
- terms_and_conditions: payment terms and key conditions, max 2 sentences

GLOBAL RULES:
- Only extract data EXPLICITLY visible. Do NOT guess or invent values.
- date format = YYYY-MM-DD. If unclear, use "".
- confidence_score = clarity of the image (0.0 to 1.0)
- If a field is not found: use "" for strings, 0.0 for numbers
- Return ONLY a JSON object. No explanation, no markdown, no code fences.

OUTPUT FORMAT:
{
    "document_type": "",
    "invoice_number": "",
    "vendor_name": "",
    "buyer_name": "",
    "date": "",
    "gstin": "",
    "currency": "INR",
    "subtotal_amount": 0.0,
    "tax_amount": 0.0,
    "total_amount": 0.0,
    "terms_and_conditions": "",
    "line_items": [
        {
            "description": "",
            "unit": "",
            "quantity": 1,
            "unit_price": 0.0,
            "amount": 0.0
        }
    ],
    "confidence_score": 0.0
}"""

    def extract_with_groq(self, ocr_data: Any) -> Dict:
        try:
            images_b64 = []

            if isinstance(ocr_data, dict):
                images_b64 = ocr_data.get("images_b64", [])
                raw_text = ocr_data.get("raw_text", "")
            elif isinstance(ocr_data, list):
                raw_text = "\n".join([item.get('text', '') for item in ocr_data])
            else:
                raw_text = str(ocr_data)

            # ✅ Vision path — send image directly to Groq (fast, accurate, no local OCR)
            if images_b64:
                # Only send first 2 pages max to keep it fast
                pages_to_send = images_b64[:2]

                content = [{"type": "text", "text": self._build_prompt()}]
                for img_b64 in pages_to_send:
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_b64}"
                        }
                    })

                response = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": content}],
                    model="meta-llama/llama-4-scout-17b-16e-instruct",  # ✅ Groq vision model
                    temperature=0.0,
                    response_format={"type": "json_object"},
                    max_tokens=2000,
                    seed=42
                )

            # ✅ Text fallback path (if somehow only raw_text is available)
            else:
                raw_text = raw_text[:4000]
                response = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": self._build_prompt() + f"\n\nOCR TEXT:\n{raw_text}"}],
                    model="llama-3.1-8b-instant",
                    temperature=0.0,
                    response_format={"type": "json_object"},
                    max_tokens=2000,
                    seed=42
                )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            print(f"Extraction Error: {e}")
            return {
                "invoice_number": "ERROR",
                "vendor_name": "Could not extract",
                "date": "",
                "gstin": "",
                "total_amount": 0.0,
                "tax_amount": 0.0,
                "line_items": [],
                "terms_and_conditions": "",
                "confidence_score": 0.0
            }