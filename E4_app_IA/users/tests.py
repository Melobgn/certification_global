from django.test import TestCase
from django.contrib.auth import get_user_model
from users.admin import CustomUserAdmin

User = get_user_model()

class CustomUserModelTest(TestCase):
    def test_user_has_role_field(self):
        user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="test@example.com",
            role="annotateur"
        )
        self.assertEqual(user.role, "annotateur")

class CustomUserAdminTest(TestCase):
    def test_role_in_list_display(self):
        self.assertIn("role", CustomUserAdmin.list_display)

    def test_role_in_fieldsets(self):
        fieldset_fields = [
            field
            for _, opts in CustomUserAdmin.fieldsets
            for field in opts.get("fields", [])
        ]
        self.assertIn("role", fieldset_fields)

    def test_role_in_add_fieldsets(self):
        add_fieldset_fields = [
            field
            for _, opts in CustomUserAdmin.add_fieldsets
            for field in opts.get("fields", [])
        ]
        self.assertIn("role", add_fieldset_fields)