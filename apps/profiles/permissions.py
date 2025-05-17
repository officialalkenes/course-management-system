# permissions.py
from rest_framework.permissions import BasePermission

from apps.abstract.choices import UserType


class IsOnboardingComplete(BasePermission):
    message = "Please complete your profile onboarding before accessing this resource."

    def has_permission(self, request, view):
        user = request.user
        if user.user_type == UserType.TEACHER:
            return (
                hasattr(user, "teacher_profile")
                and user.teacher_profile.onboarding_completed
            )
        elif user.user_type == UserType.STUDENT:
            return (
                hasattr(user, "student_profile")
                and user.student_profile.onboarding_completed
            )
        return True
