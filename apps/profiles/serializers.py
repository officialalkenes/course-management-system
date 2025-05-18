# serializers.py
import re
from rest_framework import serializers
from .models import TeacherProfile, StudentProfile


class TeacherOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = [
            "bio",
            "qualifications",
            "specialization",
            "years_of_experience",
            "institution",
            "department",
        ]
        extra_kwargs = {
            "bio": {"required": True},
            "qualifications": {"required": True},
            "specialization": {"required": True},
        }

    def validate(self, data):
        # Add any custom validation logic here
        return data

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.onboarding_completed = True
        instance.save()
        return instance


class StudentOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            "student_id",
            "date_of_birth",
            "grade_level",
            "parent_guardian_name",
            "parent_guardian_contact",
            "school_name",
            "academic_interests",
        ]
        extra_kwargs = {
            "student_id": {"required": True},
            "date_of_birth": {"required": True},
            "grade_level": {"required": True},
        }

    def validate_parent_guardian_contact(self, value):
        if value and not re.match(r"^\+?[0-9]{10,15}$", value):
            raise serializers.ValidationError("Invalid phone number format")
        return value

    def validate(self, data):
        return data

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.onboarding_completed = True
        instance.save()
        return instance


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = [
            "id",
            "bio",
            "qualifications",
            "specialization",
            "years_of_experience",
            "institution",
            "department",
            "is_verified",
            "onboarding_completed",
        ]


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "student_id",
            "date_of_birth",
            "grade_level",
            "parent_guardian_name",
            "parent_guardian_contact",
            "school_name",
            "academic_interests",
            "onboarding_completed",
        ]
