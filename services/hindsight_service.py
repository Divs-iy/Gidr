# services/hindsight_service.py
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
    safe_vendor = vendor_name.lower().replace(" ", "_").replace("/", "_")
    bank_id = f"gidr_u{user_id}_{safe_vendor}"
    logger.info(f"🏦 bank_id generated: {bank_id}")  # ✅ ADD
    return bank_id
    # return f"gidr_user_{user_id}_vendor_{safe_vendor}"


async def store_invoice_memory(user_id, vendor_name, invoice_number, total_amount, date, line_items):
    if not HINDSIGHT_AVAILABLE:
        return False
    try:
        memory_text = f"""Invoice processed for vendor: {vendor_name}
Invoice Number: {invoice_number}
Date: {date}
Total Amount: {total_amount}
Line Items: {json.dumps(line_items)}
Processed at: {datetime.now().isoformat()}""".strip()

        metadata = {
            "invoice_number": str(invoice_number),
            "total_amount": str(total_amount),
            "date": str(date),
            "vendor": vendor_name,
            "type": "invoice"
        }
        tags = ["invoice", vendor_name.lower().replace(" ", "_")]

        bank_id = get_bank_id(user_id, vendor_name)
        await client.aretain(bank_id=bank_id, content=memory_text, metadata=metadata, tags=tags)

        global_bank_id = f"gidr_user_{user_id}"
        await client.aretain(bank_id=global_bank_id, content=memory_text, metadata=metadata, tags=tags)

        logger.info(f"✅ Stored invoice {invoice_number} in Hindsight for {vendor_name}")
        return True
    except Exception as e:
        logger.error(f"Hindsight store error: {e}")
        return False


async def check_duplicate_invoice(user_id, vendor_name, invoice_number, total_amount):
    if not HINDSIGHT_AVAILABLE:
        return {"is_duplicate": False, "reason": "", "original_date": None}
    try:
        bank_id = get_bank_id(user_id, vendor_name)
        result = await client.arecall(
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


async def check_vendor_anomaly(user_id, vendor_name, total_amount, line_items):
    if not HINDSIGHT_AVAILABLE:
        return {"has_anomaly": False, "alerts": []}
    try:
        bank_id = get_bank_id(user_id, vendor_name)
        result = await client.arecall(
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


async def store_discrepancy_pattern(user_id, vendor_name, discrepancies, invoice_number):
    if not HINDSIGHT_AVAILABLE or not discrepancies:
        return False
    try:
        bank_id = get_bank_id(user_id, vendor_name)
        disc_text = f"""Discrepancy recorded for vendor: {vendor_name}
Invoice: {invoice_number}
Date: {datetime.now().isoformat()}
Discrepancies found: {json.dumps(discrepancies)}""".strip()

        await client.aretain(
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


async def query_vendor_intelligence(user_id, question, vendor_name=None):
    if not HINDSIGHT_AVAILABLE:
        return {"answer": "Memory system not available right now.", "model_used": None, "cost": None}
    try:
        # ✅ Query multiple bank_ids to catch memories stored with any format
        bank_ids_to_try = [
            f"gidr_user_{user_id}",           # global bank
            f"gidr_u{user_id}",               # new global format
        ]
        if vendor_name:
            safe = vendor_name.lower().replace(" ", "_").replace("/", "_")
            bank_ids_to_try += [
                f"gidr_u{user_id}_{safe}",                    # new format
                f"gidr_user_{user_id}_vendor_{safe}",         # old format
                f"gidr_user_{user_id}_vendor_{safe[:40]}",    # old truncated
            ]

        all_facts = []
        for bid in bank_ids_to_try:
            try:
                logger.info(f"🔍 Trying bank_id: {bid}")
                result = await client.arecall(bank_id=bid, query=question)
                facts = getattr(result, "facts", None) or getattr(result, "results", None) or []
                all_facts.extend(facts)
                if all_facts:
                    logger.info(f"✅ Found {len(facts)} facts in {bid}")
            except Exception as e:
                logger.warning(f"bank_id {bid} failed: {e}")
                continue

        if not all_facts:
            return {
                "answer": "No vendor history found yet. Process some invoices first to build memory.",
                "model_used": None,
                "cost": None
            }

        context_parts = [getattr(f, "content", "") for f in all_facts[:5] if getattr(f, "content", "")]
        context = "\n---\n".join(context_parts)

        from services.cascadeflow_service import route_extraction

        is_complex = len(all_facts) > 5 or any(
            w in question.lower() for w in ["compare", "trend", "why", "analyze", "pattern"]
        )

        prompt = f"""You are Gidr's financial intelligence assistant. Answer ONLY using the vendor history context below. If the context does not contain enough information, say "I don't have enough history to answer that yet."

Context:
{context}

Question: {question}

Give a concise, specific answer using only real data explicitly present in the context above."""

        routed = route_extraction(prompt, is_complex=is_complex)

        return {
            "answer": routed.get("result", "Could not generate answer"),
            "model_used": routed.get("model_used"),
            "cost": routed.get("cost"),
            "routed_via": routed.get("routed_via"),
            "complexity": "complex" if is_complex else "simple"
        }

    except Exception as e:
        logger.error(f"Hindsight query error: {e}")
        return {"answer": f"Could not query vendor intelligence: {str(e)}", "model_used": None, "cost": None}