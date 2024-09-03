from django.db import models
from lunch.models import CustomUser
from django_jalali.db import models as jmodels
import jdatetime

class MonthlyReport(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text_input = models.TextField()
    month = models.IntegerField(choices=[(i, jdatetime.date(1400, i, 1).strftime('%B')) for i in range(1, 13)])
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "گزارش ماهانه"
        verbose_name_plural = "گزارش های ماهانه"
    def __str__(self):
        moonth = jdatetime.date(1400, self.month , 1).strftime('%B')
        return (f'گزارش {moonth} ماه {self.user.first_name} {self.user.last_name}')
    
    
class Season(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        verbose_name = "فصل"
        verbose_name_plural = "فصل ها"
    def __str__(self):
        return self.name
    
class SeasonSurveyQuestion(models.Model):
    text = models.CharField(max_length=255)
    class Meta:
        verbose_name = "سوال نظرسنجی"
        verbose_name_plural = "سوال های نظرسنجی"
    def __str__(self):
        return self.text
    
class SeasonSurveyResponse(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    question = models.ForeignKey(SeasonSurveyQuestion, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'season', 'question')
        verbose_name = "پاسخ نظرسنجی"
        verbose_name_plural = "پاسخ های نظرسنجی"
        
    def __str__(self):
        return (f'نظرسنجی فصل {self.season.name} {self.user.first_name} {self.user.last_name}')
    

class Payslip(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = jmodels.jDateField()
    file = models.FileField(upload_to='payslips/')
    def __str__(self):
        return f'فیش حقوقی {self.date.strftime('%B')} ماه {self.user.first_name} {self.user.last_name}'
    class Meta:
        verbose_name = "فیش حقوقی"
        verbose_name_plural = "فیش حقوقی"