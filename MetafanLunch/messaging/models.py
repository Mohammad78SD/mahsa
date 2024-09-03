from django.db import models
import jdatetime
from django_jalali.db import models as jmodels

class Notification(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = jmodels.jDateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class WebPushSubscription(models.Model):
    subscription_json = models.JSONField()

    def __str__(self):
        return f"Subscription {self.id}"