# tests/test_serializers.py
import pytest
from faker import Faker
from apps.profiles.serializers import (
    TeacherOnboardingSerializer,
    StudentOnboardingSerializer,
)

fake = Faker()


@pytest.mark.django_db
def test_teacher_onboarding_serializer(teacher_user):
    """Test teacher onboarding serializer validation"""
    profile = teacher_user.teacher_profile
    valid_data = {
        "bio": fake.text(),
        "qualifications": "PhD, MSc",
        "specialization": "Mathematics",
        "years_of_experience": 5,
        "institution": "University of Test",
        "department": "Math Department",
    }

    serializer = TeacherOnboardingSerializer(instance=profile, data=valid_data)
    assert serializer.is_valid(), serializer.errors

    # Test missing required fields
    invalid_data = valid_data.copy()
    invalid_data.pop("bio")
    serializer = TeacherOnboardingSerializer(instance=profile, data=invalid_data)
    assert not serializer.is_valid()
    assert "bio" in serializer.errors


@pytest.mark.django_db
def test_student_onboarding_serializer(student_user):
    """Test student onboarding serializer validation"""
    profile = student_user.student_profile
    valid_data = {
        "student_id": "STU2023001",
        "date_of_birth": "2000-01-01",
        "grade_level": "11",
        "parent_guardian_name": fake.name(),
        "parent_guardian_contact": "+1234567890",
        "school_name": "Test High School",
        "academic_interests": "Math, Science",
    }

    serializer = StudentOnboardingSerializer(instance=profile, data=valid_data)
    assert serializer.is_valid(), serializer.errors

    # Test invalid phone number
    invalid_data = valid_data.copy()
    invalid_data["parent_guardian_contact"] = "invalid"
    serializer = StudentOnboardingSerializer(instance=profile, data=invalid_data)
    assert not serializer.is_valid()
    assert "parent_guardian_contact" in serializer.errors
