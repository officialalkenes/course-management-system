# apps/courses/serializers.py
from rest_framework import serializers

from apps.profiles.serializers import StudentProfileSerializer, TeacherProfileSerializer
from .models import Course, Assignment, Enrollment, Submission


class CourseSerializer(serializers.ModelSerializer):
    teacher = TeacherProfileSerializer(read_only=True)
    is_enrolled = serializers.SerializerMethodField()

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
        ]

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if hasattr(request.user, "student_profile"):
                return obj.enrollments.filter(
                    student=request.user.student_profile, is_active=True
                ).exists()
        return False


class AssignmentSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(read_only=True)
    has_submitted = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id",
            "course",
            "title",
            "description",
            "due_date",
            "max_points",
            "created_at",
            "has_submitted",
        ]

    def get_has_submitted(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if hasattr(request.user, "student_profile"):
                return obj.submissions.filter(
                    student=request.user.student_profile
                ).exists()
        return False


class EnrollmentSerializer(serializers.ModelSerializer):
    student = StudentProfileSerializer(read_only=True)
    course = CourseSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "student", "course", "enrolled_at", "is_active"]


class SubmissionSerializer(serializers.ModelSerializer):
    assignment = serializers.PrimaryKeyRelatedField(read_only=True)
    student = StudentProfileSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "assignment",
            "student",
            "content",
            "submitted_at",
            "points",
            "is_reviewed",
            "feedback",
        ]


class CreateSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ["content"]


class GradeSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ["points", "feedback", "is_reviewed"]
