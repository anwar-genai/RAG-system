import re

MAX_MESSAGE_LENGTH = 1000

_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+(instructions?|prompts?)",
    r"disregard\s+(all\s+)?(previous|prior)\s+(instructions?|prompts?)",
    r"forget\s+(all\s+)?(previous|prior)\s+(instructions?|prompts?)",
    r"you\s+are\s+now\s+(?:a|an|the)\s+",
    r"act\s+as\s+(?:if\s+you\s+are\s+)?(?:a|an|the)\s+",
    r"pretend\s+(?:you\s+are|to\s+be)\s+",
    r"\bjailbreak\b",
    r"\bDAN\s+mode\b",
    r"\bdo\s+anything\s+now\b",
    r"reveal\s+(?:your\s+)?(?:system\s+)?prompt",
    r"what\s+(?:are\s+)?your\s+instructions",
    r"repeat\s+(?:the\s+)?(?:above|system|previous)\s+(?:prompt|instructions?)",
    r"</?(system|user|assistant)>",
    r"\[INST\]|\[/INST\]",
    r"<\|im_start\|>|<\|im_end\|>",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]

# Strip non-printable control characters except tab and newline
_CONTROL_CHAR_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def sanitize_message(text: str) -> tuple[bool, str]:
    """Returns (is_safe, cleaned_text) or (False, error_reason) without touching the network."""
    text = text.strip()

    if not text:
        return False, "Message cannot be empty."

    if len(text) > MAX_MESSAGE_LENGTH:
        return False, f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters."

    for pattern in _COMPILED:
        if pattern.search(text):
            return False, "Message contains disallowed content."

    cleaned = _CONTROL_CHAR_RE.sub('', text)
    return True, cleaned
