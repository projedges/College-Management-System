from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0024_classroom_building_timetable_break'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='lecture_hours',
            field=models.IntegerField(default=3, help_text='Lecture hours per week (L)'),
        ),
        migrations.AddField(
            model_name='subject',
            name='tutorial_hours',
            field=models.IntegerField(default=0, help_text='Tutorial hours per week (T)'),
        ),
        migrations.AddField(
            model_name='subject',
            name='practical_hours',
            field=models.IntegerField(default=0, help_text='Practical/Lab hours per week (P)'),
        ),
        migrations.AddField(
            model_name='subject',
            name='credits',
            field=models.IntegerField(default=3, help_text='Credits (C)'),
        ),
        migrations.AddField(
            model_name='subject',
            name='category',
            field=models.CharField(
                choices=[
                    ('PC', 'Program Core'),
                    ('PE', 'Program Elective'),
                    ('OE', 'Open Elective'),
                    ('BS', 'Basic Science'),
                    ('PC/BS', 'Program Core / Basic Science'),
                    ('MC', 'Mandatory Course'),
                    ('PW', 'Project Work'),
                    ('AC', 'Audit Course'),
                    ('HS', 'Humanities & Social Science'),
                    ('ES', 'Engineering Science'),
                    ('OTHER', 'Other'),
                ],
                default='PC',
                help_text='Subject category',
                max_length=10,
            ),
        ),
    ]
