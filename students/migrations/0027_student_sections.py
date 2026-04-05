from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0026_timetable_section'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='section_capacity',
            field=models.PositiveIntegerField(default=60),
        ),
        migrations.AddField(
            model_name='student',
            name='section',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
    ]
