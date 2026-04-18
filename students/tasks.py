"""
Celery background tasks for EduTrack.

Run worker:  celery -A studentmanagementsystem worker -l info
Run beat:    celery -A studentmanagementsystem beat -l info
"""
from celery import shared_task
from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Count, F, Sum
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


# ── Fee Reminders ─────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_fee_reminders(self):
    """
    Send fee reminders to students with pending/partial fees.
    Runs daily at 9 AM IST via Celery Beat.
    Sends:
      - 7-day advance reminder
      - 3-day advance reminder
      - Overdue reminder
    """
    from .models import Fee, FeeInstallment

    today = timezone.localdate()
    sent = 0
    errors = 0

    # ── 1. Upcoming fee due dates ─────────────────────────────────────────────
    for days_ahead in (7, 3):
        target_date = today + timedelta(days=days_ahead)
        fees = (
            Fee.objects
            .filter(status__in=['PENDING', 'PARTIAL'], due_date=target_date)
            .select_related('student__user', 'student__department__college')
        )
        for fee in fees:
            student = fee.student
            email = student.user.email
            if not email:
                continue
            balance = max(fee.total_amount - fee.paid_amount, 0)
            college_name = student.department.college.name
            try:
                send_mail(
                    subject=f'[{college_name}] Fee Due in {days_ahead} Days — Rs {balance:.0f}',
                    message=(
                        f'Dear {student.user.get_full_name() or student.user.username},\n\n'
                        f'This is a reminder that your semester fee of Rs {balance:.0f} '
                        f'is due on {fee.due_date.strftime("%d %b %Y")}.\n\n'
                        f'Please log in to the portal and complete your payment at your earliest convenience.\n\n'
                        f'Portal: {getattr(settings, "SITE_URL", "http://localhost:8000")}/dashboard/student/fees/pay/\n\n'
                        f'Regards,\n{college_name} — Accounts Department'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                sent += 1
            except Exception as exc:
                logger.warning('Fee reminder email failed for %s: %s', student.roll_number, exc)
                errors += 1

    # ── 2. Overdue fees ───────────────────────────────────────────────────────
    overdue_fees = (
        Fee.objects
        .filter(status__in=['PENDING', 'PARTIAL'], due_date__lt=today)
        .select_related('student__user', 'student__department__college')
    )
    for fee in overdue_fees:
        student = fee.student
        email = student.user.email
        if not email:
            continue
        balance = max(fee.total_amount - fee.paid_amount, 0)
        overdue_days = (today - fee.due_date).days
        college_name = student.department.college.name
        try:
            send_mail(
                subject=f'[{college_name}] OVERDUE Fee — Rs {balance:.0f} ({overdue_days} days overdue)',
                message=(
                    f'Dear {student.user.get_full_name() or student.user.username},\n\n'
                    f'Your semester fee of Rs {balance:.0f} was due on '
                    f'{fee.due_date.strftime("%d %b %Y")} and is now {overdue_days} day(s) overdue.\n\n'
                    f'Late fee penalties may apply. Please clear your dues immediately.\n\n'
                    f'Portal: {getattr(settings, "SITE_URL", "http://localhost:8000")}/dashboard/student/fees/pay/\n\n'
                    f'Regards,\n{college_name} — Accounts Department'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            sent += 1
        except Exception as exc:
            logger.warning('Overdue fee email failed for %s: %s', student.roll_number, exc)
            errors += 1

    logger.info('send_fee_reminders: sent=%d errors=%d', sent, errors)
    return {'sent': sent, 'errors': errors}


# ── Attendance Alerts ─────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_attendance_alerts(self):
    """
    Send attendance alerts to students below threshold.
    Runs daily at 8 AM IST via Celery Beat.
    """
    from .models import Student, Attendance, AttendanceRule, Subject
    from django.db.models import Count, Q

    sent = 0
    errors = 0

    # Process each active student
    students = Student.objects.filter(status='ACTIVE').select_related(
        'user', 'department__college'
    )

    for student in students:
        email = student.user.email
        if not email:
            continue

        college = student.department.college
        # Get attendance rule for this student
        try:
            rule = AttendanceRule.objects.filter(
                college=college,
                department=student.department,
                semester=student.current_semester,
            ).first() or AttendanceRule.objects.filter(
                college=college,
                department=student.department,
                semester__isnull=True,
            ).first() or AttendanceRule.objects.filter(
                college=college,
                department__isnull=True,
                semester__isnull=True,
            ).first()
        except Exception:
            continue

        if not rule:
            continue

        threshold = rule.alert_below_pct or 75

        # Calculate overall attendance
        subjects = Subject.objects.filter(
            department=student.department,
            semester=student.current_semester,
        )
        att_agg = Attendance.objects.filter(
            student=student, session__subject__in=subjects
        ).aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='PRESENT'))
        )
        total = att_agg['total'] or 0
        present = att_agg['present'] or 0

        if total < 5:  # Not enough sessions to alert
            continue

        pct = round(present / total * 100, 1)
        if pct >= threshold:
            continue

        # Calculate classes needed
        min_pct = rule.effective_min_overall
        classes_needed = None
        if pct < min_pct:
            x = (min_pct / 100 * total - present) / (1 - min_pct / 100)
            classes_needed = max(0, int(x) + (1 if x % 1 > 0 else 0))

        try:
            send_mail(
                subject=f'[{college.name}] Attendance Alert — {pct}% (Below {threshold}%)',
                message=(
                    f'Dear {student.user.get_full_name() or student.user.username},\n\n'
                    f'Your overall attendance is {pct}%, which is below the required {threshold}%.\n\n'
                    + (f'You need to attend {classes_needed} more consecutive classes to meet the minimum requirement.\n\n' if classes_needed else '')
                    + f'Please check your attendance details on the portal.\n\n'
                    f'Portal: {getattr(settings, "SITE_URL", "http://localhost:8000")}/dashboard/student/\n\n'
                    f'Regards,\n{college.name}'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            sent += 1
        except Exception as exc:
            logger.warning('Attendance alert email failed for %s: %s', student.roll_number, exc)
            errors += 1

    logger.info('send_attendance_alerts: sent=%d errors=%d', sent, errors)
    return {'sent': sent, 'errors': errors}


# ── Bulk Result Generation ────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def generate_results_bulk(self, exam_id, student_ids, triggered_by_user_id):
    """
    Compute results for a batch of students asynchronously.
    Called from exam_results view when action='compute'.
    """
    from .models import Exam, Student, Marks, ExamResult, Result, ResultVersion
    from django.contrib.auth.models import User
    from django.db import transaction
    from django.db.models import Sum

    try:
        exam = Exam.objects.select_related('college').get(pk=exam_id)
        triggered_by = User.objects.get(pk=triggered_by_user_id)
    except Exception as exc:
        logger.error('generate_results_bulk: setup failed: %s', exc)
        raise self.retry(exc=exc)

    computed = 0
    errors = 0

    for sid in student_ids:
        try:
            student = Student.objects.select_related('department').get(pk=sid)
            marks_agg = Marks.objects.filter(
                student=student, exam=exam,
                subject__semester=exam.semester,
            ).aggregate(
                total_obtained=Sum('marks_obtained'),
                total_max=Sum('max_marks'),
            )
            obtained = marks_agg['total_obtained'] or 0
            max_m = marks_agg['total_max'] or 0
            pct = round(obtained / max_m * 100, 1) if max_m > 0 else 0

            # Simple grade calculation
            if pct >= 90: grade = 'O'
            elif pct >= 80: grade = 'A+'
            elif pct >= 70: grade = 'A'
            elif pct >= 60: grade = 'B+'
            elif pct >= 50: grade = 'B'
            elif pct >= 40: grade = 'C'
            else: grade = 'F'

            is_pass = pct >= 40.0

            with transaction.atomic():
                ExamResult.objects.update_or_create(
                    student_id=sid, exam=exam,
                    defaults={
                        'total_marks_obtained': obtained,
                        'total_max_marks': max_m,
                        'percentage': pct,
                        'grade': grade,
                        'is_pass': is_pass,
                        'status': 'DRAFT',
                    }
                )
                # Compute SGPA
                marks_qs = Marks.objects.filter(
                    student=student, exam=exam,
                    subject__semester=exam.semester,
                ).select_related('subject')
                grade_points = {'O': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 'C': 5, 'F': 0}
                total_cp = sum((m.subject.credits or 0) * grade_points.get(m.grade or 'F', 0) for m in marks_qs)
                total_cr = sum(m.subject.credits or 0 for m in marks_qs)
                sgpa = round(total_cp / total_cr, 2) if total_cr > 0 else 0.0

                Result.objects.update_or_create(
                    student_id=sid, semester=exam.semester,
                    defaults={
                        'gpa': sgpa, 'sgpa': sgpa,
                        'total_marks': obtained,
                        'percentage': pct,
                        'total_credits': total_cr,
                    }
                )
            computed += 1
        except Exception as exc:
            logger.warning('generate_results_bulk: student %s failed: %s', sid, exc)
            errors += 1

    logger.info('generate_results_bulk: exam=%s computed=%d errors=%d', exam_id, computed, errors)
    return {'exam_id': exam_id, 'computed': computed, 'errors': errors}


# ── Bulk Email Notifications ──────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_bulk_announcement(self, announcement_id):
    """
    Send an announcement email to all students in the college.
    Called when admin publishes an announcement.
    """
    from .models import Announcement, Student

    try:
        ann = Announcement.objects.select_related('college').get(pk=announcement_id)
    except Announcement.DoesNotExist:
        logger.warning('send_bulk_announcement: announcement %s not found', announcement_id)
        return

    college = ann.college
    if not college:
        return  # Platform-level announcement — skip email

    students = Student.objects.filter(
        department__college=college, status='ACTIVE'
    ).select_related('user').exclude(user__email='')

    messages = []
    for student in students:
        messages.append((
            f'[{college.name}] {ann.title}',
            ann.content,
            settings.DEFAULT_FROM_EMAIL,
            [student.user.email],
        ))

    if messages:
        try:
            send_mass_mail(messages, fail_silently=True)
            logger.info('send_bulk_announcement: sent to %d students', len(messages))
        except Exception as exc:
            logger.error('send_bulk_announcement: failed: %s', exc)
            raise self.retry(exc=exc)

    return {'sent': len(messages)}
