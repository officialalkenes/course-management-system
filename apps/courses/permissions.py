from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


class IsCourseTeacher(permissions.BasePermission):
    """
    Permission to check if the user is the teacher of the course.

    For objects that are courses themselves, checks if course.teacher == user.teacher_profile.
    For objects that have a course attribute, checks if obj.course.teacher == user.teacher_profile.
    """

    message = _("You must be the teacher of this course to perform this action.")

    def has_permission(self, request, view):
        # Allow list and retrieve actions for authenticated users
        if view.action in ["list", "retrieve"] and request.user.is_authenticated:
            return True

        # For other actions, check if user is a teacher
        return hasattr(request.user, "teacher_profile")

    def has_object_permission(self, request, view, obj):
        # For read actions, allow both teachers and enrolled students
        if request.method in permissions.SAFE_METHODS:
            # For teachers, check if they own the course
            if hasattr(request.user, "teacher_profile"):
                teacher_profile = request.user.teacher_profile

                # Check if obj is a Course or has a course attribute
                if hasattr(obj, "teacher"):
                    return obj.teacher == teacher_profile
                elif hasattr(obj, "course"):
                    return obj.course.teacher == teacher_profile

            # For students, check if they're enrolled in the course
            elif hasattr(request.user, "student_profile"):
                student_profile = request.user.student_profile

                # Check if obj is a Course or has a course attribute
                if hasattr(obj, "enrollments"):
                    return obj.enrollments.filter(
                        student=student_profile, is_active=True
                    ).exists()
                elif hasattr(obj, "course") and hasattr(obj.course, "enrollments"):
                    return obj.course.enrollments.filter(
                        student=student_profile, is_active=True
                    ).exists()

            return False

        # For write actions, only allow teachers who own the course
        if not hasattr(request.user, "teacher_profile"):
            return False

        teacher_profile = request.user.teacher_profile

        # Check if obj is a Course or has a course attribute
        if hasattr(obj, "teacher"):
            return obj.teacher == teacher_profile
        elif hasattr(obj, "course"):
            return obj.course.teacher == teacher_profile

        return False


class IsEnrolledStudent(permissions.BasePermission):
    """
    Permission to check if the user is enrolled in the course associated with an object.
    """

    message = _("You must be enrolled in this course to perform this action.")

    def has_permission(self, request, view):
        # Only allow students to take student-specific actions
        if view.action in ["create", "submit"]:
            return hasattr(request.user, "student_profile")

        # Allow list and retrieve for all authenticated users
        if view.action in ["list", "retrieve"]:
            return request.user.is_authenticated

        return False

    def has_object_permission(self, request, view, obj):
        # Only students can access student-specific objects
        if not hasattr(request.user, "student_profile"):
            return False

        student_profile = request.user.student_profile

        # For submissions, check if the student is the owner
        if hasattr(obj, "student"):
            if obj.student == student_profile:
                return True

        # Check if student is enrolled in the related course
        if hasattr(obj, "course"):
            return obj.course.enrollments.filter(
                student=student_profile, is_active=True
            ).exists()
        elif hasattr(obj, "assignment") and hasattr(obj.assignment, "course"):
            return obj.assignment.course.enrollments.filter(
                student=student_profile, is_active=True
            ).exists()

        return False


class IsSubmissionOwnerOrCourseTeacher(permissions.BasePermission):
    """
    Permission to check if the user is either:
    - The student who owns the submission (can view only)
    - The teacher of the course the submission belongs to (can view and grade)
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Students can only view their own submissions
        if hasattr(user, "student_profile"):
            if obj.student == user.student_profile:
                # Students can only read their submissions, not modify them
                return request.method in permissions.SAFE_METHODS

        # Teachers can view and grade submissions for their courses
        if hasattr(user, "teacher_profile"):
            if obj.assignment.course.teacher == user.teacher_profile:
                return True

        return False
