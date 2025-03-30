from django.contrib import admin
from surveys.models import MonthlyReport, Season, SeasonSurveyQuestion as Question, SeasonSurveyResponse as Response, Payslip



@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text']

@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ['user', 'season', 'question', 'rating']
    list_filter = ['user', 'season', 'question']

admin.site.register(MonthlyReport)

admin.site.register(Payslip)