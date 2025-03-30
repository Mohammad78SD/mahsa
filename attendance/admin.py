from django.contrib import admin
from .models import AttendaceRecord, AttendanceRequest
# Register your models here.
admin.site.register(AttendaceRecord)


class AttendanceRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'date')
    date_hierarchy = 'created_at'
    ordering = ('created_at',)
admin.site.register(AttendanceRequest, AttendanceRequestAdmin)