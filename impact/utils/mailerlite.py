import logging
from typing import Optional

from django.conf import settings

import requests

logger = logging.getLogger(__name__)


def subscribe(
    email: str, group_ids: Optional[list[str]] = None, fields: Optional[dict] = None
) -> bool:
    """Subscribe an email to MailerLite group(s). Returns True on success."""
    groups = group_ids or [settings.MAILERLITE_SWITCHED_GROUP_ID]
    if not all(groups):
        logger.error("MailerLite group id is not configured; skipping subscribe")
        return False
    try:
        group_numbers = [int(g) for g in groups]
    except (TypeError, ValueError):
        logger.error(f"MailerLite group id is not numeric: {groups!r}")
        return False
    payload = {"email": email, "groups": group_numbers}
    if fields:
        payload["fields"] = fields
    try:
        response = requests.request(
            "POST",
            f"{settings.MAILERLITE_API_BASE_URL}/subscribers",
            json=payload,
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
    except requests.RequestException as e:
        logger.error(f"MailerLite API call failed: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error in MailerLite subscribe: {e}")
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
    except requests.RequestException as e:
        logger.error(f"MailerLite API call failed: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error in MailerLite unsubscribe: {e}")
        return False
