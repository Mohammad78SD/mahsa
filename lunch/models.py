from django.db import models
from django_jalali.db import models as jmodels
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.conf import settings
import jdatetime


class Lunch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    date = jmodels.jDateField()
    is_lunch_requested = models.BooleanField(default=False)

    @classmethod
    def is_lunch_requested_today(cls, user):
        today = jdatetime.datetime.now().date()
        return cls.objects.filter(user=user, date=today).exists()

    class Meta:
        unique_together = ("user", "date")

    class Meta:
        verbose_name = "رزرو"
        verbose_name_plural = "رزروها"

    def __str__(self):
        return "رزرو %s در روز %s" % (self.user, self.date.strftime("%A %Y/%m/%d"))


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The Phone number field must be set")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(phone_number, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    avatar = models.ImageField(
        upload_to="avatars/", null=True, blank=True, verbose_name="تصویر پروفایل"
    )
    phone_number = models.CharField(
        max_length=15, unique=True, verbose_name="شماره موبایل"
    )
    first_name = models.CharField(max_length=30, verbose_name="نام")
    last_name = models.CharField(max_length=30, verbose_name="نام خانوادگی")
    sex = models.CharField(
        max_length=10,
        verbose_name="جنسیت",
        choices=[("man", "مرد"), ("woman", "زن")],
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=30, verbose_name="سمت", null=True, blank=True)
    father_name = models.CharField(
        max_length=30, verbose_name="نام پدر", null=True, blank=True
    )
    birthdate = jmodels.jDateField(verbose_name="تاریخ تولد", null=True, blank=True)
    national_code = models.CharField(
        max_length=10, verbose_name="کد ملی", null=True, blank=True
    )
    address = models.TextField(verbose_name="آدرس", null=True, blank=True)
    postal_code = models.CharField(
        max_length=10, verbose_name="کد پستی", null=True, blank=True
    )
    education = models.CharField(
        max_length=30, verbose_name="آخرین مدرک تحصیلی", null=True, blank=True
    )
    major = models.CharField(
        max_length=30, verbose_name="رشته تحصیلی", null=True, blank=True
    )
    start_date = jmodels.jDateField(
        verbose_name="تاریخ شروع به کار", null=True, blank=True
    )
    salary = models.PositiveIntegerField(verbose_name="حقوق ساعتی", default=0)
    description = models.TextField(verbose_name="توضیحات", null=True, blank=True)
    end_date = jmodels.jDateField(verbose_name="تاریخ پایان کار", null=True, blank=True)
    rfid = models.CharField(
        max_length=10, verbose_name="کد RFID", null=True, blank=True
    )

    is_file = models.BooleanField(default=False, verbose_name="کاربر فایلی است؟")
    is_active = models.BooleanField(default=True, verbose_name="وضعیت کاربر")
    is_staff = models.BooleanField(default=False, verbose_name="آیا ادمین است؟")

    objects = CustomUserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def has_filled_report_for_previous_month(self):
        today = jdatetime.date.today()
        previous_month = today.month - 1 if today.month > 1 else 12
        previous_year = today.year if today.month > 1 else today.year - 1

        print(previous_month, previous_year)
        from surveys.models import MonthlyReport

        start_date = jdatetime.date(previous_year, 1, 1)
        end_date = jdatetime.date(previous_year, 12, 29)
        return MonthlyReport.objects.filter(
            user=self,
            month=previous_month,
            created_at__gte=start_date,
            created_at__lte=end_date,
        ).exists()

    def count_received_files(self):
        return self.received_files.filter(seen=False).count()

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return self.first_name + " " + self.last_name


class OTP(models.Model):
    phone_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    expiry_time = models.DateTimeField()

    def __str__(self):
        return self.phone_number + " : " + self.otp
