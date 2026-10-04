from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.contrib.auth.decorators import login_required
from .models import Lunch, OTP, CustomUser
import random
from django.contrib.auth.hashers import make_password
from django.conf import settings
from .utils import send_otp, send_sms
from django.contrib import messages
import jdatetime
import datetime


from .models import Lunch
import jdatetime
from .utils import send_sms
from django.http import HttpResponse
from django.core.cache import cache
from attendance.models import AttendaceRecord
from messaging.models import Notification
from surveys.models import Payslip

from django.contrib.humanize.templatetags.humanize import intcomma


from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display


@login_required
def home(request):
    user = request.user

    this_month_total_time = AttendaceRecord.total_attendance_duration_this_month(
        request.user
    )

    today_lunch = Lunch.is_lunch_requested_today(request.user)

    received_files_count = user.count_received_files()

    notifications = Notification.objects.all().order_by("-created_at")[:3]

    monthly_report_filled = user.has_filled_report_for_previous_month()

    today_attendance = AttendaceRecord.objects.filter(
        user=request.user, date=jdatetime.date.today()
    ).first()
    if today_attendance:
        today_price = (
            AttendaceRecord.duration(today_attendance).total_seconds()
            / 3600
            * user.salary
        )
    else:
        today_price = 0
    payslips = Payslip.objects.filter(user=request.user)[:1]
    print(payslips)
    return render(
        request,
        "home.html",
        {
            "this_month_total_time": int(this_month_total_time),
            "today_lunch": today_lunch,
            "received_files_count": received_files_count,
            "notifications": notifications,
            "monthly_report_filled": monthly_report_filled,
            "today_price": f"{int(today_price):,}",
            "payslips": payslips,
        },
    )


def create_working_form(request):
    user = request.user
    if user.is_authenticated:
        if request.method == "GET":
            return render(request, "lunch/working_form.html")
        elif request.method == "POST":
            receiver = request.POST.get("receiver")
            name = user.first_name + " " + user.last_name
            father = user.father_name
            national_code = user.national_code
            start_date = user.start_date
            role = user.role

            data = {
                "name": name,
                "father": father,
                "national_code": national_code,
                "start_date": start_date.strftime("%Y/%m/%d"),
                "role": role,
                "receiver": receiver,
                "date": jdatetime.date.today().strftime("%Y/%m/%d"),
            }

            image = Image.open(str(settings.BASE_DIR / "static" / "images" / "working_form_base.png")).convert(
                "RGB"
            )

            draw = ImageDraw.Draw(image)

            font_path = str(settings.BASE_DIR / "static" / "fonts" / "fonts" / "ttf" / "Vazirmatn-FD-Bold.ttf")
            font = ImageFont.truetype(font_path, 24)

            # Coordinates for each field (adjust to fit your form layout)
            positions = {
                "name": (620, 645),
                "father": (950, 700),
                "national_code": (650, 700),
                "start_date": (350, 700),
                "role": (770, 750),
                "receiver": (900, 510),
                "date": (1000, 150),
            }

            for key, value in data.items():
                if value is None:
                    text = ""
                else:
                    text = value

                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                x, y = positions[key]
                draw.text((x - text_width, y), text, font=font, fill="black")

            print("Image created with the following data:")

            import os
            from django.http import FileResponse

            forms_dir = str(settings.MEDIA_ROOT / "forms")  # generated files hold personal data: keep out of static
            os.makedirs(forms_dir, exist_ok=True)
            filename = f"{forms_dir}/فرم اشتغال به کار{user.first_name} {user.last_name} برای {receiver}.png"

            # Save or return the image
            image.save(filename)
            response = FileResponse(open(filename, "rb"), content_type="image/png")
            from urllib.parse import quote

            quoted_filename = quote(os.path.basename(filename))
            response["Content-Disposition"] = (
                f"attachment; filename*=UTF-8''{quoted_filename}"
            )
            return response
        else:
            return HttpResponse("Method not allowed", status=405)
    else:
        return redirect("login")


def send_lunch_reservation_sms(request):
    print("Sending lunch reservation SMS...")
    today = jdatetime.date.today()
    if today.strftime("%A") == "چهارشنبه" or today.strftime("%A") == "پنج‌شنبه":
        return HttpResponse("we dont send sms in wednsday and thursday.")
    else:
        tomorrow = today + jdatetime.timedelta(days=1)

    # Retrieve lunch reservations for tomorrow
    reservations = Lunch.objects.filter(date=tomorrow)
    print(tomorrow)
    if reservations:
        # Compose SMS message
        # message = "اسامی ناهار {0}:\n".format(tomorrow.strftime('%A %Y/%m/%d'))
        # print(message)
        message = "\n"
        i = 1
        for reservation in reservations:
            message += (
                f"{i}.{reservation.user.first_name} {reservation.user.last_name}\n"
            )
            i += 1
        message += f"{i}. مهدی امجدی\n"
        message += f"{i+1}. دکتر فشارکی\n"
        message += f"{i+2}. محمد ژیان نسب\n"
        if tomorrow.strftime("%A") != "شنبه":
            message += f"{i+3}. حسن نقیان\n"
            i += 1
        if tomorrow.strftime("%A") == "یک‌شنبه" or tomorrow.strftime("%A") == "سه‌شنبه":
            message += f"{i+3}. عبدالحمید فطانت\n"

        ptrn = {"date": tomorrow.strftime("%A %Y/%m/%d"), "names": message}
        send_sms(settings.SMS_LUNCH_RECIPIENTS, ptrn)
        print("SMS sent")
    else:
        message = "رزروی وجود ندارد"
        print("No reservations found")
    return HttpResponse(message)


