# from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
# from django.db import models
# from django.utils.translation import gettext_lazy as _
# from django.core.exceptions import ValidationError
# from django.contrib.auth.hashers import identify_hasher

# # from apps.abstract.choices import UserType
# # from apps.abstract.models import BaseModel
# from apps.user.managers import UserManager


# class User(BaseModel, AbstractBaseUser, PermissionsMixin):
#     """
#     Custom user model that uses email as the unique identifier.
#     """

#     user_type = models.CharField(
#         max_length=20,
#         choices=UserType.choices,
#         default=UserType.USER,
#         verbose_name=_("user type"),
#     )
#     email = models.EmailField(unique=True, verbose_name=_("email address"))
#     first_name = models.CharField(max_length=30, verbose_name=_("first name"))
#     otp = models.CharField(max_length=6, blank=True, null=True, verbose_name=_("otp"))
#     otp_verified = models.BooleanField(default=False, verbose_name=_("otp verified"))
#     otp_created_at = models.DateTimeField(
#         blank=True, null=True, verbose_name=_("otp created at")
#     )
#     phone_verified = models.BooleanField(
#         default=False, verbose_name=_("phone verified")
#     )
#     phone_number = models.CharField(
#         max_length=15, blank=True, null=True, verbose_name=_("phone number")
#     )
#     last_name = models.CharField(max_length=30, verbose_name=_("last name"))
#     is_active = models.BooleanField(default=True, verbose_name=_("is active"))
#     is_staff = models.BooleanField(default=False, verbose_name=_("is staff"))

#     USERNAME_FIELD = "email"
#     REQUIRED_FIELDS = ["first_name", "last_name"]

#     objects = UserManager()  # Custom user manager

#     def __str__(self):
#         return self.email

#     def save(self, *args, **kwargs):
#         if not self.pk:
#             try:
#                 # If this is already a Django‐style hash, identify_hasher won’t error
#                 identify_hasher(self.password)
#             except ValueError:
#                 # not a hash yet, so hash it
#                 self.set_password(self.password)
#         super().save(*args, **kwargs)

#     def clean(self):
#         """
#         Custom validation to ensure that the email is unique and valid.
#         """
#         if not self.email or not self.phone_number:
#             raise ValidationError(_("Email is required."))
#         if User.objects.filter(email=self.email).exists():
#             raise ValidationError(_("Email already exists."))

#         if (
#             self.status != "DELETED"
#             and User.objects.exclude(pk=self.pk)
#             .filter(email=self.email, status__ne="DELETED")
#             .exists()
#         ):
#             raise ValidationError("A user with this email already exists.")

#     class Meta:
#         verbose_name = _("user")
#         verbose_name_plural = _("users")
#         ordering = ["email"]

#     def get_full_name(self):
#         """
#         Returns the user's full name.
#         """
#         return f"{self.first_name} {self.last_name}"

#     def get_short_name(self):
#         """
#         Returns the user's short name.
#         """
#         return self.first_name
