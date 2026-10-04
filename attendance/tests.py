from datetime import time
from unittest import mock

import jdatetime
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from attendance.models import AttendaceRecord, AttendanceRequest

User = get_user_model()


def make_user(phone="09120000090", **kw):
    return User.objects.create_user(
        phone_number=phone, password="pass12345", first_name="T", last_name="U", **kw
    )


PAST = jdatetime.date(1404, 1, 2)


class AttendanceRecordTests(TestCase):
    def setUp(self):
        self.user = make_user(salary=100000)

    def _duration(self, check_in, check_out):
        record = AttendaceRecord(user=self.user, date=PAST, check_in=check_in, check_out=check_out)
        # Pin "today" to a non special weekday so the result is deterministic.
        with mock.patch.object(jdatetime.date, "today", return_value=jdatetime.date(1404, 1, 5)):
            return record.duration()

    def test_check_in_after_check_out_rejected(self):
        with self.assertRaises(ValueError):
            AttendaceRecord.objects.create(
                user=self.user, date=PAST, check_in=time(17, 0), check_out=time(9, 0)
            )

    def test_early_check_in_has_no_break_deducted(self):
        self.assertEqual(self._duration(time(7, 0), time(15, 0)).total_seconds(), 8 * 3600)

    def test_morning_check_in_deducts_one_hour_break(self):
        self.assertEqual(self._duration(time(8, 0), time(16, 0)).total_seconds(), 7 * 3600)

    def test_afternoon_check_in_no_deduction(self):
        self.assertEqual(self._duration(time(13, 0), time(17, 0)).total_seconds(), 4 * 3600)

    def test_missing_check_out_on_past_day_defaults_to_1600(self):
        self.assertEqual(self._duration(time(7, 0), None).total_seconds(), 9 * 3600)

    def test_daily_total_price_uses_salary(self):
        record = AttendaceRecord.objects.create(
            user=self.user, date=PAST, check_in=time(7, 0), check_out=time(8, 0)
        )
        with mock.patch.object(jdatetime.date, "today", return_value=jdatetime.date(1404, 1, 5)):
            self.assertAlmostEqual(record.daily_total_price(), 100000)

    def test_month_range_runs_from_21st_to_20th(self):
        start, end = AttendaceRecord.current_month_date_range()
        self.assertEqual((start.day, end.day), (21, 20))
        self.assertLess(start, end)


class AttendanceRequestTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_approving_new_request_creates_record(self):
        req = AttendanceRequest.objects.create(
            user=self.user,
            date=PAST,
            requested_check_in=time(8, 0),
            requested_check_out=time(16, 0),
            request_reason="forgot to clock in",
        )
        self.assertEqual(req.status, "pending")
        self.assertFalse(AttendaceRecord.objects.exists())
        req.status = "approved"
        req.save()
        record = AttendaceRecord.objects.get(user=self.user)
        self.assertEqual((record.date.strftime("%Y/%m/%d"), record.check_in), ("1404/01/02", time(8, 0)))

    def test_approving_change_request_updates_existing_record(self):
        record = AttendaceRecord.objects.create(
            user=self.user, date=PAST, check_in=time(9, 0), check_out=time(15, 0)
        )
        req = AttendanceRequest.objects.create(
            user=self.user,
            date=PAST,
            attendance=record,
            requested_check_in=time(8, 0),
            requested_check_out=time(16, 0),
            request_reason="wrong time",
        )
        req.status = "approved"
        req.save()
        record.refresh_from_db()
        self.assertEqual((record.check_in, record.check_out), (time(8, 0), time(16, 0)))


class AttendanceViewTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_submit_new_request_via_view(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("request_attendance"),
            {
                "date": "1404/01/02",
                "requested_check_in": "08:00",
                "requested_check_out": "16:00",
                "request_reason": "forgot",
            },
        )
        self.assertRedirects(response, reverse("user_requests"), fetch_redirect_response=False)
        req = AttendanceRequest.objects.get(user=self.user)
        self.assertEqual(req.status, "pending")
        self.assertEqual(req.date.strftime("%Y/%m/%d"), "1404/01/02")

    def test_request_with_missing_fields_creates_nothing(self):
        self.client.force_login(self.user)
        self.client.post(reverse("request_attendance"), {"date": "1404/01/02"})
        self.assertFalse(AttendanceRequest.objects.exists())

    def test_cannot_edit_other_users_record(self):
        other = make_user(phone="09120000089")
        record = AttendaceRecord.objects.create(user=other, date=PAST, check_in=time(8, 0))
        self.client.force_login(self.user)
        response = self.client.get(reverse("change_attendance", args=[record.id]))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_redirected_on_all_user_views(self):
        for name in ("attendance_list", "user_requests", "request_attendance", "report_attendance"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn("login", response["Location"], name)

    def test_report_forbidden_for_non_superuser(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("report_attendance")).status_code, 403)

    def test_report_downloads_for_superuser(self):
        admin = User.objects.create_superuser(
            phone_number="09120000088", password="x", first_name="A", last_name="B"
        )
        self.client.force_login(admin)
        response = self.client.get(reverse("report_attendance"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])


