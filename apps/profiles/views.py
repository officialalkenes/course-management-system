# views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from apps.abstract.choices import UserType
from apps.profiles.models import StudentProfile, TeacherProfile
from .serializers import TeacherOnboardingSerializer, StudentOnboardingSerializer
from django.shortcuts import get_object_or_404


class OnboardingViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="teacher")
    def teacher_onboarding(self, request):
        if request.user.user_type != UserType.TEACHER:
            return Response(
                {"detail": "Only teachers can complete this onboarding."},
                status=status.HTTP_403_FORBIDDEN,
            )

        profile = get_object_or_404(TeacherProfile, user=request.user)
        serializer = TeacherOnboardingSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="student")
    def student_onboarding(self, request):
        if request.user.user_type != UserType.STUDENT:
            return Response(
                {"detail": "Only students can complete this onboarding."},
                status=status.HTTP_403_FORBIDDEN,
            )

        profile = get_object_or_404(StudentProfile, user=request.user)
        serializer = StudentOnboardingSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
