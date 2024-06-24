from django import forms
from .models import MonthlyReport, Season, SeasonSurveyQuestion as Question
import jdatetime


MONTH_CHOICES = [(i, jdatetime.date(1400, i, 1).strftime('%B')) for i in range(1, 13)]
class ReportForm(forms.ModelForm):
    month = forms.ChoiceField(choices=MONTH_CHOICES, label="انتخاب ماه", widget=forms.Select)
    class Meta:
        model = MonthlyReport
        fields = ['text_input', 'month']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text_input'].label = "متن گزارش"

class SeasonForm(forms.Form):
    season = forms.ModelChoiceField(queryset=Season.objects.all(), label="انتخاب فصل")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        questions = Question.objects.all()
        for question in questions:
            self.fields[f'rating_{question.id}'] = forms.ChoiceField(
                choices=[(i, str(i)) for i in range(1, 6)],
                widget=forms.RadioSelect,
                label=question.text
            )