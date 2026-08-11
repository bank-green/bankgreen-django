import logging
from typing import Optional

from django.conf import settings

import requests


logger = logging.getLogger(__name__)


def subscribe(email: str, group_id: Optional[str] = None) -> bool:
    """Subscribe an email to a MailerLite group. Returns True on success."""
    group = group_id or settings.MAILERLITE_SWITCHED_GROUP_ID
    if not group:
        logger.error("MailerLite group id is not configured; skipping subscribe")
        return False
    try:
        # MailerLite rejects a quoted id with "The groups.0 field must be a number", so the id
        # goes out as a JSON number even though it reaches us as a string from the environment.
        response = requests.request(
            "POST",
            f"{settings.MAILERLITE_API_BASE_URL}/subscribers",
            json={"email": email, "groups": [int(group)]},
            headers={
                "Authorization": f"Bearer {settings.MAILERLITE_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=5,
        )
        if response.ok:
            return True
        logger.error(f"MailerLite API returned {response.status_code}: {response.text}")
        return False
    except Exception as e:
        logger.error(f"MailerLite API call failed: {e}")
        return False


def unsubscribe_from_group(email: str, group_id: str) -> bool:
    """Remove an email from a MailerLite group. Returns True on success.

    The removal endpoint takes a numeric subscriber id, not an address, so the address is
    resolved first. Only the lookup endpoint accepts an email in place of an id.
    """
    headers = {
        "Authorization": f"Bearer {settings.MAILERLITE_API_KEY}",
        "Accept": "application/json",
    }
    try:
        lookup = requests.request(
            "GET",
            f"{settings.MAILERLITE_API_BASE_URL}/subscribers/{email}",
            headers=headers,
            timeout=5,
        )
        if lookup.status_code == 404:
            # Never subscribed, so the address is already out of every group. Expected for
            # respondents who declined marketing — a no-op, not a failure.
            return True
        if not lookup.ok:
            logger.error(f"MailerLite API returned {lookup.status_code}: {lookup.text}")
            return False
        subscriber_id = (lookup.json().get("data") or {}).get("id")
        if not subscriber_id:
            logger.error("MailerLite subscriber lookup returned no id")
            return False

        response = requests.request(
            "DELETE",
            f"{settings.MAILERLITE_API_BASE_URL}/subscribers/{subscriber_id}/groups/{group_id}",
            headers=headers,
            timeout=5,
        )
        if response.ok:
            return True
        logger.error(f"MailerLite API returned {response.status_code}: {response.text}")
        return False
    except Exception as e:
        logger.error(f"MailerLite API call failed: {e}")
        return False
