from django.contrib.auth import get_user_model
from django.db import models
from django_jalali.db import models as jmodels
import jdatetime
from datetime import datetime, timedelta
from django.db.models import Q

User = get_user_model()


class AttendaceRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = jmodels.jDateField(default=jdatetime.date.today())
    check_in = models.TimeField()
    check_out = models.TimeField(null=True, blank=True)

    @staticmethod
    def current_month_date_range():
        today = jdatetime.date.today()
        if today.day < 21:
            # If today is before the 21st, consider the previous month
            start_month = today.month - 1 if today.month > 1 else 12
            start_year = today.year if today.month > 1 else today.year - 1
            end_month = today.month
            end_year = today.year
        else:
            # If today is 21st or later, consider the current month
            start_month = today.month
            start_year = today.year
            end_month = today.month + 1 if today.month < 12 else 1
            end_year = today.year if today.month < 12 else today.year + 1

        start_date = jdatetime.date(start_year, start_month, 21)
        end_date = jdatetime.date(end_year, end_month, 20)
        return start_date, end_date

    @classmethod
    def filter_current_month_records(cls):
        start_date, end_date = cls.current_month_date_range()
        return cls.objects.filter(date__gte=start_date, date__lte=end_date)

    @classmethod
    def total_attendance_duration_this_month(cls, user):
        if jdatetime.datetime.now().day < 21:
            year = jdatetime.datetime.now().year
            month = jdatetime.datetime.now().month
            j_start_date = (
                jdatetime.date(year, month, 21).replace(month=month - 1)
                if month > 1
                else jdatetime.date(year, month, 21).replace(month=12, year=year - 1)
            )
            j_end_date = jdatetime.date(year, month, 20)

        else:
            year = jdatetime.datetime.now().year
            month = jdatetime.datetime.now().month
            j_start_date = jdatetime.date(year, month, 21)
            j_end_date = (
                jdatetime.date(year, month, 20).replace(month=month + 1)
                if month < 12
                else jdatetime.date(year, month, 20).replace(month=1)
            )
        date_range_query = Q(date__gte=j_start_date) & Q(date__lte=j_end_date)

        attendances = cls.objects.filter(user=user).filter(date_range_query)
        total_duration = timedelta()
        for attendance in attendances:
            total_duration += attendance.duration()

        return total_duration.total_seconds() / 3600

    def duration(self):
        today = jdatetime.date.today()
        # Combine the date with the check-in and check-out times to create datetime objects
        check_in_datetime = datetime.combine(datetime.today(), self.check_in)
        if self.check_out is None and self.date == today:
            self.check_out = datetime.now().time()
        elif self.check_out is None and self.date != today:
            self.check_out = datetime.strptime("16:00", "%H:%M").time()
        check_out_datetime = datetime.combine(datetime.today(), self.check_out)

        if today.weekday() == 6:
            duration = check_out_datetime - check_in_datetime
            # add 20% to the duration
            duration = duration + timedelta(seconds=(duration.total_seconds() * 0.2))
            return duration

        if self.check_in < datetime.strptime("07:30", "%H:%M").time():
            duration = check_out_datetime - check_in_datetime
            return duration

        if self.check_in < datetime.strptime("11:30", "%H:%M").time():
            duration = check_out_datetime - check_in_datetime - timedelta(hours=1)
            return duration

    def __str__(self):
        return f'{self.user} روز {self.date.strftime("%A %Y/%m/%d")}'

    def set_default_checkou(self):
        if self.check_in and not self.check_out:
            self.check_out = self.check_in.replace(hour=16, minute=0)
            self.save()

    def daily_total_price(self):
        duration_in_hours = self.duration().total_seconds() / 3600
        return duration_in_hours * self.user.salary

    def save(self, *args, **kwargs):
        if self.check_in and self.check_out and self.check_in > self.check_out:
            raise ValueError("ساعت ورود نمی‌تواند از ساعت خروج جلوتر باشد.")
        super().save(*args, **kwargs)


class AttendanceRequest(models.Model):
    # if its a new attendance
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = jmodels.jDateField(null=True, blank=True)

    attendance = models.ForeignKey(
        AttendaceRecord,
        on_delete=models.CASCADE,
        related_name="change_requests",
        null=True,
        blank=True,
    )
    requested_check_in = models.TimeField(null=True, blank=True)
    requested_check_out = models.TimeField(null=True, blank=True)
    request_reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="pending",
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True)

    def __str__(self):
        return f"درخواست بازبینی {self.user.last_name} - {self.created_at}"

    def save(self, *args, **kwargs):
        if self.status == "approved":
            if self.attendance:
                self.attendance.check_in = self.requested_check_in
                self.attendance.check_out = self.requested_check_out
                self.attendance.save()
            else:
                self.attendance = AttendaceRecord.objects.create(
                    user=self.user,
                    date=self.date,
                    check_in=self.requested_check_in,
                    check_out=self.requested_check_out,
                )
        super().save(*args, **kwargs)
