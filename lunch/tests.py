from datetime import time
from unittest import mock

import jdatetime
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse

from lunch.models import Lunch

User = get_user_model()


def make_user(phone="09120000099", password="pass12345", **kw):
    kw.setdefault("first_name", "Test")
    kw.setdefault("last_name", "User")
    return User.objects.create_user(phone_number=phone, password=password, **kw)


class CustomUserModelTests(TestCase):
    def test_create_user_hashes_password(self):
        user = make_user()
        self.assertTrue(user.check_password("pass12345"))
        self.assertNotEqual(user.password, "pass12345")
        self.assertFalse(user.is_staff)

    def test_create_user_requires_phone_number(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(phone_number="", password="x")

    def test_create_superuser_flags(self):
        admin = User.objects.create_superuser(
            phone_number="09120000098", password="x", first_name="A", last_name="B"
        )
        self.assertTrue(admin.is_staff and admin.is_superuser)

    def test_phone_number_is_unique(self):
        make_user(phone="09120000097")
        with self.assertRaises(IntegrityError):
            make_user(phone="09120000097")

    def test_str_is_full_name(self):
        self.assertEqual(str(make_user(first_name="Ada", last_name="Lovelace")), "Ada Lovelace")


class LunchModelTests(TestCase):
    def test_is_lunch_requested_today(self):
        user = make_user()
        self.assertFalse(Lunch.is_lunch_requested_today(user))
        Lunch.objects.create(user=user, date=jdatetime.date.today(), is_lunch_requested=True)
        self.assertTrue(Lunch.is_lunch_requested_today(user))


class LunchReservationFlowTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.url = reverse("reserve_lunch")

    def _offered_dates(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        dates = response.context["dates"]
        self.assertTrue(dates)
        return [d[1] for d in dates]

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_reserve_and_cancel(self):
        self.client.force_login(self.user)
        offered = self._offered_dates()
        self.client.post(self.url, {"selected_dates": offered[:2]})
        self.assertEqual(Lunch.objects.filter(user=self.user).count(), 2)
        # Submitting only one date cancels the other.
        self.client.post(self.url, {"selected_dates": offered[:1]})
        self.assertEqual(Lunch.objects.filter(user=self.user).count(), 1)
        # Submitting nothing cancels everything.
        self.client.post(self.url, {})
        self.assertEqual(Lunch.objects.filter(user=self.user).count(), 0)

    def test_reservations_are_per_user(self):
        other = make_user(phone="09120000096")
        self.client.force_login(self.user)
        offered = self._offered_dates()
        Lunch.objects.create(
            user=other,
            date=jdatetime.datetime.strptime(offered[0], "%Y/%m/%d").date(),
            is_lunch_requested=True,
        )
        self.client.post(self.url, {})  # cancels only own reservations
        self.assertEqual(Lunch.objects.filter(user=other).count(), 1)


@override_settings(
    LUNCH_EXTRA_NAMES=["Extra One"],
    LUNCH_EXTRA_NAMES_NOT_SATURDAY=[],
    LUNCH_EXTRA_NAMES_SUN_TUE=[],
    SMS_LUNCH_RECIPIENTS=["09120000000"],
)
class LunchSmsListTests(TestCase):
    def test_list_uses_db_names_and_configured_extras(self):
        user = make_user(first_name="Ada", last_name="Lovelace")
        admin = make_user(phone="09120000081", is_staff=True)
        self.client.force_login(admin)
        today = jdatetime.date(1404, 1, 1)  # a fixed non Wed/Thu day is chosen below
        while today.strftime("%A") in ("چهارشنبه", "پنج‌شنبه"):
            today += jdatetime.timedelta(days=1)
        tomorrow = today + jdatetime.timedelta(days=1)
        Lunch.objects.create(user=user, date=tomorrow, is_lunch_requested=True)
        with mock.patch.object(jdatetime.date, "today", return_value=today), mock.patch(
            "lunch.tasks.send_sms"
        ) as send_sms:
            response = self.client.post(reverse("send_lunch_reservations_sms"))
        self.assertEqual(response.status_code, 200)
        send_sms.assert_called_once()
        names = send_sms.call_args[0][1]["names"]
        self.assertIn("1.Ada Lovelace", names)
        self.assertIn("2. Extra One", names)

    @override_settings(LUNCH_EXTRA_NAMES=[])
    def test_no_hardcoded_names_by_default(self):
        from django.conf import settings

        self.assertEqual(settings.LUNCH_EXTRA_NAMES_NOT_SATURDAY, [])
        self.assertEqual(settings.LUNCH_EXTRA_NAMES, [])


class OtpLoginFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user(phone="09120000095")
        self.login_url = reverse("login")

    def test_password_login_succeeds(self):
        response = self.client.post(
            self.login_url, {"phone_number": "09120000095", "password": "pass12345"}
        )
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertIn("_auth_user_id", self.client.session)

    def test_wrong_password_sends_otp_via_mocked_client(self):
        with mock.patch("lunch.views.send_otp") as send_otp:
            response = self.client.post(
                self.login_url, {"phone_number": "09120000095", "password": "wrong"}
            )
        self.assertRedirects(
            response,
            reverse("otp_verify", kwargs={"phone_number": "09120000095"}),
            fetch_redirect_response=False,
        )
        send_otp.assert_called_once()
        self.assertEqual(send_otp.call_args[0][0], "09120000095")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_unknown_phone_does_not_send_otp(self):
        with mock.patch("lunch.views.send_otp") as send_otp:
            self.client.post(self.login_url, {"phone_number": "09129999999", "password": "x"})
        send_otp.assert_not_called()

    def test_otp_verify_logs_in_and_code_is_single_use(self):
        cache.set("otp_09120000095", "123456", timeout=300)
        url = reverse("otp_verify", kwargs={"phone_number": "09120000095"})
        self.client.post(url, {"otp": "123456"})
        self.assertIn("_auth_user_id", self.client.session)
        self.client.logout()
        self.client.post(url, {"otp": "123456"})  # reuse must fail
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_wrong_otp_rejected(self):
        cache.set("otp_09120000095", "123456", timeout=300)
        url = reverse("otp_verify", kwargs={"phone_number": "09120000095"})
        self.client.post(url, {"otp": "000000"})
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_otp_none_string_cannot_bypass_when_no_code_stored(self):
        # Regression: str(None) == "None" used to authenticate anyone.
        url = reverse("otp_verify", kwargs={"phone_number": "09120000095"})
        self.client.post(url, {"otp": "None"})
        self.assertNotIn("_auth_user_id", self.client.session)


class LunchPermissionTests(TestCase):
    def test_home_requires_login(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)

    def test_profile_requires_login(self):
        response = self.client.get(reverse("profile_info"))
        self.assertEqual(response.status_code, 302)

    def test_working_form_anonymous_redirected(self):
        response = self.client.get(reverse("working_form"))
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)


class LunchSmsPermissionTests(TestCase):
    url_name = "send_lunch_reservations_sms"

    def test_anonymous_redirected_and_no_sms(self):
        with mock.patch("lunch.tasks.send_sms") as send_sms:
            response = self.client.post(reverse(self.url_name))
        self.assertEqual(response.status_code, 302)
        send_sms.assert_not_called()

    def test_regular_user_forbidden(self):
        self.client.force_login(make_user(phone="09120000080"))
        with mock.patch("lunch.tasks.send_sms") as send_sms:
            response = self.client.post(reverse(self.url_name))
        self.assertEqual(response.status_code, 403)
        send_sms.assert_not_called()

    def test_get_not_allowed_for_staff(self):
        self.client.force_login(make_user(phone="09120000079", is_staff=True))
        self.assertEqual(self.client.get(reverse(self.url_name)).status_code, 405)

    def test_task_sends_dict_pattern(self):
        from lunch import tasks

        user = make_user(phone="09120000078")
        today = jdatetime.date(1404, 1, 2)  # Saturday
        Lunch.objects.create(user=user, date=today + jdatetime.timedelta(days=1))
        with mock.patch.object(jdatetime.date, "today", return_value=today), mock.patch(
            "lunch.tasks.send_sms"
        ) as send_sms:
            tasks.send_lunch_reservation_sms()
        self.assertIsInstance(send_sms.call_args[0][1], dict)

    def test_task_skips_wednesday(self):
        from lunch import tasks

        wednesday = jdatetime.date(1404, 1, 6)
        self.assertEqual(wednesday.strftime("%A"), "چهارشنبه")
        with mock.patch.object(jdatetime.date, "today", return_value=wednesday), mock.patch(
            "lunch.tasks.send_sms"
        ) as send_sms:
            tasks.send_lunch_reservation_sms()
        send_sms.assert_not_called()


class OtpHardeningTests(TestCase):
    phone = "09120000077"

    def setUp(self):
        cache.clear()
        make_user(phone=self.phone)

    def _fail_login(self):
        return self.client.post(
            reverse("login"), {"phone_number": self.phone, "password": "wrong"}
        )

    def test_code_is_six_digits_and_not_printed(self):
        with mock.patch("lunch.views.send_otp") as send_otp, mock.patch("builtins.print") as pr:
            self._fail_login()
        code = send_otp.call_args[0][1]
        self.assertRegex(code, r"^\d{6}$")
        for call in pr.call_args_list:
            self.assertNotIn(code, " ".join(map(str, call.args)))

    def test_cooldown_blocks_second_sms(self):
        with mock.patch("lunch.views.send_otp") as send_otp:
            self._fail_login()
            self._fail_login()
        self.assertEqual(send_otp.call_count, 1)

    def test_five_wrong_attempts_invalidate_code(self):
        cache.set(f"otp_{self.phone}", "123456", timeout=300)
        url = reverse("otp_verify", kwargs={"phone_number": self.phone})
        for _ in range(5):
            self.client.post(url, {"otp": "000000"})
        self.client.post(url, {"otp": "123456"})  # correct, but code is burned
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_correct_code_within_attempt_cap_works(self):
        cache.set(f"otp_{self.phone}", "123456", timeout=300)
        url = reverse("otp_verify", kwargs={"phone_number": self.phone})
        for _ in range(4):
            self.client.post(url, {"otp": "000000"})
        self.client.post(url, {"otp": "123456"})
        self.assertIn("_auth_user_id", self.client.session)


class LunchMetaTests(TestCase):
    def test_unique_user_date_enforced(self):
        user = make_user(phone="09120000076")
        date = jdatetime.date(1404, 1, 2)
        Lunch.objects.create(user=user, date=date)
        with self.assertRaises(IntegrityError):
            Lunch.objects.create(user=user, date=date)
        self.assertEqual(Lunch._meta.verbose_name, "رزرو")
