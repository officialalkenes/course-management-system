import uuid

from django.db import models

from apps.abstract.choices import StatusCHOICES


class BaseModel(models.Model):
    """
    Abstract base model that provides common fields and methods for all models.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusCHOICES.choices,
        default=StatusCHOICES.ACTIVE,
        verbose_name="status",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="updated at")
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]  # Default ordering by creation date
        get_latest_by = "created_at"
        verbose_name = "base model"
        verbose_name_plural = "base models"
