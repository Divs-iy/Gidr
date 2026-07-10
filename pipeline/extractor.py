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
        self.client = Groq(api_key=api_key, timeout=45.0, max_retries=1)

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
- invoice_number: the actual invoice number or bill number. If none exists, use "".
- date: from header (format YYYY-MM-DD)
- total_amount: GRAND TOTAL of ALL sections combined. Never use a single section total.
- line_items: one row per SR.NO entry that has an amount:
    * description: SHORT name max 5 words
    * unit: extract unit as-is (No., Rmt., Set, etc.)
    * quantity: number from Qty. column
    * unit_price: number from Rate column
    * amount: number from Amount column
    * SKIP rows with no amount, header rows, note rows, section total rows
- terms_and_conditions: max 3 key points separated by " | "

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

            if images_b64:
                pages_to_send = images_b64[:1]
                content = [{"type": "text", "text": self._build_prompt()}]
                for img_b64 in pages_to_send:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                    })

                response = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": content}],
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    temperature=0.0,
                    response_format={"type": "json_object"},
                    max_tokens=2000,
                    seed=42
                )

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

    def _build_smart_prompt(self) -> str:
        return """You are an intelligent document analyzer. Your job is to:
1. Identify what type of document this is
2. Extract ALL important information in the best structured format

DOCUMENT TYPES you may encounter:
- CONTRACT / AGREEMENT (performance, service, employment, vendor)
- INVOICE / BILL
- BOQ (Bill of Quantities)
- INSURANCE POLICY
- PURCHASE ORDER
- RECEIPT
- OTHER (describe what it is)

EXTRACTION RULES:
- Only extract what is EXPLICITLY visible. Never invent or guess.
- For contracts: extract all parties, dates, fees, payment terms, and every section's key points
- For invoices: extract vendor, line items, totals
- For any document: capture ALL terms, conditions, obligations and clauses
- Keep section summaries concise but complete — max 3 sentences per section
- confidence_score = how clearly readable the document is (0.0 to 1.0)

OUTPUT — return ONLY this JSON, no markdown, no explanation:
{
    "document_type": "",
    "title": "",
    "confidence": 0.0,
    "key_fields": [
        {"label": "", "value": ""}
    ],
    "sections_found": [],
    "parties": {
        "party_a": {"name": "", "role": "", "location": ""},
        "party_b": {"name": "", "role": "", "location": ""}
    },
    "dates": {
        "agreement_date": "",
        "start_date": "",
        "end_date": "",
        "other_dates": []
    },
    "financials": {
        "total_amount": 0.0,
        "currency": "",
        "payment_schedule": [],
        "fee_breakdown": [
            {"item": "", "quantity": 1, "unit_price": 0.0, "total": 0.0}
        ]
    },
    "sections": [
        {"section_number": "", "title": "", "summary": "", "key_points": []}
    ],
    "terms_and_conditions": [
        {"category": "", "condition": ""}
    ],
    "cancellation_policy": "",
    "governing_law": "",
    "signatures": []
}"""

    def extract_smart(self, ocr_data: Any) -> dict:
        try:
            images_b64 = []
            if isinstance(ocr_data, dict):
                images_b64 = ocr_data.get("images_b64", [])

            if not images_b64:
                return {"error": "No image data found"}

            pages_to_send = images_b64[:4]
            content = [{"type": "text", "text": self._build_smart_prompt()}]
            for img_b64 in pages_to_send:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                })

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": content}],
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.0,
                response_format={"type": "json_object"},
                max_tokens=3000,
                seed=42
            )

            content_str = response.choices[0].message.content
            return json.loads(content_str)

        except Exception as e:
            print(f"Smart Extraction Error: {e}")
            return {
                "document_type": "ERROR",
                "title": "Could not extract",
                "confidence": 0.0,
                "key_fields": [],
                "sections": [],
                "terms_and_conditions": [],
                "financials": {"total_amount": 0.0, "fee_breakdown": []}
            }