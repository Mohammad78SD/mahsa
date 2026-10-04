import logging

from django.conf import settings
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)


def send_web_push(subscription_info, message_body):
    vapid_private_key = settings.VAPID_PRIVATE_KEY
    if isinstance(vapid_private_key, (list, tuple)):
        vapid_private_key = vapid_private_key[0]
    try:
        return webpush(
            subscription_info=subscription_info,
            data=message_body,
            vapid_private_key=vapid_private_key,
            vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"},
        )
    except WebPushException as ex:
        logger.warning("Web push failed: %r", ex)
    except Exception:
        logger.exception("Unexpected error sending web push")
        raise
