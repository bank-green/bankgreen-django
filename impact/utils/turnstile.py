import logging

from django.conf import settings

import requests


logger = logging.getLogger(__name__)


def verify_token(token: str) -> bool:
    """Verify a Cloudflare Turnstile token against the siteverify endpoint. Returns True if valid."""
    if not token:
        return False

    data = {"secret": settings.TURNSTILE_SECRET_KEY, "response": token}

    try:
        response = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify", data=data, timeout=5
        )
        # siteverify returns HTTP 200 even on a failed/invalid token — success lives in the body
        if response.ok and response.json().get("success"):
            return True
        logger.error(f"Turnstile verification failed: {response.text}")
        return False
    except Exception as e:
        logger.error(f"Turnstile verification call failed: {e}")
        return False
