import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.courses.models import Course, Enrollment, Assignment, Submission
from apps.profiles.models import StudentProfile

from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_course_creation():
    course = Course.objects.create(
        title="Introduction to Testing",
        code="TEST101",
        description="A foundational course on software testing.",
    )
    assert course.title == "Introduction to Testing"
    assert course.code == "TEST101"
    assert Course.objects.count() == 1


@pytest.mark.django_db
def test_course_str(course):
    assert str(course) == f"{course.code}: {course.title}"


@pytest.mark.django_db
def test_course_enrollment(course, student_user):
    student_profile, created = StudentProfile.objects.get_or_create(user=student_user)

    enrollment = Enrollment.objects.create(student=student_profile, course=course)
    assert enrollment.student == student_profile
    assert enrollment.course == course
    assert Enrollment.objects.count() == 1
    assert course.enrolled_students.count() == 1
    assert course.enrolled_students.first() == student_profile


@pytest.mark.django_db
def test_course_enrollment_capacity(course, student_user):
    course.max_students = 1
    course.save()

    StudentProfile.objects.get_or_create(user=student_user)

    Enrollment.objects.create(student=student_user.student_profile, course=course)

    new_student = User.objects.create_user(
        email="another@example.com",
        password="StudentPass123!",
        user_type="STUDENT",
        is_active=True,
    )
    new_student_profile, created = StudentProfile.objects.get_or_create(
        user=new_student
    )

    with pytest.raises(ValidationError):
        Enrollment.objects.create(student=new_student_profile, course=course)


@pytest.mark.django_db
def test_enrollment_str(enrolled_student, course):
    student_profile, created = StudentProfile.objects.get_or_create(
        user=enrolled_student
    )

    enrollment = Enrollment.objects.create(student=student_profile, course=course)
    assert str(enrollment) == f"{enrolled_student.email} enrolled in {course.code}"


@pytest.mark.django_db
def test_assignment_creation(course):
    assignment = Assignment.objects.create(
        course=course,
        title="Essay on Neural Networks",
        description="Write a 1000-word essay.",
        due_date=timezone.now() + timezone.timedelta(days=7),
        max_score=100,
    )
    assert assignment.course == course
    assert assignment.title == "Essay on Neural Networks"
    assert Assignment.objects.count() == 1


@pytest.mark.django_db
def test_assignment_str(assignment):
    assert str(assignment) == f"{assignment.course.code} - {assignment.title}"


@pytest.mark.django_db
def test_assignment_due_date_validation(course):
    past_date = timezone.now() - timezone.timedelta(days=1)

    assignment = Assignment(
        course=course,
        title="Late Assignment",
        description="Should fail validation.",
        due_date=past_date,
        max_score=50,
    )

    with pytest.raises(ValidationError):
        assignment.full_clean()


@pytest.mark.django_db
def test_submission_creation(assignment, enrolled_student):
    student_profile, created = StudentProfile.objects.get_or_create(
        user=enrolled_student
    )

    submission = Submission.objects.create(
        assignment=assignment,
        student=student_profile,
        content="This is my essay content.",
    )
    assert submission.assignment == assignment
    assert submission.student == student_profile
    assert submission.content == "This is my essay content."
    assert Submission.objects.count() == 1


@pytest.mark.django_db
def test_submission_str(submission):
    assert (
        str(submission)
        == f"Submission for {submission.assignment.title} by {submission.student.user.email}"
    )


@pytest.mark.django_db
def test_submission_grade_and_completion_update(assignment, enrolled_student):
    student_profile, created = StudentProfile.objects.get_or_create(
        user=enrolled_student
    )

    enrollment, created = Enrollment.objects.get_or_create(
        student=student_profile, course=assignment.course
    )

    submission = Submission.objects.create(
        assignment=assignment,
        student=student_profile,
        content="Submission content.",
    )

    submission.grade = 85
    submission.is_reviewed = True
    submission.save()

    enrollment.refresh_from_db()

    assignment2 = Assignment.objects.create(
        course=assignment.course,
        title="Second Essay",
        description="Another essay.",
        due_date=timezone.now() + timezone.timedelta(days=14),
        max_score=100,
    )

    submission2 = Submission.objects.create(
        assignment=assignment2,
        student=student_profile,
        content="Second submission content.",
    )

    submission2.grade = 90
    submission2.is_reviewed = True
    submission2.save()

    enrollment.refresh_from_db()

    assert enrollment.completion == 1.0


@pytest.mark.django_db
def test_enrollment_completion_calculation(assignment, enrolled_student):
    student_profile, created = StudentProfile.objects.get_or_create(
        user=enrolled_student
    )

    enrollment, created = Enrollment.objects.get_or_create(
        student=student_profile, course=assignment.course
    )

    enrollment.refresh_from_db()
    assert enrollment.completion == 0

    submission = Submission.objects.create(
        assignment=assignment,
        student=student_profile,
        content="Submission content.",
    )

    submission.grade = 75
    submission.is_reviewed = True
    submission.save()

    enrollment.refresh_from_db()

    assert enrollment.completion == 1.0

    assignment2 = Assignment.objects.create(
        course=assignment.course,
        title="Another Assignment",
        description="Desc",
        due_date=timezone.now() + timezone.timedelta(days=10),
        max_score=50,
    )

    enrollment.refresh_from_db()
    assert enrollment.completion == 0.5

    submission2 = Submission.objects.create(
        assignment=assignment2,
        student=student_profile,
        content="Content 2",
    )
    submission2.grade = 40
    submission2.is_reviewed = True
    submission2.save()

    enrollment.refresh_from_db()
    assert enrollment.completion == 1.0


@pytest.mark.django_db
def test_submission_late_detection(assignment, enrolled_student):
    student_profile, created = StudentProfile.objects.get_or_create(
        user=enrolled_student
    )

    assignment.due_date = timezone.now() - timezone.timedelta(days=1)
    assignment.save()

    submission = Submission(
        assignment=assignment,
        student=student_profile,
        content="Late content",
    )
    submission.save()

    assert submission.submitted_at > assignment.due_date


@pytest.mark.django_db
def test_multiple_submissions(assignment, enrolled_student):
    student_profile, created = StudentProfile.objects.get_or_create(
        user=enrolled_student
    )

    enrollment, created = Enrollment.objects.get_or_create(
        student=student_profile, course=assignment.course
    )

    submission1 = Submission.objects.create(  # noqa
        assignment=assignment,
        student=student_profile,
        content="First attempt",
        submitted_at=timezone.now() - timezone.timedelta(hours=2),
    )

    submission2 = Submission.objects.create(  # noqa
        assignment=assignment,
        student=student_profile,
        content="Second attempt",
        submitted_at=timezone.now() - timezone.timedelta(hours=1),
    )

    submission3 = Submission.objects.create(  # noqa
        assignment=assignment,
        student=student_profile,
        content="Third attempt",
        submitted_at=timezone.now(),
    )
    print

    assert (
        Submission.objects.filter(
            assignment=assignment, student=student_profile
        ).count()
        == 3
    )

    enrollment.refresh_from_db()
    assert enrollment.completion == 1.0
