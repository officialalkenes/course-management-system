from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.abstract.models import BaseModel
from apps.profiles.models import TeacherProfile, StudentProfile


class Course(BaseModel):
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.CASCADE, related_name="courses"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    max_students = models.PositiveIntegerField(
        default=30, help_text="Maximum number of students allowed to enroll"
    )
    enrollment_open = models.BooleanField(
        default=True, help_text="Whether enrollment is currently open"
    )
    syllabus = models.TextField(blank=True, null=True, help_text="Course syllabus")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return f"{self.code}: {self.title}"

    def clean(self):
        """Validate that end_date is after start_date."""
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_enrollment_active(self):
        """Check if course enrollment is active."""
        return (
            self.is_active
            and self.enrollment_open
            and self.end_date >= timezone.now().date()
        )

    @property
    def student_count(self):
        """Get the number of active enrollments."""
        return self.enrollments.filter(is_active=True).count()

    @property
    def available_slots(self):
        """Get the number of available enrollment slots."""
        return max(0, self.max_students - self.student_count)


class Assignment(BaseModel):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="assignments"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    max_points = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    instructions = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed instructions for completing the assignment",
    )
    allow_late_submissions = models.BooleanField(
        default=False, help_text="Whether late submissions are allowed"
    )
    late_submission_deadline = models.DateTimeField(
        blank=True, null=True, help_text="Final deadline for late submissions"
    )
    attachment_required = models.BooleanField(
        default=False, help_text="Whether an attachment is required"
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        help_text="Weight of this assignment in the overall course grade",
    )

    class Meta:
        ordering = ["due_date"]
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"

    def __str__(self):
        return f"{self.course.code} - {self.title}"

    def clean(self):
        """Validate assignment dates."""
        if self.due_date and self.due_date < timezone.now():
            raise ValidationError({"due_date": "Due date cannot be in the past."})

        if (
            self.allow_late_submissions
            and self.late_submission_deadline
            and self.late_submission_deadline < self.due_date
        ):
            raise ValidationError(
                {
                    "late_submission_deadline": "Late submission deadline must be after the due date."
                }
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_past_due(self):
        """Check if the assignment is past due."""
        return timezone.now() > self.due_date

    @property
    def can_accept_submission(self):
        """Check if the assignment can still accept submissions."""
        if not self.is_past_due:
            return True
        if self.allow_late_submissions:
            if self.late_submission_deadline:
                return timezone.now() <= self.late_submission_deadline
            return True
        return False


class Enrollment(BaseModel):
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    last_activity = models.DateTimeField(
        default=timezone.now, help_text="Last time the student accessed the course"
    )
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Percentage of course completed",
    )
    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Overall course grade",
    )

    class Meta:
        unique_together = ("student", "course")
        ordering = ["-enrolled_at"]
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"

    def __str__(self):
        return f"{self.student.user.email} in {self.course.code}"

    def clean(self):
        """Validate enrollment."""
        # Check if the course is accepting enrollments
        if not self.course.is_enrollment_active and not self.pk:
            raise ValidationError(
                "This course is not accepting enrollments at this time."
            )

        # Check if the course is at capacity
        if self.course.student_count >= self.course.max_students and not self.pk:
            raise ValidationError("This course has reached its enrollment capacity.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def update_grade(self):
        """Update the student's overall grade based on their submissions."""
        submissions = Submission.objects.filter(
            student=self.student, assignment__course=self.course, is_reviewed=True
        )

        if not submissions.exists():
            self.grade = None
            self.save(update_fields=["grade"])
            return

        total_weight = 0
        weighted_score = 0

        for submission in submissions:
            assignment = submission.assignment
            if submission.points is not None:
                weight = float(assignment.weight)
                score = submission.points / assignment.max_points
                weighted_score += score * weight
                total_weight += weight

        if total_weight > 0:
            final_grade = (weighted_score / total_weight) * 100
            self.grade = round(final_grade, 2)
            self.save(update_fields=["grade"])

    def update_completion(self):
        """Update the completion percentage based on submitted assignments."""
        total_assignments = self.course.assignments.count()
        if total_assignments == 0:
            self.completion_percentage = 0
        else:
            completed = Submission.objects.filter(
                student=self.student, assignment__course=self.course
            ).count()
            self.completion_percentage = (completed / total_assignments) * 100

        self.save(update_fields=["completion_percentage"])


class Submission(BaseModel):
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="submissions"
    )
    content = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    points = models.PositiveIntegerField(null=True, blank=True)
    is_reviewed = models.BooleanField(default=False)
    feedback = models.TextField(blank=True, null=True)

    # Additional fields
    attachment = models.FileField(upload_to="submissions/", null=True, blank=True)
    is_late = models.BooleanField(
        default=False,
        help_text="Whether this submission was submitted after the due date",
    )
    resubmission_count = models.PositiveIntegerField(
        default=0, help_text="Number of times this submission was resubmitted"
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("assignment", "student")
        ordering = ["-submitted_at"]
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"

    def __str__(self):
        return f"{self.student.user.email}'s submission for {self.assignment.title}"

    def clean(self):
        """Validate submission."""
        # Check if the student is enrolled in the course
        if not Enrollment.objects.filter(
            student=self.student, course=self.assignment.course, is_active=True
        ).exists():
            raise ValidationError(
                "You must be enrolled in the course to submit an assignment."
            )

        # Check if the assignment can accept submissions
        if not self.assignment.can_accept_submission and not self.pk:
            if self.assignment.allow_late_submissions:
                raise ValidationError(
                    "This assignment is no longer accepting submissions."
                )
            else:
                raise ValidationError("This assignment is past its due date.")

        # Check if attachment is required but not provided
        if self.assignment.attachment_required and not self.attachment:
            raise ValidationError("This assignment requires an attachment.")

    def save(self, *args, **kwargs):
        # Set is_late flag if submitting after the due date
        if not self.pk:  # Only check on creation
            self.is_late = timezone.now() > self.assignment.due_date

        super().save(*args, **kwargs)

        # Update enrollment grade and completion after submission
        enrollment = Enrollment.objects.get(
            student=self.student, course=self.assignment.course
        )
        enrollment.update_completion()
        if self.is_reviewed:
            enrollment.update_grade()
