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

    import httpx
    http_timeout = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
    kwargs = {
        'api_key': os.environ.get('OPENAI_API_KEY'),
        'max_retries': 0,  # fail-open is cheaper than retrying a dead endpoint
    }
    proxy = os.environ.get('OPENAI_PROXY', '').strip()
    if proxy:
        kwargs['http_client'] = httpx.Client(proxy=proxy, timeout=http_timeout)
    else:
        kwargs['http_client'] = httpx.Client(timeout=http_timeout)

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
        # Short timeout — moderation is a pre-check; if the provider is flaky
        # we fail open immediately rather than making the user wait 60s.
        response = _get_client().moderations.create(input=text, timeout=3.0)
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
