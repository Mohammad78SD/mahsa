from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from surveys.models import MonthlyReport

User = get_user_model()


class SurveyViewTests(TestCase):
    def test_views_require_login(self):
        for name in ("monthly_report", "season_survey", "payslip_list", "last_report"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)

    def test_monthly_report_submission_saved_for_current_user(self):
        user = User.objects.create_user(
            phone_number="09120000060", password="x", first_name="T", last_name="U"
        )
        self.client.force_login(user)
        response = self.client.post(reverse("monthly_report"), {"text_input": "done", "month": 3})
        self.assertRedirects(response, reverse("last_report"), fetch_redirect_response=False)
        self.assertEqual(MonthlyReport.objects.get(user=user).month, 3)


class MonthChoicesTests(TestCase):
    def test_choices_are_static_jalali_names(self):
        from surveys.models import JALALI_MONTHS

        choices = MonthlyReport._meta.get_field("month").choices
        self.assertEqual(choices, JALALI_MONTHS)
        self.assertEqual(len(choices), 12)
        self.assertEqual(choices[0], (1, "فروردین"))
        self.assertEqual(choices[11], (12, "اسفند"))
