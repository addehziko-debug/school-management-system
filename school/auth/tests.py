from django.contrib.auth import get_user_model
from Records.models import Department, Student
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class LoginTests(APITestCase):
    def setUp(self):
        self.username = "student"
        self.password = "correct-password"
        self.user = get_user_model().objects.create_user(
            username=self.username,
            password=self.password,
        )

    def test_valid_credentials_return_a_token(self):
        response = self.client.post(
            "/auth/login/",
            {"username": self.username, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["token"], Token.objects.get(user=self.user).key)

    def test_invalid_credentials_are_rejected(self):
        response = self.client.post(
            "/auth/login/",
            {"username": self.username, "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_missing_credentials_are_rejected(self):
        response = self.client.post("/auth/login/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_object_payload_is_rejected(self):
        response = self.client.post("/auth/login/", [], format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CreateLogoutTests(APITestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Science")

    def test_create_user_without_profile_fields_remains_supported(self):
        response = self.client.post(
            "/auth/create/",
            {"username": "basic-user", "password": "a-strong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(username="basic-user")
        self.assertFalse(Student.objects.filter(user=user).exists())
        self.assertNotIn("profile_id", response.data)

    def test_create_user_returns_user_details_and_token(self):
        response = self.client.post(
            "/auth/create/",
            {
                "username": "new-student",
                "password": "a-strong-password",
                "full_name": "New Student",
                "depts": self.department.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(username="new-student")
        student = Student.objects.get(user=user)
        self.assertEqual(response.data["id"], user.pk)
        self.assertEqual(response.data["profile_id"], student.pk)
        self.assertEqual(student.depts, self.department)
        self.assertEqual(response.data["token"], Token.objects.get(user=user).key)
        self.assertNotIn("password", response.data)

    def test_create_rejects_duplicate_username(self):
        get_user_model().objects.create_user(
            username="existing-student",
            password="a-strong-password",
        )

        response = self.client.post(
            "/auth/create/",
            {
                "username": "existing-student",
                "password": "another-strong-password",
                "full_name": "Existing Student",
                "depts": self.department.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_weak_password(self):
        response = self.client.post(
            "/auth/create/",
            {
                "username": "new-student",
                "password": "123",
                "full_name": "New Student",
                "depts": self.department.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(get_user_model().objects.filter(username="new-student").exists())

    def test_logout_requires_a_token(self):
        response = self.client.post("/auth/logout/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_deletes_the_authenticating_token(self):
        user = get_user_model().objects.create_user(
            username="student",
            password="a-strong-password",
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.post("/auth/logout/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(user=user).exists())
