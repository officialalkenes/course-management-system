import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from faker import Faker

from apps.courses.models import Course, Assignment, Enrollment, Submission
from apps.profiles.models import TeacherProfile, StudentProfile
from django.contrib.auth import get_user_model

User = get_user_model()
fake = Faker()

# -----------------------------
# Base client/auth fixtures
# -----------------------------


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def teacher_user(db):
    user = User.objects.create_user(
        email=fake.email(),
        password="TeacherPass123!",
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        user_type="TEACHER",
        is_active=True,
    )
    TeacherProfile.objects.get_or_create(user=user)
    return user


@pytest.fixture
def student_user(db):
    user = User.objects.create_user(
        email=fake.email(),
        password="StudentPass123!",
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        user_type="STUDENT",
        is_active=True,
    )
    StudentProfile.objects.get_or_create(user=user)
    return user


@pytest.fixture
def teacher_client(api_client, teacher_user):
    token = RefreshToken.for_user(teacher_user).access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def student_client(api_client, student_user):
    token = RefreshToken.for_user(student_user).access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


# -----------------------------
# Core app data fixtures
# -----------------------------


@pytest.fixture
def course(db, teacher_user):
    teacher_profile = teacher_user.teacher_profile
    return Course.objects.create(
        title="Intro to AI",
        code=f"AI{fake.random_int(100, 999)}",
        description="Learn the basics of AI.",
        teacher=teacher_profile,
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timezone.timedelta(days=90),
        max_students=50,
        enrollment_open=True,
        is_active=True,
    )


@pytest.fixture
def enrolled_student(course, student_user):
    enrollment = Enrollment.objects.create(
        student=student_user.student_profile,
        course=course,
        is_active=True,
    )
    return enrollment.student.user  # return user object


@pytest.fixture
def assignment(course):
    return Assignment.objects.create(
        course=course,
        title="Essay on Neural Networks",
        description="Submit a 2-page essay.",
        due_date=timezone.now() + timezone.timedelta(days=7),
        max_points=100,
        allow_late_submissions=True,
        late_submission_deadline=timezone.now() + timezone.timedelta(days=10),
        attachment_required=False,
    )


@pytest.fixture
def submission(assignment, enrolled_student):
    return Submission.objects.create(
        assignment=assignment,
        student=enrolled_student.student_profile,
        content="This is my essay on neural networks.",
        is_reviewed=False,
    )
