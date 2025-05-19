import pytest
from django.utils import timezone
from apps.courses.models import Course, Enrollment, Submission
from apps.profiles.models import StudentProfile
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_course_str(course):
    """Test string representation of Course"""
    assert str(course) == f"{course.code}: {course.title}"


@pytest.mark.django_db
def test_course_date_validation():
    """Test that Course clean method raises on invalid dates"""
    from django.core.exceptions import ValidationError
    from apps.profiles.models import TeacherProfile

    teacher = TeacherProfile.objects.first()
    course = Course(
        title="Bad Dates",
        code="BAD001",
        description="Test course",
        teacher=teacher,
        start_date=timezone.now().date(),
        end_date=timezone.now().date() - timezone.timedelta(days=1),
    )
    with pytest.raises(ValidationError):
        course.clean()


@pytest.mark.django_db
def test_assignment_str(assignment):
    """Test string representation of Assignment"""
    expected = f"{assignment.course.code} - {assignment.title}"
    assert str(assignment) == expected


@pytest.mark.django_db
def test_assignment_can_accept_submission(assignment):
    """Test logic for accepting submission"""
    # Before due date
    assert assignment.can_accept_submission is True

    # After late deadline
    assignment.due_date = timezone.now() - timezone.timedelta(days=10)
    assignment.late_submission_deadline = timezone.now() - timezone.timedelta(days=1)
    assignment.save()
    assert assignment.can_accept_submission is False


@pytest.mark.django_db
def test_enrollment_str(enrolled_student, course):
    """Test string representation of Enrollment"""
    enrollment = course.enrollments.get(student=enrolled_student.student_profile)
    assert str(enrollment) == f"{enrolled_student.email} in {course.code}"


@pytest.mark.django_db
def test_enrollment_clean_capacity(course, student_user):
    """Test enrollment clean method for capacity and status"""
    from django.core.exceptions import ValidationError

    course.max_students = 1
    course.save()

    # First enrollment should succeed
    Enrollment.objects.create(
        student=student_user.student_profile, course=course, is_active=True
    )

    # Create a different student
    new_student = User.objects.create_user(
        email="another@example.com", password="testpass123", user_type="STUDENT"
    )
    StudentProfile.objects.create(user=new_student)

    # Second enrollment should fail
    with pytest.raises(ValidationError):
        Enrollment(
            student=new_student.student_profile, course=course, is_active=True
        ).full_clean()  # Must call full_clean() explicitly


@pytest.mark.django_db
def test_submission_str(submission):
    """Test string representation of Submission"""
    expected = f"{submission.student.user.email}'s submission for {submission.assignment.title}"
    assert str(submission) == expected


@pytest.mark.django_db
def test_submission_late_flag(assignment, enrolled_student):
    """Test that `is_late` flag is set correctly on submission save"""
    assignment.due_date = timezone.now() - timezone.timedelta(days=1)
    assignment.save()

    submission = Submission.objects.create(
        assignment=assignment,
        student=enrolled_student.student_profile,
        content="Late work",
    )
    assert submission.is_late is True
