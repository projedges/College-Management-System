from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_registration_request_statuses(apps, schema_editor):
    RegistrationRequest = apps.get_model("students", "RegistrationRequest")
    RegistrationRequest.objects.filter(status="PENDING").update(status="SUBMITTED")
    RegistrationRequest.objects.filter(status="REVIEWED").update(status="APPROVED")


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0022_supply_exam_registration"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="registrationrequest",
            name="correction_fields",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="registrationrequest",
            name="review_notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="registrationrequest",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="registrationrequest",
            name="reviewed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reviewed_registration_requests",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(migrate_registration_request_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="registrationrequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("SUBMITTED", "Submitted"),
                    ("UNDER_REVIEW", "Under Review"),
                    ("NEEDS_CORRECTION", "Needs Correction"),
                    ("APPROVED", "Approved"),
                    ("CONVERTED", "Converted"),
                    ("REJECTED", "Rejected"),
                ],
                default="SUBMITTED",
                max_length=20,
            ),
        ),
    ]
