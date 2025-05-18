from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0001_initial"),
    ]

    operations = [
        # First add a temporary UUID field (not primary key yet)
        migrations.AddField(
            model_name="studentprofile",
            name="uuid_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="teacherprofile",
            name="uuid_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        # Add the status and meta fields
        migrations.AddField(
            model_name="studentprofile",
            name="meta",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "Active"),
                    ("inactive", "Inactive"),
                    ("pending", "Pending"),
                    ("deleted", "Deleted"),
                    ("archived", "Archived"),
                    ("suspended", "Suspended"),
                    ("blocked", "Blocked"),
                ],
                default="active",
                max_length=20,
                verbose_name="status",
            ),
        ),
        migrations.AddField(
            model_name="teacherprofile",
            name="meta",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="teacherprofile",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "Active"),
                    ("inactive", "Inactive"),
                    ("pending", "Pending"),
                    ("deleted", "Deleted"),
                    ("archived", "Archived"),
                    ("suspended", "Suspended"),
                    ("blocked", "Blocked"),
                ],
                default="active",
                max_length=20,
                verbose_name="status",
            ),
        ),
    ]
