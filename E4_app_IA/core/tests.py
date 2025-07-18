from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class CoreViewsTest(TestCase):
    databases = {"default", "weapon_data"}

    def setUp(self):
        self.client = Client()
        self.user_analyst = User.objects.create_user(
            username="test_analyst", password="testpass", role="analyst"
        )
        self.user_admin = User.objects.create_user(
            username="test_admin", password="testpass", role="admin"
        )

    def test_home_page_status_code(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirection vers login

    def test_dashboard_authenticated_access(self):
        self.client.login(username="test_analyst", password="testpass")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/dashboard.html")

    def test_annotation_dashboard_authenticated_access(self):
        self.client.login(username="test_analyst", password="testpass")
        response = self.client.get(reverse("annotation_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/annotation_dashboard.html")

    def test_historique_annotations_authenticated_access(self):
        self.client.login(username="test_analyst", password="testpass")
        response = self.client.get(reverse("historique_annotations"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/historique_annotations.html")

    # def test_admin_dashboard_authenticated_access(self):
    #     self.client.login(username="test_admin", password="testpass")
    #     response = self.client.get(reverse("admin_dashboard"))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, "core/admin_dashboard.html")
