from django.urls import path
from . import views

urlpatterns = [
    path('monthly-report/', views.monthly_report, name='monthly_report'),
    path('season-survey/', views.survey_view, name='season_survey'),
    path('payslips/', views.payslip_list, name='payslip_list'),
    path('last-report/', views.last_report, name='last_report'),
]
