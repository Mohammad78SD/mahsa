from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('reserve_lunch/', views.reserve_lunch, name='reserve_lunch'),
    path('log-out/', views.logout_view, name='account_logout'),
    path('send_lunch_reservations_sms/', views.send_lunch_reservation_sms, name='send_lunch_reservations_sms'),
    
]