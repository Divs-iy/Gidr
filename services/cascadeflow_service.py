# services/cascadeflow_service.py

import os
import logging

logger = logging.getLogger(__name__)

try:
    from cascadeflow import Cascade
    cascade_client = Cascade(
        providers=["groq"],
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    CASCADE_AVAILABLE = True
    logger.info("✅ cascadeflow initialized")
except Exception as e:
    CASCADE_AVAILABLE = False
    logger.warning(f"⚠️ cascadeflow not available: {e}")

from groq import Groq
groq_fallback = Groq(api_key=os.getenv("GROQ_API_KEY"))


def route_extraction(ocr_text: str, is_complex: bool = False) -> dict:
    """
    Routes invoice extraction to cheap or powerful model based on complexity.
    Returns extracted data + cost/model metadata for audit trail.
    """
    model = "llama3-70b-8192" if is_complex else "llama3-8b-8192"

    if not CASCADE_AVAILABLE:
        # Fallback: direct Groq call
        response = groq_fallback.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": ocr_text}],
            max_tokens=1000
        )
        return {
            "result": response.choices[0].message.content,
            "model_used": model,
            "cost": "unknown",
            "routed_via": "direct_fallback"
        }

    try:
        result = cascade_client.run(
            prompt=ocr_text,
            budget_tier="low" if not is_complex else "high"
        )
        return {
            "result": result.get("output"),
            "model_used": result.get("model"),
            "cost": result.get("cost"),
            "latency_ms": result.get("latency_ms"),
            "routed_via": "cascadeflow"
        }
    except Exception as e:
        logger.error(f"cascadeflow error: {e}")
        response = groq_fallback.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": ocr_text}],
            max_tokens=1000
        )
        return {
            "result": response.choices[0].message.content,
            "model_used": model,
            "cost": "unknown",
            "routed_via": "fallback_after_error"
        }


def get_audit_trail() -> list:
    """Returns list of all routing decisions made this session."""
    if not CASCADE_AVAILABLE:
        return []
    try:
        return cascade_client.get_audit_log()
    except Exception:
        return []