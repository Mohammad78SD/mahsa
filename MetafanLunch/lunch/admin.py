from django.contrib import admin
from lunch.models import Lunch, CustomUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import jdatetime
from datetime import datetime, timedelta
from django.contrib.auth.models import Group

class ShamsiDateRangeFilter(admin.SimpleListFilter):
    title = _('تاریخ ماهانه')
    parameter_name = 'shamsi_date_range'

    def lookups(self, request, model_admin):
        return (
            ('current', _('ماه جاری')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'current':
            today = timezone.now().date()
            j_today = jdatetime.date.fromgregorian(date=today)
            
            # Calculate start and end dates for the current Shamsi month range
            if j_today.month == 1:
                start_date_jalali = jdatetime.date(j_today.year - 1, 12, 25)
            else:
                start_date_jalali = jdatetime.date(j_today.year, j_today.month - 1, 25)
                    
            end_date_jalali = jdatetime.date(j_today.year, j_today.month, 25)
            
            print(start_date_jalali, end_date_jalali)
            return queryset.filter(date__range=(start_date_jalali, end_date_jalali))
    
        
        return queryset

class Filter(admin.ModelAdmin):
    list_display = ("user_name", "dates")
    list_filter = ("user", ShamsiDateRangeFilter, "date")
    
    def user_name(self, obj):
        return obj.user
    def dates(self, obj):
        return obj.date
    
    user_name.short_description = 'کاربر'
    dates.short_description = 'تاریخ'
admin.site.register(Lunch, Filter)

admin.site.register(CustomUser)
admin.site.unregister(Group)