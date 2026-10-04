# tasks.py
from datetime import datetime, timedelta
from .models import Lunch
import jdatetime
from django.conf import settings
from .utils import send_sms

def send_lunch_reservation_sms():
    print('Sending lunch reservation SMS...')
    today = jdatetime.date.today()
    if today.strftime('%A') == 'چهارشنبه':
        tomorrow = today + jdatetime.timedelta(days=3)
    else:
        tomorrow = today + jdatetime.timedelta(days=1)

    # Retrieve lunch reservations for tomorrow
    reservations = Lunch.objects.filter(date=tomorrow)

    if reservations:
        # Compose SMS message
        message = f"اسامی ناهار {tomorrow}:\n"
        for reservation in reservations:
            message += f"{reservation.user.first_name} {reservation.user.last_name}\n"

        send_sms(settings.SMS_LUNCH_RECIPIENTS, message)
