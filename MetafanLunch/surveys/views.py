from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ReportForm, SeasonForm
from .models import Payslip, SeasonSurveyQuestion as Question, SeasonSurveyResponse as Response

@login_required
def monthly_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report_form = form.save(commit=False)
            report_form.user = request.user
            report_form.save()
            return redirect('success')
    else:
        form = ReportForm()
    return render(request, 'surveys/report_form.html', {'form': form})

def success(request):
    return render(request, 'surveys/success.html')



@login_required
def survey_view(request):
    if request.method == "POST":
        form = SeasonForm(request.POST)
        if form.is_valid():
            season = form.cleaned_data['season']
            for question in Question.objects.all():
                rating = form.cleaned_data[f'rating_{question.id}']
                Response.objects.update_or_create(
                    user=request.user,
                    season=season,
                    question=question,
                    defaults={'rating': rating}
                )
            return redirect('success')
    else:
        form = SeasonForm()

    return render(request, 'surveys/season_survey.html', {'form': form})

def survey_success(request):
    return render(request, 'surveys/success.html')


@login_required
def payslip_list(request):
    payslips = Payslip.objects.filter(user=request.user)
    return render(request, 'payslips/payslip_list.html', {'payslips': payslips})