def logout_view(request):
    logout(request)
    print("user logged out.")
    return redirect("login")


def register(request):
    if request.user.is_authenticated:
        return redirect("reserve_lunch")
    User = get_user_model()
    context = {}

    if request.method == "POST":
        first_name = request.POST["firstName"]
        last_name = request.POST["lastName"]
        phone_number = request.POST["phone_number"]
        password = request.POST["password1"]
        password2 = request.POST["password2"]

        if password != password2:
            messages.error(request, "گذرواژه ها تطابق ندارند!")
        elif User.objects.filter(phone_number=phone_number).exists():
            messages.error(request, "این شماره تلفن قبلا ثبت شده است.")
        else:
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                password=make_password(password),
            )
            user.save()
            messages.success(request, "کاربر با موفقیت ایجاد شد!")

            return redirect("login")

    return redirect("home")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        phone_number = request.POST["phone_number"]
        password = request.POST.get("password")

        user = authenticate(request, phone_number=phone_number, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            user = CustomUser.objects.filter(phone_number=phone_number).first()
            if user:
                otp = random.randint(1000, 9999)
                cache.set(
                    f"otp_{phone_number}", otp, timeout=300
                )  # Store OTP for 5 minutes
                send_otp(phone_number, otp)
                print(otp)
                print(phone_number)
                messages.error(
                    request, "گذرواژه اشتباه بود، کد یکبار مصرف برای شما ارسال شد."
                )
                return redirect("otp_verify", phone_number=phone_number)
            else:
                messages.error(request, "کاربری با این شماره تلفن وجود ندارد.")
                return redirect("login")

    return render(request, "lunch/login.html")


def otp_verify_view(request, phone_number):
    if request.method == "POST":
        otp = request.POST.get("otp")
        stored_otp = cache.get(f"otp_{phone_number}")
        print(f"stored otp:{stored_otp}")
        print(f"phonenumber is verifyview: {phone_number}")
        if str(otp) == str(stored_otp):
            user = CustomUser.objects.get(phone_number=phone_number)
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "کد یکبار مصرف اشتباه است لطفا مجدد تلاش نمایید.")
    return render(request, "lunch/otp_verify.html", {"phone_number": phone_number})


@login_required
def profile_info(request):
    profile_info = request.user
    return render(request, "lunch/profile_info.html", {"profile_info": profile_info})


@login_required(login_url="login")
def reserve_lunch(request):
    today = jdatetime.date.today()
    tomorrow = today + jdatetime.timedelta(days=1)
    after_tomorrow = tomorrow + jdatetime.timedelta(days=1)
    print(datetime.datetime.now().hour)
    if datetime.datetime.now().hour < 7:
        dates = [(tomorrow + jdatetime.timedelta(days=i)) for i in range(7)]
    else:
        dates = [(after_tomorrow + jdatetime.timedelta(days=i)) for i in range(7)]

    # Remove the dates that the user has already reserved
    reserved_dates = Lunch.objects.filter(
        user=request.user, date__in=dates
    ).values_list("date", flat=True)
    dates_info = []
    for date in dates:
        day_name = date.strftime("%A")
        date_str = date.strftime("%Y/%m/%d")
        # Exclude Thursday and Friday
        if day_name not in ["پنج‌شنبه", "جمعه"]:
            is_reserved = date in reserved_dates
            dates_info.append((day_name, date_str, is_reserved))

    if request.method == "GET":
        return render(request, "lunch/reserve_lunch.html", {"dates": dates_info})

    elif request.method == "POST":
        date_str = request.POST.getlist("selected_dates")
        dates = []
        for item in date_str:
            dates.append(jdatetime.datetime.strptime(item, "%Y/%m/%d").date())

        for date in dates_info:
            # Check if date[1] is not in dates
            if date[1] not in [d.strftime("%Y/%m/%d") for d in dates]:
                lunch_reservation = Lunch.objects.filter(
                    user=request.user,
                    date=jdatetime.datetime.strptime(date[1], "%Y/%m/%d").date(),
                ).first()
                if lunch_reservation:
                    lunch_reservation.delete()
            # Check if date[1] is in dates and date[2] is False
            elif date[1] in [d.strftime("%Y/%m/%d") for d in dates] and not date[2]:
                Lunch.objects.create(
                    user=request.user,
                    date=jdatetime.datetime.strptime(date[1], "%Y/%m/%d").date(),
                    is_lunch_requested=True,
                )

        messages.success(request, f"تغییرات با موفقیت اعمال شد.")
        return redirect("reserve_lunch")
    else:
        messages.error(request, "خطا در ارسال درخواست.")
        return redirect("reserve_lunch")
