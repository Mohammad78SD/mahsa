from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


def make_user(phone, **kw):
    return User.objects.create_user(
        phone_number=phone, password="x", first_name="T", last_name="U", **kw
    )


class MessagingPermissionTests(TestCase):
    def test_send_and_file_views_require_login(self):
        for name in ("send_file", "file_list"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)

    def test_non_file_user_forbidden(self):
        self.client.force_login(make_user("09120000070"))
        for name in ("send_file", "file_list"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)

    def test_file_user_allowed(self):
        self.client.force_login(make_user("09120000071", is_file=True))
        self.assertEqual(self.client.get(reverse("file_list")).status_code, 200)

    def test_vapid_key_endpoint_returns_configured_public_key(self):
        response = self.client.get(reverse("get_vapid_key"))
        self.assertEqual(response.json(), {"publicKey": "dummy-public-key"})
