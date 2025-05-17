from django.db import models


class UserType(models.TextChoices):
    """
    Choices for the user type field in models.
    """

    TEACHER = "teacher", "Teacher"
    STUDENT = "student", "Student"
    SUPERADMIN = "super_admin", "Super Admin"
    USER = "user", "User"


class StatusCHOICES(models.TextChoices):
    """
    Choices for the status field in models.
    """

    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    PENDING = "pending", "Pending"
    DELETED = "deleted", "Deleted"
    ARCHIVED = "archived", "Archived"
    SUSPENDED = "suspended", "Suspended"
    BLOCKED = "blocked", "Blocked"
