from collections.abc import Mapping

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from Records.models import Department, Student


def _credentials(data):
    if not isinstance(data, Mapping):
        return None, None, Response(
            {"detail": "A JSON object with username and password is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not username or not isinstance(password, str) or not password:
        return None, None, Response(
            {"detail": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return username, password, None


class Login(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        username, password, error = _credentials(request.data)
        if error is not None:
            return error

        user = authenticate(request=request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key}, status=status.HTTP_200_OK)


class Create(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        username, password, error = _credentials(request.data)
        if error is not None:
            return error

        profile_data_supplied = any(field in request.data for field in ("full_name", "depts", "age"))
        student_profile = None
        if profile_data_supplied:
            full_name = request.data.get("full_name")
            department_id = request.data.get("depts")
            age = request.data.get("age", 15)
            if not isinstance(full_name, str) or not full_name.strip() or len(full_name.strip()) > 20:
                return Response(
                    {"full_name": ["Enter a name of at most 20 characters."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                age = int(age)
                if age < 1:
                    raise ValueError
            except (TypeError, ValueError):
                return Response(
                    {"age": ["Enter a valid age greater than zero."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                department = Department.objects.get(pk=department_id)
            except (TypeError, ValueError, Department.DoesNotExist):
                return Response(
                    {"depts": ["Choose a valid department."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            return Response(
                {"username": ["A user with that username already exists."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User(username=username)
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            return Response(
                {"password": list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password)
            if profile_data_supplied:
                student_profile = Student.objects.create(
                    user=user,
                    full_name=full_name.strip(),
                    age=age,
                    depts=department,
                )
            token = Token.objects.create(user=user)
        response_data = {
            "id": user.pk,
            "username": user.get_username(),
            "token": token.key,
        }
        if student_profile is not None:
            response_data["profile_id"] = student_profile.pk
        return Response(response_data, status=status.HTTP_201_CREATED)


class Logout(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUser(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "is_staff": request.user.is_staff,
            "is_superuser": request.user.is_superuser,
        })