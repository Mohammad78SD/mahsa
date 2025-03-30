from attendance.models import AttendaceRecord


def site_info(request):
    if(request.user.is_anonymous):
        return {}
    this_month_total_time = AttendaceRecord.total_attendance_duration_this_month(request.user)
    print(f"this_month_total_time: {this_month_total_time}")
    this_month_total_price = this_month_total_time * request.user.salary
    return {
        'this_month_total_price': f"{int(this_month_total_price):,}",
    }