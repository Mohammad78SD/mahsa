import json
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification, WebPushSubscription
from .utils import send_web_push

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notification)
def send_notification(sender, instance, created, **kwargs):
    if not created:
        return
    for subscription in WebPushSubscription.objects.all():
        try:
            response = send_web_push(
                subscription_info=subscription.subscription_json,
                message_body=json.dumps({
                    "title": instance.title,
                    "description": instance.description,
                }),
            )
            if not response or response.status_code != 201:
                logger.warning(
                    "Unexpected web push response for subscription %s: %s",
                    subscription.id,
                    response.status_code if response else "no response",
                )
        except Exception:
            logger.exception("Error sending notification to subscription %s", subscription.id)
