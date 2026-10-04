from django.contrib.auth import get_user_model
from django.db import models
from django_jalali.db import models as jmodels
import jdatetime
from datetime import datetime, time, timedelta
from django.db.models import Q

User = get_user_model()


class AttendaceRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = jmodels.jDateField(default=jdatetime.date.today)
    check_in = models.TimeField()
    check_out = models.TimeField(null=True, blank=True)

    @staticmethod
    def current_month_date_range():
        today = jdatetime.date.today()
        if today.day < 28:
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
            duration = attendance.duration()
            if duration is not None:
                total_duration += duration

        return total_duration.total_seconds() / 3600

    def duration(self):
        """Paid working time for this record.

        Business rules (kept from the original implementation):
        - Missing check-out: now if the record is for today, else 16:00.
        - Friday (the record's own date): worked time + 20%, no break deducted.
        - Otherwise a 1 hour lunch break is deducted when the person checked in
          before noon, except for check-ins before 07:30 (early shift, no break).
          Check-ins from 12:00 on have no deduction. The original code returned
          None for 11:30-12:00; we treat that gap like the rest of the morning
          (break deducted), so the rule is simply "before 12:00".
        """
        check_out = self.check_out
        if check_out is None:
            if self.date == jdatetime.date.today():
                check_out = datetime.now().time()
            else:
                check_out = time(16, 0)
        today = datetime.today()
        duration = datetime.combine(today, check_out) - datetime.combine(today, self.check_in)

        if self.date.weekday() == 6:  # Friday (jdatetime weeks start on Saturday)
            return duration * 1.2
        if self.check_in < time(7, 30) or self.check_in >= time(12, 0):
            return duration
        return max(duration - timedelta(hours=1), timedelta(0))

    def __str__(self):
        return f'{self.user} روز {self.date.strftime("%A %Y/%m/%d")}'

    def set_default_checkou(self):
        if self.check_in and not self.check_out:
            self.check_out = self.check_in.replace(hour=16, minute=0)
            self.save()

    def daily_total_price(self):
        duration = self.duration()
        if duration is None:
            return 0
        duration_in_hours = duration.total_seconds() / 3600
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
