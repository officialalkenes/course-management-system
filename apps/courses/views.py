# apps/courses/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

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
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if hasattr(user, "teacher_profile"):
            return queryset.filter(teacher=user.teacher_profile)
        elif hasattr(user, "student_profile"):
            return queryset.filter(
                enrollments__student=user.student_profile, enrollments__is_active=True
            )
        return queryset.none()

    def perform_create(self, serializer):
        if hasattr(self.request.user, "teacher_profile"):
            serializer.save(teacher=self.request.user.teacher_profile)
        else:
            raise permissions.PermissionDenied("Only teachers can create courses")

    @action(detail=True, methods=["post"])
    def enroll(self, request, pk=None):
        course = self.get_object()
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"detail": "Only students can enroll in courses"},
                status=status.HTTP_403_FORBIDDEN,
            )

        student = request.user.student_profile
        enrollment, created = Enrollment.objects.get_or_create(
            student=student, course=course, defaults={"is_active": True}
        )

        if not created:
            enrollment.is_active = True
            enrollment.save()

        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def unenroll(self, request, pk=None):
        course = self.get_object()
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"detail": "Only students can unenroll from courses"},
                status=status.HTTP_403_FORBIDDEN,
            )

        student = request.user.student_profile
        enrollment = get_object_or_404(Enrollment, student=student, course=course)
        enrollment.is_active = False
        enrollment.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if hasattr(user, "teacher_profile"):
            return queryset.filter(course__teacher=user.teacher_profile)
        elif hasattr(user, "student_profile"):
            return queryset.filter(
                course__enrollments__student=user.student_profile,
                course__enrollments__is_active=True,
            )
        return queryset.none()

    def perform_create(self, serializer):
        course = serializer.validated_data.get("course")
        if not hasattr(self.request.user, "teacher_profile"):
            raise permissions.PermissionDenied("Only teachers can create assignments")
        if course.teacher != self.request.user.teacher_profile:
            raise permissions.PermissionDenied(
                "You can only create assignments for your own courses"
            )
        serializer.save()


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateSubmissionSerializer
        elif self.action == "grade":
            return GradeSubmissionSerializer
        return SubmissionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if hasattr(user, "teacher_profile"):
            return queryset.filter(assignment__course__teacher=user.teacher_profile)
        elif hasattr(user, "student_profile"):
            return queryset.filter(student=user.student_profile)
        return queryset.none()

    def perform_create(self, serializer):
        assignment = serializer.validated_data.get("assignment")
        if not hasattr(self.request.user, "student_profile"):
            raise permissions.PermissionDenied("Only students can submit assignments")

        student = self.request.user.student_profile
        if not assignment.course.enrollments.filter(
            student=student, is_active=True
        ).exists():
            raise permissions.PermissionDenied(
                "You must be enrolled in the course to submit assignments"
            )

        if Submission.objects.filter(assignment=assignment, student=student).exists():
            raise permissions.PermissionDenied(
                "You have already submitted this assignment"
            )

        serializer.save(student=student)

    @action(detail=True, methods=["post"])
    def grade(self, request, pk=None):
        submission = self.get_object()
        if not hasattr(request.user, "teacher_profile"):
            return Response(
                {"detail": "Only teachers can grade submissions"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if submission.assignment.course.teacher != request.user.teacher_profile:
            return Response(
                {"detail": "You can only grade submissions for your own courses"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(submission, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(is_reviewed=True)
        return Response(serializer.data)
