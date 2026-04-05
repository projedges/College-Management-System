from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0025_subject_ltpc_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetable',
            name='section',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Section label e.g. A, B, C. Leave blank if no sections.',
                max_length=10,
            ),
        ),
    ]
