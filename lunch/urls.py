from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("otp-verify/<str:phone_number>/", views.otp_verify_view, name="otp_verify"),
    path("reserve_lunch/", views.reserve_lunch, name="reserve_lunch"),
    path("log-out/", views.logout_view, name="account_logout"),
    path("profile/", views.profile_info, name="profile_info"),
    path(
        "send_lunch_reservations_sms/",
        views.send_lunch_reservation_sms,
        name="send_lunch_reservations_sms",
    ),
    path("working_form/", views.create_working_form, name="working_form"),
]
