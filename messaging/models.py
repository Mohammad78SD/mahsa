from django.db import models
import jdatetime
from django_jalali.db import models as jmodels
from lunch.models import CustomUser as User
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
    

class SharedFile(models.Model):
    file = models.FileField(upload_to='shared_files/', verbose_name="فایل")  # Store files in a dedicated directory
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_files', verbose_name="فرستنده")
    recipients = models.ManyToManyField(User, related_name='received_files', verbose_name="گیرندگان")
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ارسال")
    name = models.CharField(max_length=255, blank=True, verbose_name= "نام فایل") # Store original filename
    seen = models.BooleanField(default=False, verbose_name="خوانده شده؟")
    
    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.file.name # Store the original filename
        super().save(*args, **kwargs)
        
