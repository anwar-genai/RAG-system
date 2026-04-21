import logging
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

_FLAGGED_CATEGORIES = {'hate', 'harassment', 'self-harm', 'sexual/minors', 'violence'}


def is_content_safe(text: str) -> tuple[bool, str]:
    """
    Check text against the OpenAI moderation endpoint (free, ~100ms).
    Returns (is_safe, reason).
    Fails open: if the moderation API is unavailable, allow the request through
    so a service outage never blocks legitimate users.
    """
    try:
        response = _client.moderations.create(input=text)
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
