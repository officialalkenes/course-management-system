import pytest
from django.urls import reverse
from rest_framework import status
from faker import Faker
from apps.profiles.models import StudentProfile, TeacherProfile
from apps.abstract.choices import UserType

fake = Faker()


@pytest.mark.django_db
def test_teacher_onboarding_view(teacher_client, teacher_user):
    """Test teacher onboarding endpoint"""
    url = reverse("onboarding-list")  # Using the ViewSet's URL name
    data = {
        "user_type": UserType.TEACHER,
        "bio": fake.text(),
        "qualifications": "PhD, MSc",
        "specialization": "Computer Science",
        "years_of_experience": 8,
        "institution": "Tech University",
        "department": "Computer Science",
    }

    response = teacher_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK

    # Verify profile was updated
    teacher_user.refresh_from_db()
    profile = TeacherProfile.objects.get(user=teacher_user)
    assert profile.onboarding_completed is True
    assert profile.specialization == "Computer Science"


@pytest.mark.django_db
def test_student_onboarding_view(student_client, student_user):
    """Test student onboarding endpoint"""
    url = reverse("onboarding-list")  # Using the ViewSet's URL name
    data = {
        "user_type": UserType.STUDENT,
        "student_id": "STU2023001",
        "date_of_birth": "2005-05-15",
        "grade_level": "10",
        "parent_guardian_name": fake.name(),
        "parent_guardian_contact": "+1234567890",
        "school_name": "High School",
        "academic_interests": "Programming, Robotics",
    }

    response = student_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK

    # Verify profile was updated
    student_user.refresh_from_db()
    profile = StudentProfile.objects.get(user=student_user)
    assert profile.onboarding_completed is True
    assert profile.student_id == "STU2023001"


@pytest.mark.django_db
def test_onboarding_wrong_user_type(teacher_client, student_client):
    """Test that users can't complete onboarding for wrong role"""
    url = reverse("onboarding-list")

    # Teacher trying to submit student data
    student_data = {"user_type": UserType.STUDENT, "student_id": "STU2023001"}
    response = teacher_client.post(url, student_data, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Student trying to submit teacher data
    teacher_data = {"user_type": UserType.TEACHER, "qualifications": "PhD"}
    response = student_client.post(url, teacher_data, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_onboarding_required_fields(teacher_client, teacher_user):
    """Test that required fields are enforced"""
    url = reverse("onboarding-list")
    incomplete_data = {
        "user_type": UserType.TEACHER,
        "qualifications": "PhD",
        "specialization": "Physics",
        # Missing bio (required)
    }

    response = teacher_client.post(url, incomplete_data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "bio" in response.data
