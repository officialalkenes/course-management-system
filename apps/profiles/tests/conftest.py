from faker import Faker
import pytest
from django.contrib.auth import get_user_model
from apps.abstract.choices import UserType
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient

from apps.profiles.models import StudentProfile, TeacherProfile

fake = Faker()
User = get_user_model()


# Add this fixture
@pytest.fixture
def api_client():
    """Regular unauthenticated APIClient"""
    return APIClient()


@pytest.fixture
def teacher_user(db):
    """A user with teacher role and profile"""
    user = User.objects.create_user(
        email=fake.email(),
        password="TeacherPass123!",
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        user_type=UserType.TEACHER,
        is_active=True,
    )
    TeacherProfile.objects.get_or_create(user=user)
    return user


@pytest.fixture
def student_user(db):
    """A user with student role and profile"""
    user = User.objects.create_user(
        email=fake.email(),
        password="StudentPass123!",
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        user_type=UserType.STUDENT,
        is_active=True,
    )
    StudentProfile.objects.get_or_create(user=user)
    return user


@pytest.fixture
def teacher_client(api_client, teacher_user):
    """APIClient authenticated as teacher"""
    token = RefreshToken.for_user(teacher_user).access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def student_client(api_client, student_user):
    """APIClient authenticated as student"""
    token = RefreshToken.for_user(student_user).access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client
