from django.conf import settings
from ippanel import Client


def _client():
    return Client(settings.SMS_API_KEY)


def send_otp(phone_number, otp):
    """Send a one-time login code via an ippanel pattern."""
    ptrn = {"code": otp}
    _client().send_pattern(
        settings.SMS_OTP_PATTERN, settings.SMS_SENDER, str(phone_number), ptrn
    )
    return True


def send_sms(phone_number, ptrn):
    """Send the lunch-list pattern message to each number in `phone_number`."""
    client = _client()
    for num in phone_number:
        client.send_pattern(
            settings.SMS_LUNCH_PATTERN, settings.SMS_SENDER, str(num), ptrn
        )
