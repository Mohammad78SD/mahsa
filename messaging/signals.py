from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification, WebPushSubscription
from .utils import send_web_push
import json

@receiver(post_save, sender=Notification)
def send_notification(sender, instance, created, **kwargs):
    if created:
        print(f"New notification created: {instance.title}")
        subscriptions = WebPushSubscription.objects.all()
        print(f"Number of subscriptions: {subscriptions.count()}")
        for subscription in subscriptions:
            print(f"Sending to subscription: {subscription.id}")
            try:
                response = send_web_push(
                    subscription_info=subscription.subscription_json,
                    message_body=json.dumps({
                        "title": instance.title,
                        "description": instance.description
                    })
                )
                if response and response.status_code == 201:
                    print("Notification sent successfully")
                else:
                    print(f"Unexpected response: {response.status_code if response else 'No response'}")
            except Exception as e:
                print(f"Error sending notification: {str(e)}")
                import traceback
                print(traceback.format_exc())