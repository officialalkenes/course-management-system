import pytest
from faker import Faker

fake = Faker()


@pytest.mark.django_db
def test_teacher_profile_creation(teacher_user):
    """Test that teacher profile is created correctly"""
    profile = teacher_user.teacher_profile
    assert profile is not None
    assert profile.onboarding_completed is False
    assert str(profile) == f"Teacher Profile for {teacher_user.email}"


@pytest.mark.django_db
def test_student_profile_creation(student_user):
    """Test that student profile is created correctly"""
    profile = student_user.student_profile
    assert profile is not None
    assert profile.onboarding_completed is False
    assert str(profile) == f"Student Profile for {student_user.email}"


@pytest.mark.django_db
def test_teacher_profile_completion(teacher_user):
    """Test marking teacher profile as complete"""
    profile = teacher_user.teacher_profile
    profile.bio = fake.text()
    profile.qualifications = "PhD in Computer Science"
    profile.specialization = "Computer Science"
    profile.years_of_experience = 10
    profile.onboarding_completed = True
    profile.save()

    assert profile.onboarding_completed is True


@pytest.mark.django_db
def test_student_profile_completion(student_user):
    """Test marking student profile as complete"""
    profile = student_user.student_profile
    profile.student_id = "STU12345"
    profile.date_of_birth = fake.date_of_birth()
    profile.grade_level = "12"
    profile.onboarding_completed = True
    profile.save()

    assert profile.onboarding_completed is True
