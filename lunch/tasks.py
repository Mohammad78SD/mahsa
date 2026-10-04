from django.conf import settings
import jdatetime

from .models import Lunch
from .utils import send_sms


def send_lunch_reservation_sms():
    """Build tomorrow's lunch list and SMS it to the configured recipients.

    Single source of truth, used by the staff-only view (and usable from a
    scheduler). Returns the text that was (or would have been) reported.
    """
    today = jdatetime.date.today()
    if today.strftime("%A") in ("چهارشنبه", "پنج‌شنبه"):
        return "we dont send sms in wednsday and thursday."
    tomorrow = today + jdatetime.timedelta(days=1)

    reservations = Lunch.objects.filter(date=tomorrow).select_related("user")
    if not reservations:
        return "رزروی وجود ندارد"

    message = "\n"
    i = 1
    for reservation in reservations:
        message += f"{i}.{reservation.user.first_name} {reservation.user.last_name}\n"
        i += 1
    extra_names = list(settings.LUNCH_EXTRA_NAMES)
    weekday = tomorrow.strftime("%A")
    if weekday != "شنبه":
        extra_names += settings.LUNCH_EXTRA_NAMES_NOT_SATURDAY
    if weekday in ("یک‌شنبه", "سه‌شنبه"):
        extra_names += settings.LUNCH_EXTRA_NAMES_SUN_TUE
    for name in extra_names:
        message += f"{i}. {name}\n"
        i += 1

    send_sms(
        settings.SMS_LUNCH_RECIPIENTS,
        {"date": tomorrow.strftime("%A %Y/%m/%d"), "names": message},
    )
    return message
