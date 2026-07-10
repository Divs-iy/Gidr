# services/hindsight_service.py
# Vendor memory layer using Hindsight — CORRECTED API

import os
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from hindsight_client import Hindsight
    client = Hindsight(
        base_url=os.getenv("HINDSIGHT_BASE_URL", "https://ui.hindsight.vectorize.io"),
        api_key=os.getenv("HINDSIGHT_API_KEY")
    )
    HINDSIGHT_AVAILABLE = True
    logger.info("✅ Hindsight client initialized")
except Exception as e:
    HINDSIGHT_AVAILABLE = False
    logger.warning(f"⚠️ Hindsight not available: {e}")


def get_bank_id(user_id: int, vendor_name: str) -> str:
    safe_vendor = vendor_name.lower().replace(" ", "_").replace("/", "_")[:40]
    return f"gidr_user_{user_id}_vendor_{safe_vendor}"


def store_invoice_memory(user_id, vendor_name, invoice_number, total_amount, date, line_items):
    if not HINDSIGHT_AVAILABLE:
        return False
    try:
        bank_id = get_bank_id(user_id, vendor_name)
        memory_text = f"""Invoice processed for vendor: {vendor_name}
Invoice Number: {invoice_number}
Date: {date}
Total Amount: {total_amount}
Line Items: {json.dumps(line_items)}
Processed at: {datetime.now().isoformat()}""".strip()

        client.retain(
            bank_id=bank_id,
            content=memory_text,
            metadata={
                "invoice_number": str(invoice_number),
                "total_amount": str(total_amount),
                "date": str(date),
                "vendor": vendor_name,
                "type": "invoice"
            },
            tags=["invoice", vendor_name.lower().replace(" ", "_")]
        )
        logger.info(f"✅ Stored invoice {invoice_number} in Hindsight for {vendor_name}")
        return True
    except Exception as e:
        logger.error(f"Hindsight store error: {e}")
        return False


def check_duplicate_invoice(user_id, vendor_name, invoice_number, total_amount):
    if not HINDSIGHT_AVAILABLE:
        return {"is_duplicate": False, "reason": "", "original_date": None}
    try:
        bank_id = get_bank_id(user_id, vendor_name)
        result = client.recall(
            bank_id=bank_id,
            query=f"invoice number {invoice_number} amount {total_amount}",
            tags=["invoice"]
        )
        facts = getattr(result, "facts", None) or getattr(result, "results", None) or []

        for fact in facts:
            metadata = getattr(fact, "metadata", {}) or {}
            stored_inv_num = str(metadata.get("invoice_number", ""))
            stored_amount = float(metadata.get("total_amount", 0) or 0)

            if stored_inv_num == str(invoice_number):
                return {
                    "is_duplicate": True,
                    "reason": f"Invoice #{invoice_number} was already processed on {metadata.get('date', 'unknown date')}",
                    "original_date": metadata.get("date"),
                    "confidence": "HIGH"
                }
            if abs(stored_amount - float(total_amount)) < 0.01 and stored_amount > 0:
                return {
                    "is_duplicate": True,
                    "reason": f"An invoice of the same amount ₹{total_amount} from {vendor_name} was already processed on {metadata.get('date', 'unknown date')}. Possible duplicate.",
                    "original_date": metadata.get("date"),
                    "confidence": "MEDIUM"
                }
        return {"is_duplicate": False, "reason": "", "original_date": None}
    except Exception as e:
        logger.error(f"Hindsight duplicate check error: {e}")
        return {"is_duplicate": False, "reason": "", "original_date": None}


def check_vendor_anomaly(user_id, vendor_name, total_amount, line_items):
    if not HINDSIGHT_AVAILABLE:
        return {"has_anomaly": False, "alerts": []}
    try:
        bank_id = get_bank_id(user_id, vendor_name)
        result = client.recall(
            bank_id=bank_id,
            query=f"historical invoices total amount for {vendor_name}",
            tags=["invoice"]
        )
        facts = getattr(result, "facts", None) or getattr(result, "results", None) or []

        if len(facts) < 2:
            return {"has_anomaly": False, "alerts": [], "history_count": len(facts)}

        historical_amounts = []
        for f in facts:
            metadata = getattr(f, "metadata", {}) or {}
            amt = metadata.get("total_amount")
            if amt:
                try:
                    historical_amounts.append(float(amt))
                except ValueError:
                    pass

        if not historical_amounts:
            return {"has_anomaly": False, "alerts": []}

        avg_amount = sum(historical_amounts) / len(historical_amounts)
        alerts = []

        if total_amount > avg_amount * 1.15:
            pct_diff = ((total_amount - avg_amount) / avg_amount) * 100
            alerts.append({
                "type": "AMOUNT_SPIKE",
                "severity": "HIGH" if pct_diff > 30 else "MEDIUM",
                "message": f"Total amount ₹{total_amount:,.2f} is {pct_diff:.1f}% above this vendor's average of ₹{avg_amount:,.2f}",
                "avg_historical": round(avg_amount, 2),
                "current": total_amount,
                "pct_above_avg": round(pct_diff, 1)
            })

        return {
            "has_anomaly": len(alerts) > 0,
            "alerts": alerts,
            "history_count": len(facts),
            "avg_historical_amount": round(avg_amount, 2),
            "invoices_analyzed": len(historical_amounts)
        }
    except Exception as e:
        logger.error(f"Hindsight anomaly check error: {e}")
        return {"has_anomaly": False, "alerts": []}


def store_discrepancy_pattern(user_id, vendor_name, discrepancies, invoice_number):
    if not HINDSIGHT_AVAILABLE or not discrepancies:
        return False
    try:
        bank_id = get_bank_id(user_id, vendor_name)
        disc_text = f"""Discrepancy recorded for vendor: {vendor_name}
Invoice: {invoice_number}
Date: {datetime.now().isoformat()}
Discrepancies found: {json.dumps(discrepancies)}""".strip()

        client.retain(
            bank_id=bank_id,
            content=disc_text,
            metadata={
                "type": "discrepancy",
                "invoice_number": str(invoice_number),
                "vendor": vendor_name,
                "discrepancy_count": str(len(discrepancies))
            },
            tags=["discrepancy", vendor_name.lower().replace(" ", "_")]
        )
        logger.info(f"✅ Stored discrepancy pattern for {vendor_name}")
        return True
    except Exception as e:
        logger.error(f"Hindsight discrepancy store error: {e}")
        return False


def query_vendor_intelligence(user_id, question, vendor_name: Optional[str] = None):
    if not HINDSIGHT_AVAILABLE:
        return "Memory system not available right now."
    try:
        bank_id = get_bank_id(user_id, vendor_name) if vendor_name else f"gidr_user_{user_id}"
        result = client.recall(bank_id=bank_id, query=question)
        facts = getattr(result, "facts", None) or getattr(result, "results", None) or []

        if not facts:
            return "No vendor history found yet. Process some invoices first to build memory."

        context_parts = [getattr(f, "content", "") for f in facts[:5] if getattr(f, "content", "")]
        context = "\n---\n".join(context_parts)

        from groq import Groq
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are Gidr's financial intelligence assistant. Answer questions about vendor invoice history concisely based on the context provided."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Hindsight query error: {e}")
        return f"Could not query vendor intelligence: {str(e)}"