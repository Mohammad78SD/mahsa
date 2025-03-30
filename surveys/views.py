from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ReportForm, SeasonForm
from .models import Payslip, SeasonSurveyQuestion as Question, SeasonSurveyResponse as Response, MonthlyReport
from django.contrib import messages

@login_required
def monthly_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report_form = form.save(commit=False)
            report_form.user = request.user
            report_form.save()
            messages.success(request, "گزارش ماهانه با موفقیت ثبت شد.")
            return redirect('last_report')
    else:
        form = ReportForm()
    return render(request, 'surveys/report_form.html', {'form': form})

@login_required
def last_report(request):
    report = MonthlyReport.objects.filter(user=request.user).order_by('-created_at')[:1]
    return render(request, 'surveys/last_report.html', {'report': report})


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
            messages.success(request, "نظرسنجی با موفقیت ثبت شد.")
            return redirect('season_survey')
    else:
        Responses = Response.objects.filter(user=request.user)[:1]
        last_season_report = Responses[0].season if Responses else None
        form = SeasonForm()

    return render(request, 'surveys/season_survey.html', {'form': form, 'last_season_report': last_season_report})


@login_required
def payslip_list(request):
    payslips = Payslip.objects.filter(user=request.user)
    return render(request, 'payslips/payslip_list.html', {'payslips': payslips})
