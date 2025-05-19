from rest_framework import serializers
from django.utils import timezone

from apps.profiles.serializers import StudentProfileSerializer, TeacherProfileSerializer
from .models import Course, Assignment, Enrollment, Submission


class CourseSerializer(serializers.ModelSerializer):
    teacher = TeacherProfileSerializer(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    student_count = serializers.IntegerField(read_only=True, source="student_count")
    available_slots = serializers.IntegerField(read_only=True, source="available_slots")
    assignment_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "code",
            "description",
            "teacher",
            "start_date",
            "end_date",
            "is_active",
            "created_at",
            "is_enrolled",
            "max_students",
            "enrollment_open",
            "syllabus",
            "student_count",
            "available_slots",
            "assignment_count",
        ]
        read_only_fields = [
            "teacher",
            "created_at",
            "is_enrolled",
            "student_count",
            "available_slots",
            "assignment_count",
        ]

    def get_assignment_count(self, obj):
        return obj.assignments.count()

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if hasattr(request.user, "student_profile"):
                return obj.enrollments.filter(
                    student=request.user.student_profile, is_active=True
                ).exists()
        return False

    def validate(self, data):
        """Validate course dates."""
        start_date = data.get(
            "start_date", self.instance.start_date if self.instance else None
        )
        end_date = data.get(
            "end_date", self.instance.end_date if self.instance else None
        )

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "End date must be after start date"}
            )

        return data


class CourseDetailSerializer(CourseSerializer):
    """Extended course serializer with enrollments info for teachers."""

    enrollments = serializers.SerializerMethodField()
    assignments = serializers.SerializerMethodField()

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ["enrollments", "assignments"]

    def get_enrollments(self, obj):
        # Only show enrollments to teachers
        request = self.context.get("request")
        if request and hasattr(request.user, "teacher_profile"):
            if request.user.teacher_profile == obj.teacher:
                enrollments = obj.enrollments.filter(is_active=True)
                return EnrollmentListSerializer(enrollments, many=True).data
        return []

    def get_assignments(self, obj):
        assignments = obj.assignments.all()
        return AssignmentBasicSerializer(
            assignments, many=True, context=self.context
        ).data


class AssignmentBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for assignments list view."""

    submission_count = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id",
            "title",
            "due_date",
            "max_points",
            "submission_count",
        ]

    def get_submission_count(self, obj):
        return obj.submissions.count()


class AssignmentSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    has_submitted = serializers.SerializerMethodField()
    is_past_due = serializers.BooleanField(source="is_past_due", read_only=True)
    can_accept_submission = serializers.BooleanField(
        source="can_accept_submission", read_only=True
    )

    class Meta:
        model = Assignment
        fields = [
            "id",
            "course",
            "course_code",
            "course_title",
            "title",
            "description",
            "instructions",
            "due_date",
            "max_points",
            "allow_late_submissions",
            "late_submission_deadline",
            "attachment_required",
            "weight",
            "created_at",
            "has_submitted",
            "is_past_due",
            "can_accept_submission",
        ]
        read_only_fields = [
            "created_at",
            "has_submitted",
            "is_past_due",
            "can_accept_submission",
            "course_code",
            "course_title",
        ]

    def get_has_submitted(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if hasattr(request.user, "student_profile"):
                return obj.submissions.filter(
                    student=request.user.student_profile
                ).exists()
        return False

    def validate(self, data):
        """Validate assignment dates."""
        due_date = data.get("due_date")
        if due_date and due_date < timezone.now():
            raise serializers.ValidationError(
                {"due_date": "Due date cannot be in the past"}
            )

        allow_late_submissions = data.get("allow_late_submissions", False)
        late_submission_deadline = data.get("late_submission_deadline")

        if (
            allow_late_submissions
            and late_submission_deadline
            and late_submission_deadline < due_date
        ):
            raise serializers.ValidationError(
                {
                    "late_submission_deadline": "Late submission deadline must be after the due date"
                }
            )

        return data


class EnrollmentListSerializer(serializers.ModelSerializer):
    """Simplified enrollment serializer for lists."""

    student_name = serializers.CharField(
        source="student.user.get_full_name", read_only=True
    )
    student_email = serializers.EmailField(source="student.user.email", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student_name",
            "student_email",
            "enrolled_at",
            "is_active",
            "completion_percentage",
            "grade",
        ]


class EnrollmentSerializer(serializers.ModelSerializer):
    student = StudentProfileSerializer(read_only=True)
    course = CourseSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "course",
            "enrolled_at",
            "is_active",
            "last_activity",
            "completion_percentage",
            "grade",
        ]
        read_only_fields = [
            "enrolled_at",
            "completion_percentage",
            "grade",
            "last_activity",
        ]


class SubmissionListSerializer(serializers.ModelSerializer):
    """Simplified submission serializer for lists."""

    student_name = serializers.CharField(
        source="student.user.get_full_name", read_only=True
    )
    assignment_title = serializers.CharField(source="assignment.title", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "student_name",
            "assignment_title",
            "submitted_at",
            "is_reviewed",
            "points",
            "is_late",
        ]


class SubmissionSerializer(serializers.ModelSerializer):
    assignment_title = serializers.CharField(source="assignment.title", read_only=True)
    course_title = serializers.CharField(
        source="assignment.course.title", read_only=True
    )
    max_points = serializers.IntegerField(
        source="assignment.max_points", read_only=True
    )
    student_name = serializers.CharField(
        source="student.user.get_full_name", read_only=True
    )
    student_email = serializers.EmailField(source="student.user.email", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "assignment",
            "assignment_title",
            "course_title",
            "student",
            "student_name",
            "student_email",
            "content",
            "attachment",
            "submitted_at",
            "is_late",
            "points",
            "max_points",
            "is_reviewed",
            "feedback",
            "resubmission_count",
            "last_updated",
        ]
        read_only_fields = [
            "assignment",
            "student",
            "submitted_at",
            "is_late",
            "resubmission_count",
            "last_updated",
            "assignment_title",
            "course_title",
            "student_name",
            "student_email",
            "max_points",
        ]


class CreateSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ["assignment", "content", "attachment"]

    def validate(self, data):
        assignment = data.get("assignment")
        user = self.context["request"].user

        # Check if student is enrolled in the course
        if not Enrollment.objects.filter(
            student=user.student_profile, course=assignment.course, is_active=True
        ).exists():
            raise serializers.ValidationError(
                "You must be enrolled in the course to submit this assignment"
            )

        # Check if the assignment can still accept submissions
        if not assignment.can_accept_submission:
            if assignment.allow_late_submissions:
                raise serializers.ValidationError(
                    "This assignment is no longer accepting submissions"
                )
            else:
                raise serializers.ValidationError(
                    "This assignment is past its due date"
                )

        # Check if attachment is required but not provided
        if assignment.attachment_required and not data.get("attachment"):
            raise serializers.ValidationError("This assignment requires an attachment")

        # Check if student has already submitted (assuming update is handled elsewhere)
        if (
            not self.instance
            and Submission.objects.filter(
                assignment=assignment, student=user.student_profile
            ).exists()
        ):
            raise serializers.ValidationError(
                "You have already submitted this assignment"
            )

        return data


class GradeSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ["points", "feedback", "is_reviewed"]

    def validate_points(self, value):
        max_points = self.instance.assignment.max_points
        if value > max_points:
            raise serializers.ValidationError(
                f"Points cannot exceed the maximum of {max_points}"
            )
        if value < 0:
            raise serializers.ValidationError("Points cannot be negative")
        return value

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        # Update student's enrollment grade if submission is reviewed
        if instance.is_reviewed:
            enrollment = Enrollment.objects.get(
                student=instance.student, course=instance.assignment.course
            )
            enrollment.update_grade()

        return instance
