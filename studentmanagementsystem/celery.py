import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studentmanagementsystem.settings')

app = Celery('studentmanagementsystem')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# ── Periodic task schedule ────────────────────────────────────────────────────
app.conf.beat_schedule = {
    # Fee reminders: daily at 9 AM IST
    'fee-reminders-daily': {
        'task': 'students.tasks.send_fee_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
    # Attendance alerts: daily at 8 AM IST
    'attendance-alerts-daily': {
        'task': 'students.tasks.send_attendance_alerts',
        'schedule': crontab(hour=8, minute=0),
    },
}
app.conf.timezone = 'Asia/Kolkata'
