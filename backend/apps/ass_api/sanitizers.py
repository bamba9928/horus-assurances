import re
from collections.abc import Mapping

REDACTED = "***REDACTED***"

SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "basic",
    "client_secret",
    "password",
    "secret",
    "token",
    "username",
}

SENSITIVE_PATTERNS = [
    re.compile(r"(basic\s+)[a-z0-9+/=._:-]+", re.IGNORECASE),
    re.compile(r"(bearer\s+)[a-z0-9._~+/-]+", re.IGNORECASE),
    re.compile(r"(password\s*[=:]\s*)[^\s,;]+", re.IGNORECASE),
    re.compile(r"(token\s*[=:]\s*)[^\s,;]+", re.IGNORECASE),
    re.compile(r"(secret\s*[=:]\s*)[^\s,;]+", re.IGNORECASE),
    re.compile(r"(api[_-]?key\s*[=:]\s*)[^\s,;]+", re.IGNORECASE),
]


def is_sensitive_key(key) -> bool:
    normalized_key = str(key).lower().replace("-", "_")
    return normalized_key in SENSITIVE_KEYS or any(
        sensitive_key in normalized_key
        for sensitive_key in ("password", "token", "secret", "authorization", "api_key")
    )


def sanitize_value(value):
    if isinstance(value, Mapping):
        return {
            key: REDACTED if is_sensitive_key(key) else sanitize_value(nested_value)
            for key, nested_value in value.items()
        }

    if isinstance(value, list):
        return [sanitize_value(item) for item in value]

    if isinstance(value, tuple):
        return [sanitize_value(item) for item in value]

    if isinstance(value, str):
        sanitized = value
        for pattern in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(r"\1" + REDACTED, sanitized)
        return sanitized

    return value


def sanitize_error_message(message: str) -> str:
    return sanitize_value(message or "")
