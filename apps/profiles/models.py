from django.db import models

from django.contrib.auth import get_user_model

User = get_user_model()


class TeacherProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="teacher_profile"
    )
    bio = models.TextField(blank=True, null=True)
    qualifications = models.TextField(blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(blank=True, null=True)
    institution = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Teacher Profile"
        verbose_name_plural = "Teacher Profiles"

    def __str__(self):
        return f"Teacher Profile for {self.user.email}"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile"
    )
    student_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    date_of_birth = models.DateField(blank=True, null=True)
    grade_level = models.CharField(max_length=50, blank=True, null=True)
    parent_guardian_name = models.CharField(max_length=100, blank=True, null=True)
    parent_guardian_contact = models.CharField(max_length=20, blank=True, null=True)
    school_name = models.CharField(max_length=100, blank=True, null=True)
    academic_interests = models.TextField(blank=True, null=True)
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"

    def __str__(self):
        return f"Student Profile for {self.user.email}"
