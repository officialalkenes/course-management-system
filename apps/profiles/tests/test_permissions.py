# tests/test_permissions.py
import pytest
from apps.profiles.permissions import IsOnboardingComplete
from apps.profiles.models import TeacherProfile, StudentProfile


@pytest.mark.django_db
def test_is_onboarding_complete_permission(teacher_user, student_user):
    """Test the IsOnboardingComplete permission class"""
    permission = IsOnboardingComplete()

    # Test with incomplete profiles
    request = type("Request", (), {"user": teacher_user})
    assert not permission.has_permission(request, None)

    request = type("Request", (), {"user": student_user})
    assert not permission.has_permission(request, None)

    # Complete the profiles
    TeacherProfile.objects.filter(user=teacher_user).update(onboarding_completed=True)
    StudentProfile.objects.filter(user=student_user).update(onboarding_completed=True)

    # Refresh from db
    teacher_user.refresh_from_db()
    student_user.refresh_from_db()

    # Test with complete profiles
    request = type("Request", (), {"user": teacher_user})
    assert permission.has_permission(request, None)

    request = type("Request", (), {"user": student_user})
    assert permission.has_permission(request, None)
