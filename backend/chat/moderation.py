import logging
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

_FLAGGED_CATEGORIES = {'hate', 'harassment', 'self-harm', 'sexual/minors', 'violence'}

_client = None


def _get_client() -> OpenAI:
    """Lazily build the OpenAI client so OPENAI_PROXY and env-loaded API keys are picked up."""
    global _client
    if _client is not None:
        return _client

    kwargs = {'api_key': os.environ.get('OPENAI_API_KEY')}
    proxy = os.environ.get('OPENAI_PROXY', '').strip()
    if proxy:
        import httpx
        kwargs['http_client'] = httpx.Client(proxy=proxy)

    _client = OpenAI(**kwargs)
    return _client


def is_content_safe(text: str) -> tuple[bool, str]:
    """
    Check text against the OpenAI moderation endpoint (free, ~100ms).
    Returns (is_safe, reason).
    Fails open: if the moderation API is unavailable, allow the request through
    so a service outage never blocks legitimate users.
    """
    try:
        response = _get_client().moderations.create(input=text)
        result = response.results[0]
        if result.flagged:
            triggered = [
                cat for cat, flagged in result.categories.__dict__.items()
                if flagged and cat in _FLAGGED_CATEGORIES
            ]
            return False, f"Content flagged: {', '.join(triggered)}"
        return True, text
    except Exception as exc:
        logger.warning("Moderation API unavailable, failing open: %s", exc)
        return True, text
