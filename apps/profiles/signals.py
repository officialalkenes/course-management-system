# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.abstract.choices import UserType
from .models import TeacherProfile, StudentProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == UserType.TEACHER:
            TeacherProfile.objects.create(user=instance)
        elif instance.user_type == UserType.STUDENT:
            StudentProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "teacher_profile"):
        instance.teacher_profile.save()
    elif hasattr(instance, "student_profile"):
        instance.student_profile.save()
