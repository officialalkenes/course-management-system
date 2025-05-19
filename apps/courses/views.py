# apps/courses/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


from apps.courses.filters import AssignmentFilter
from apps.courses.permissions import (
    IsCourseTeacher,
    IsEnrolledStudent,
    IsSubmissionOwnerOrCourseTeacher,
)
from apps.courses.serializers import (
    AssignmentSerializer,
    CourseSerializer,
    CreateSubmissionSerializer,
    GradeSubmissionSerializer,
    SubmissionSerializer,
    EnrollmentSerializer,
)
from .models import Course, Assignment, Enrollment, Submission


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsCourseTeacher]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_active", "enrollment_open"]
    search_fields = ["title", "code"]
    ordering_fields = ["start_date", "end_date", "created_at"]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "teacher_profile"):
            return Course.objects.filter(teacher=user.teacher_profile)
        elif hasattr(user, "student_profile"):
            return Course.objects.filter(
                enrollments__student=user.student_profile, enrollments__is_active=True
            )
        return Course.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "teacher_profile"):
            raise permissions.PermissionDenied("Only teachers can create courses")
        serializer.save(teacher=user.teacher_profile)

    @action(detail=True, methods=["post"])
    def enroll(self, request, pk=None):
        course = self.get_object()
        user = request.user

        if not hasattr(user, "student_profile"):
            return Response(
                {"detail": "Only students can enroll in courses."},
                status=status.HTTP_403_FORBIDDEN,
            )

        enrollment, created = Enrollment.objects.get_or_create(
            student=user.student_profile, course=course, defaults={"is_active": True}
        )

        if not created and not enrollment.is_active:
            enrollment.is_active = True
            enrollment.save()

        serializer = EnrollmentSerializer(enrollment)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def unenroll(self, request, pk=None):
        course = self.get_object()
        user = request.user

        if not hasattr(user, "student_profile"):
            return Response(
                {"detail": "Only students can unenroll from courses."},
                status=status.HTTP_403_FORBIDDEN,
            )

        enrollment = get_object_or_404(
            Enrollment, student=user.student_profile, course=course
        )
        enrollment.is_active = False
        enrollment.save()

        return Response(
            {"detail": "Successfully unenrolled."}, status=status.HTTP_204_NO_CONTENT
        )


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsCourseTeacher]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AssignmentFilter
    ordering_fields = ["due_date", "created_at"]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "teacher_profile"):
            return Assignment.objects.filter(course__teacher=user.teacher_profile)
        elif hasattr(user, "student_profile"):
            return Assignment.objects.filter(
                course__enrollments__student=user.student_profile,
                course__enrollments__is_active=True,
            )
        return Assignment.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        course = serializer.validated_data.get("course")

        if not hasattr(user, "teacher_profile"):
            raise permissions.PermissionDenied("Only teachers can create assignments")

        if course.teacher != user.teacher_profile:
            raise permissions.PermissionDenied(
                "You can only create assignments for your own courses"
            )

        serializer.save()


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["assignment", "is_reviewed", "is_late"]
    ordering_fields = ["submitted_at", "points", "last_updated"]

    def get_permissions(self):
        if self.action == "grade":
            return [permissions.IsAuthenticated(), IsCourseTeacher()]
        elif self.action in ["create", "list", "retrieve"]:
            return [permissions.IsAuthenticated(), IsEnrolledStudent()]
        return [permissions.IsAuthenticated(), IsSubmissionOwnerOrCourseTeacher()]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateSubmissionSerializer
        elif self.action == "grade":
            return GradeSubmissionSerializer
        return SubmissionSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "teacher_profile"):
            return Submission.objects.filter(
                assignment__course__teacher=user.teacher_profile
            )
        elif hasattr(user, "student_profile"):
            return Submission.objects.filter(student=user.student_profile)
        return Submission.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        assignment = serializer.validated_data.get("assignment")

        if not hasattr(user, "student_profile"):
            raise permissions.PermissionDenied("Only students can submit assignments")

        student = user.student_profile

        if not assignment.course.enrollments.filter(
            student=student, is_active=True
        ).exists():
            raise permissions.PermissionDenied(
                "You must be enrolled in the course to submit this assignment"
            )

        if Submission.objects.filter(assignment=assignment, student=student).exists():
            raise permissions.PermissionDenied(
                "You have already submitted this assignment"
            )

        serializer.save(student=student)

    @action(detail=True, methods=["post"])
    def grade(self, request, pk=None):
        submission = self.get_object()
        user = request.user

        if not hasattr(user, "teacher_profile"):
            return Response(
                {"detail": "Only teachers can grade submissions"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if submission.assignment.course.teacher != user.teacher_profile:
            return Response(
                {"detail": "You can only grade submissions for your own courses"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(submission, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(is_reviewed=True)
        return Response(serializer.data)
