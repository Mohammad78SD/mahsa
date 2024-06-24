from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from .models import Lunch, OTP, CustomUser
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
import random
from django.contrib.auth.hashers import make_password
from .utils import send_otp, send_sms
from django.contrib import messages
import jdatetime
import datetime
# tasks
# from datetime import datetime, timedelta
from .models import Lunch
import jdatetime
from .utils import send_sms
from django.http import HttpResponse




def send_lunch_reservation_sms(request):
    print('Sending lunch reservation SMS...')
    today = jdatetime.date.today()
    if today.strftime('%A') == 'چهارشنبه':
        tomorrow = today + jdatetime.timedelta(days=3)
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
            message += f"{i}.{reservation.user.first_name} {reservation.user.last_name}\n"
            i+=1
        if (tomorrow.strftime('%A') == 'شنبه' or tomorrow.strftime('%A') == 'دوشنبه' or tomorrow.strftime('%A') == 'چهارشنبه'):
            message += f"{i}. دکتر فشارکی\n"
            i+=1
        message += f"{i}. مهدی امجدی"

        ptrn = {
        'date': tomorrow.strftime('%A %Y/%m/%d'),
        'names': message
        }
        send_sms('***REMOVED***', ptrn)
        print("SMS sent")
    else:
        message = "رزروی وجود ندارد"
        print("No reservations found")
    return HttpResponse(message)


def register(request):
    if request.user.is_authenticated:
        return redirect('reserve_lunch')
    User = get_user_model()
    context = {}

    if request.method == 'POST':
        first_name = request.POST['firstName']
        last_name = request.POST['lastName']
        phone_number = request.POST['phone_number']
        password = request.POST['password1']
        password2 = request.POST['password2']

        if password != password2:
            messages.error(request, 'گذرواژه ها تطابق ندارند!')
        elif User.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'این شماره تلفن قبلا ثبت شده است.')
        else:
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                password=make_password(password),
            )
            user.save()
            messages.success(request, 'کاربر با موفقیت ایجاد شد!')

            return redirect('login')


    return render(request, 'lunch/register.html')



def login_view(request):
    if request.user.is_authenticated:
        return redirect('reserve_lunch')
    
    if request.method == 'POST':
        phone_number = request.POST['phone_number']
        password = request.POST.get('password')
        otp = request.POST.get('otp')

        if password:
            print("in password if of login")
            user = authenticate(request, phone_number=phone_number, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
        elif otp:
            print("in otp if of login")
            otp_obj = OTP.objects.filter(phone_number=phone_number, otp=otp, expiry_time__gte=timezone.now()).first()
            if otp_obj:
                user = CustomUser.objects.get(phone_number=phone_number)
                login(request, user)
                print("user logged in")
                return redirect('home')

        # If password or OTP is not provided or is incorrect, generate a new OTP
        otp = random.randint(1000, 9999)
        expiry_time = timezone.now() + timezone.timedelta(minutes=5)
        OTP.objects.create(phone_number=phone_number, otp=otp, expiry_time=expiry_time)
        send_otp(phone_number, otp)

    return render(request, 'lunch/login.html')

@login_required(login_url='login')
def reserve_lunch(request):
    today = jdatetime.date.today()
    if today.strftime('%A') == 'چهارشنبه':
        tomorrow = today + jdatetime.timedelta(days=3)
    else:
        tomorrow = today + jdatetime.timedelta(days=1)
    after_tomorrow = tomorrow + jdatetime.timedelta(days=1)
    print(datetime.datetime.now().hour)
    if(datetime.datetime.now().hour<16):
        dates = [(tomorrow + jdatetime.timedelta(days=i)) for i in range(7)]
    else:
        dates = [(after_tomorrow + jdatetime.timedelta(days=i)) for i in range(7)]

    # Remove the dates that the user has already reserved
    reserved_dates = Lunch.objects.filter(user=request.user, date__in=dates).values_list('date', flat=True)
    dates_info = []
    for date in dates:
        day_name = date.strftime('%A')
        date_str = date.strftime('%Y/%m/%d')
        # Exclude Thursday and Friday
        if day_name not in ['پنج‌شنبه', 'جمعه']:
            is_reserved = date in reserved_dates
            dates_info.append((day_name, date_str, is_reserved))
    
    if request.method == 'GET':
        return render(request, 'lunch/reserve_lunch.html', {'dates': dates_info})

    elif request.method == 'POST':
        date_str = request.POST.getlist('selected_dates')
        dates = []
        for item in date_str:
            dates.append(jdatetime.datetime.strptime(item, '%Y/%m/%d').date())

        
        for date in dates_info:
            # Check if date[1] is not in dates
            if date[1] not in [d.strftime('%Y/%m/%d') for d in dates]:
                lunch_reservation = Lunch.objects.filter(user=request.user, date=jdatetime.datetime.strptime(date[1], '%Y/%m/%d').date()).first()
                if lunch_reservation:
                    lunch_reservation.delete()
            # Check if date[1] is in dates and date[2] is False
            elif date[1] in [d.strftime('%Y/%m/%d') for d in dates] and not date[2]:
                Lunch.objects.create(user=request.user, date=jdatetime.datetime.strptime(date[1], '%Y/%m/%d').date(), is_lunch_requested=True)

        messages.success(request, f'تغییرات با موفقیت اعمال شد.')
        return redirect('reserve_lunch')