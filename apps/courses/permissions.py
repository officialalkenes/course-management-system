# apps/courses/permissions.py
from rest_framework import permissions


class IsCourseTeacher(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, "teacher_profile"):
            return obj.teacher == request.user.teacher_profile
        return False


class IsEnrolledStudent(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, "student_profile"):
            if hasattr(obj, "course"):
                return obj.course.enrollments.filter(
                    student=request.user.student_profile, is_active=True
                ).exists()
            elif hasattr(obj, "assignment"):
                return obj.assignment.course.enrollments.filter(
                    student=request.user.student_profile, is_active=True
                ).exists()
        return False