class DurationRegressionTests(TestCase):
    def setUp(self):
        self.user = make_user(phone="09120000060")

    def _d(self, date, check_in, check_out):
        return AttendaceRecord(user=self.user, date=date, check_in=check_in, check_out=check_out).duration()

    def test_friday_bonus_uses_record_date_not_today(self):
        friday = jdatetime.date(1404, 1, 8)
        self.assertEqual(friday.weekday(), 6)
        # "today" is a Saturday; the bonus must still apply to the Friday record.
        with mock.patch.object(jdatetime.date, "today", return_value=jdatetime.date(1404, 1, 9)):
            self.assertEqual(self._d(friday, time(8, 0), time(12, 0)).total_seconds(), 4 * 3600 * 1.2)

    def test_no_friday_bonus_when_today_is_friday_but_record_is_not(self):
        with mock.patch.object(jdatetime.date, "today", return_value=jdatetime.date(1404, 1, 8)):
            self.assertEqual(self._d(PAST, time(13, 0), time(17, 0)).total_seconds(), 4 * 3600)

    def test_check_in_between_1130_and_1200_is_not_none(self):
        with mock.patch.object(jdatetime.date, "today", return_value=jdatetime.date(1404, 1, 5)):
            result = self._d(PAST, time(11, 45), time(16, 0))
        self.assertEqual(result.total_seconds(), (4 * 3600 + 15 * 60) - 3600)

    def test_duration_does_not_mutate_check_out(self):
        record = AttendaceRecord(user=self.user, date=PAST, check_in=time(13, 0))
        record.duration()
        self.assertIsNone(record.check_out)


class AttendanceApiTests(TestCase):
    def setUp(self):
        self.user = make_user(phone="09120000061", rfid="1234567")
        self.url = reverse("attendance_api")
        self.body = {"rfid": "1234567", "time": "2025-03-22T08:00:00"}

    def _post(self, token=None, body=None):
        headers = {"HTTP_X_DEVICE_TOKEN": token} if token is not None else {}
        return self.client.post(
            self.url, data=body or self.body, content_type="application/json", **headers
        )

    @override_settings(ATTENDANCE_DEVICE_TOKEN="s3cret")
    def test_missing_or_wrong_token_rejected(self):
        self.assertEqual(self._post().status_code, 403)
        self.assertEqual(self._post("nope").status_code, 403)
        self.assertFalse(AttendaceRecord.objects.exists())

    @override_settings(ATTENDANCE_DEVICE_TOKEN="")
    def test_fails_closed_when_no_token_configured(self):
        self.assertEqual(self._post("").status_code, 503)
        self.assertEqual(self._post("anything").status_code, 503)
        self.assertFalse(AttendaceRecord.objects.exists())

    @override_settings(ATTENDANCE_DEVICE_TOKEN="s3cret")
    def test_valid_token_records_check_in(self):
        self.assertEqual(self._post("s3cret").json()["status"], "success")
        self.assertEqual(AttendaceRecord.objects.filter(user=self.user).count(), 1)

    @override_settings(ATTENDANCE_DEVICE_TOKEN="s3cret")
    def test_get_not_allowed_and_bad_body(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(self._post("s3cret", {"time": "2025-03-22T08:00:00"}).status_code, 400)
        self.assertEqual(self._post("s3cret", {"rfid": "1"}).status_code, 400)


class AttendanceViewRedirectTests(TestCase):
    def test_checkin_redirect_target_exists(self):
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        from attendance.views import attendance

        request = RequestFactory().post("/x", {"checkin": "08:00"})
        request.user = make_user(phone="09120000062")
        request.session = {}
        request._messages = FallbackStorage(request)
        response = attendance(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("attendance_list"))
