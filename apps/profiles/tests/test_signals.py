# tests/test_signals.py
import pytest
from django.contrib.auth import get_user_model
from apps.abstract.choices import UserType

User = get_user_model()


@pytest.mark.django_db
def test_teacher_profile_creation_signal():
    """Test that teacher profile is created automatically"""
    user = User.objects.create_user(
        email="teacher_signal@test.com",
        password="testpass",
        first_name="Signal",
        last_name="Teacher",
        user_type=UserType.TEACHER,
    )

    assert hasattr(user, "teacher_profile")
    assert not hasattr(user, "student_profile")


@pytest.mark.django_db
def test_student_profile_creation_signal():
    """Test that student profile is created automatically"""
    user = User.objects.create_user(
        email="student_signal@test.com",
        password="testpass",
        first_name="Signal",
        last_name="Student",
        user_type=UserType.STUDENT,
    )

    assert hasattr(user, "student_profile")
    assert not hasattr(user, "teacher_profile")
