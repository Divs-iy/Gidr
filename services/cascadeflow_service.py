# services/cascadeflow_service.py

import os
import logging
import asyncio
import concurrent.futures

logger = logging.getLogger(__name__)

try:
    from cascadeflow import get_balanced_agent
    cascade_agent = get_balanced_agent(verbose=False, enable_cascade=True)
    CASCADE_AVAILABLE = True
    logger.info("✅ cascadeflow initialized (balanced agent)")
except Exception as e:
    CASCADE_AVAILABLE = False
    logger.warning(f"⚠️ cascadeflow not available: {e}")

from groq import Groq
groq_fallback = Groq(api_key=os.getenv("GROQ_API_KEY"))


def route_extraction(prompt: str, is_complex: bool = False) -> dict:
    fallback_model = "llama-3.3-70b-versatile" if is_complex else "llama-3.1-8b-instant"

    if not CASCADE_AVAILABLE:
        try:
            response = groq_fallback.chat.completions.create(
                model=fallback_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            return {
                "result": response.choices[0].message.content,
                "model_used": fallback_model,
                "cost": "unknown",
                "routed_via": "direct_fallback"
            }
        except Exception as e:
            logger.error(f"Groq fallback error: {e}")
            return {"result": "Could not generate answer.", "model_used": None, "cost": None, "routed_via": "error"}

    try:
        complexity_hint = "complex" if is_complex else "simple"

        # ✅ Run cascade in a fresh thread with its own event loop
        # asyncio.run() fails inside FastAPI's running loop — new thread fixes this
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    cascade_agent.run(
                        query=prompt,
                        max_tokens=400,
                        complexity_hint=complexity_hint
                    )
                )
                return result
            finally:
                loop.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(run_in_thread)
            result = future.result(timeout=30)

        return {
            "result": getattr(result, "content", None) or getattr(result, "text", str(result)),
            "model_used": getattr(result, "model", None) or getattr(result, "model_used", fallback_model),
            "cost": getattr(result, "cost", None) or getattr(result, "total_cost", "unknown"),
            "latency_ms": getattr(result, "latency_ms", None),
            "routed_via": "cascadeflow"
        }

    except Exception as e:
        logger.error(f"cascadeflow run error: {e}")
        try:
            response = groq_fallback.chat.completions.create(
                model=fallback_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            return {
                "result": response.choices[0].message.content,
                "model_used": fallback_model,
                "cost": "unknown",
                "routed_via": "fallback_after_error"
            }
        except Exception as e2:
            logger.error(f"Groq fallback also failed: {e2}")
            return {"result": "Could not generate answer.", "model_used": None, "cost": None, "routed_via": "error"}


def get_audit_trail() -> list:
    if not CASCADE_AVAILABLE:
        return []
    try:
        return cascade_agent.get_stats()
    except Exception:
        return []