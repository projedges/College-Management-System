import csv
from collections import defaultdict
from datetime import datetime, timedelta, time as dt_time
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Q, Count, F, ExpressionWrapper, FloatField
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse
from ..models import (
    UserRole, College, Student, Faculty, Department, HOD, Principal,
    Fee, Announcement, ActivityLog, Attendance, AttendanceSession,
    Subject, FacultySubject, Timetable, Result, Marks, Exam,
    Assignment, AssignmentSubmission, HODApproval, FacultyPerformance,
    Payment, SystemReport, StudentProfile, Address, Parent, Notification, Substitution,
    EmergencyContact, UserSecurity, RegistrationRequest, TicketComment,
    RegistrationInvite, HelpDeskTicket, FacultyAvailability, Classroom, FeeStructure,
    Quiz, QuizQuestion, QuizOption, QuizAttempt, QuizAnswer, InternalMark,
    LessonPlan, LeaveApplication, CollegeBranding,
    ExamController, ExamType, ExamSchedule, HallTicket, ExamResult, RevaluationRequest,
    ExamStaff, EvaluationScheme, ValuationAssignment, ExamStaffLog,
    AttendanceRule, AttendanceExemption, AttendanceCorrection, EligibilityOverride,
    FeeBreakdown, SupplyExamRegistration, TimetableBreak,
    Regulation, CurriculumEntry, ElectivePool, ElectiveSelection,
    Section, SectionSubjectFacultyMap,
    AuditLog, FeeInstallmentPlan, FeeInstallment, LateFeeRule, FeeWaiver,
    GraceMarksRule, GraceMarksApplication,
    StudentRegulation, RegulationMigration, SubjectSchemeOverride,
    ResultVersion, ResultFreeze, MarksModeration,
    ExamEligibilityConfig, StudentLifecycleEvent, DisciplinaryRecord,
    ElectiveWaitlist, CollegeFeatureConfig,
)

# --- Helpers for Performance and Validation ---

def super_admin_required(view_func):
    """Decorator for views that checks that the user is a superuser."""
    actual_decorator = user_passes_test(lambda u: u.is_superuser, login_url='super_admin_login')
    return actual_decorator(view_func)

def _safe_int(val, default=0):
    try: return int(val)
    except (ValueError, TypeError): return default

def _safe_float(val, default=0.0):
    try: return float(val)
    except (ValueError, TypeError): return default

def _get_college_branding(college):
    """Returns CollegeBranding for a college, creating defaults if not set."""
    if not college:
        return None
    branding, _ = CollegeBranding.objects.get_or_create(college=college)
    return branding

# ----------------------------------------------


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # Get the real client IP, ignoring proxy hops
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def _get_or_create_security(user):
    security, _ = UserSecurity.objects.get_or_create(user=user)
    return security


def _check_timetable_conflict(day, start, end, faculty=None, classroom=None, ignore_id=None):
    """Utility to prevent overlapping slots for faculty or rooms."""
    qs = Timetable.objects.filter(day_of_week=day)
    if ignore_id:
        qs = qs.exclude(id=ignore_id)

    # Check for time overlap: (StartA < EndB) and (EndA > StartB)
    overlap_qs = qs.filter(Q(start_time__lt=end, end_time__gt=start))

    if faculty and overlap_qs.filter(faculty=faculty).exists():
        return True, f"Conflict: {faculty.user.get_full_name()} is already teaching during this time."
    
    if classroom and overlap_qs.filter(classroom=classroom).exists():
        return True, f"Conflict: Room {classroom.room_number} is occupied during this time."
    
    return False, ""


def _check_attendance_permission(user, subject, slot=None):
    """
    Checks if a user has permission to mark attendance for a subject.
    In DEBUG mode the time-lock is relaxed so testing is possible.
    """
    from django.conf import settings
    role = getattr(user, 'userrole', None)
    if not role: return False, "No role assigned."
    if user.is_superuser: return True, ""

    # HOD Override: HODs can mark for any subject in their department
    if role.role == 2 and hasattr(user, 'hod') and user.hod.department == subject.department:
        return True, ""

    # Faculty / Substitute Logic
    if role.role in (2, 3) and hasattr(user, 'faculty'):
        # Check direct assignment
        is_assigned = FacultySubject.objects.filter(faculty=user.faculty, subject=subject).exists()

        # Check substitution for today
        now = timezone.localtime(timezone.now())
        today_day = {0:'MON',1:'TUE',2:'WED',3:'THU',4:'FRI',5:'SAT',6:'SUN'}.get(now.weekday())
        if not slot:
            slot = Timetable.objects.filter(subject=subject, day_of_week=today_day).first()

        is_sub = False
        if slot:
            is_sub = Substitution.objects.filter(
                timetable_slot=slot, substitute_faculty=user.faculty, date=now.date()
            ).exists()

        if not (is_assigned or is_sub):
            return False, "You are not assigned to this subject."

        # Production: enforce time window (relaxed only in test environments via env var)
        import os
        if os.environ.get('ATTENDANCE_TIME_LOCK_DISABLED') == '1':
            return True, ""

        # Enforce time window
        if not slot:
            return False, "No timetable slot found for this subject today."

        end_dt = timezone.make_aware(datetime.combine(now.date(), slot.end_time))
        marking_end = end_dt + timedelta(minutes=10)
        edit_end    = end_dt + timedelta(minutes=60)

        if slot.start_time <= now.time() <= marking_end.time():
            return True, ""
        if now > marking_end and now <= edit_end:
            return True, "Editing window: up to 60 min after class."
        return False, f"Attendance locked. Window: {slot.start_time}–{slot.end_time} (+10 min grace)."

    return False, "Unauthorized."


def _sync_fee_status(fee):
    if fee.paid_amount >= fee.total_amount:
        fee.status = "PAID"
    elif fee.paid_amount > 0:
        fee.status = "PARTIAL"
    else:
        fee.status = "PENDING"
    return fee


def _audit(action_type, performed_by, description, student=None, faculty=None,
           college=None, old_value='', new_value='', request=None):
    """Create an AuditLog entry. Never raises — audit failures must not break flows."""
    try:
        ip = None
        if request:
            x_fwd = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_fwd.split(',')[0].strip() if x_fwd else request.META.get('REMOTE_ADDR')
        AuditLog.objects.create(
            action_type=action_type,
            performed_by=performed_by,
            student=student,
            faculty=faculty,
            college=college,
            description=description,
            old_value=str(old_value),
            new_value=str(new_value),
            ip_address=ip,
        )
    except Exception:
        pass


def _assignment_deadline_from_input(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _pdf_escape(value):
    return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _generate_temporary_password():
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#$%!'
    return get_random_string(14, allowed_chars=alphabet)


def _resolve_password(raw_password):
    password = (raw_password or '').strip()
    if password:
        return password, False
    return _generate_temporary_password(), True


# ── PDF BUILDER (reportlab) ───────────────────────────────────────────────────

def _get_pdf_styles():
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    styles = getSampleStyleSheet()
    PRIMARY = colors.HexColor('#0d7377')
    DARK    = colors.HexColor('#071e26')
    MUTED   = colors.HexColor('#64748b')
    styles.add(ParagraphStyle('CollegeName',  fontName='Helvetica-Bold',   fontSize=16, textColor=colors.white,      spaceAfter=2,  leading=20))
    styles.add(ParagraphStyle('Tagline',      fontName='Helvetica',        fontSize=9,  textColor=colors.HexColor('#cce8e9'), spaceAfter=0))
    styles.add(ParagraphStyle('DocTitle',     fontName='Helvetica-Bold',   fontSize=13, textColor=colors.white,      spaceAfter=0,  alignment=TA_RIGHT))
    styles.add(ParagraphStyle('DocSubtitle',  fontName='Helvetica',        fontSize=8,  textColor=colors.HexColor('#cce8e9'), spaceAfter=0, alignment=TA_RIGHT))
    styles.add(ParagraphStyle('SectionHead',  fontName='Helvetica-Bold',   fontSize=8,  textColor=PRIMARY,           spaceAfter=4,  spaceBefore=10, leading=10))
    styles.add(ParagraphStyle('FieldLabel',   fontName='Helvetica',        fontSize=8,  textColor=MUTED,             spaceAfter=1))
    styles.add(ParagraphStyle('FieldValue',   fontName='Helvetica-Bold',   fontSize=9,  textColor=DARK,              spaceAfter=4))
    styles.add(ParagraphStyle('TableHeader',  fontName='Helvetica-Bold',   fontSize=8,  textColor=colors.white))
    styles.add(ParagraphStyle('TableCell',    fontName='Helvetica',        fontSize=8,  textColor=DARK))
    styles.add(ParagraphStyle('Footer',       fontName='Helvetica',        fontSize=7,  textColor=MUTED,             alignment=TA_CENTER))
    styles.add(ParagraphStyle('AmountBig',    fontName='Helvetica-Bold',   fontSize=18, textColor=PRIMARY))
    styles.add(ParagraphStyle('StatusBadge',  fontName='Helvetica-Bold',   fontSize=9,  textColor=colors.white,      alignment=TA_CENTER))
    styles.add(ParagraphStyle('Normal8',      fontName='Helvetica',        fontSize=8,  textColor=DARK,              spaceAfter=3))
    return styles, PRIMARY, DARK, MUTED


def _build_pdf_header(elements, college, doc_title, doc_subtitle='', styles=None, PRIMARY=None):
    """Renders the teal header band with college name and document title."""
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.units import mm

    if styles is None:
        styles, PRIMARY, _, _ = _get_pdf_styles()
    if PRIMARY is None:
        PRIMARY = colors.HexColor('#0d7377')

    college_name = college.name if college else 'EduTrack'
    tagline = ''
    if college:
        try:
            tagline = college.branding.tagline or ''
        except Exception:
            pass
    city_state = ''
    if college and college.city:
        city_state = college.city + (f', {college.state}' if college.state else '')

    left_cell = [
        Paragraph(college_name, styles['CollegeName']),
    ]
    if tagline:
        left_cell.append(Paragraph(tagline, styles['Tagline']))
    if city_state:
        left_cell.append(Paragraph(city_state, styles['Tagline']))

    right_cell = [
        Paragraph(doc_title, styles['DocTitle']),
        Paragraph(doc_subtitle, styles['DocSubtitle']),
    ]

    header_table = Table([[left_cell, right_cell]], colWidths=['60%', '40%'])
    header_table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), PRIMARY),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING',   (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 14),
        ('ROUNDEDCORNERS', [6, 6, 0, 0]),
    ]))
    elements.append(header_table)


def _build_pdf_footer_note(elements, college, styles, note=''):
    from reportlab.platypus import Paragraph, HRFlowable
    from reportlab.lib import colors
    elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceAfter=6, spaceBefore=10))
    footer_text = note or 'This is a computer-generated document and does not require a physical signature.'
    if college and college.email:
        footer_text += f'  |  {college.email}'
    elements.append(Paragraph(footer_text, styles['Footer']))


def _pdf_response(filename, title, lines, generated_by=None, report_type=None, college=None):
    """Legacy plain-text PDF — kept for backward compat but now uses reportlab."""
    from io import BytesIO
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors

    styles, PRIMARY, DARK, MUTED = _get_pdf_styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=10*mm, bottomMargin=15*mm)
    elements = []
    _build_pdf_header(elements, college, title, styles=styles, PRIMARY=PRIMARY)
    elements.append(Spacer(1, 8))

    for line in lines:
        if not line.strip():
            elements.append(Spacer(1, 4))
        elif line.startswith('  '):
            elements.append(Paragraph(f'&nbsp;&nbsp;&nbsp;{line.strip()}', styles['Normal8']))
        else:
            elements.append(Paragraph(line, styles['Normal8']))

    _build_pdf_footer_note(elements, college, styles)
    doc.build(elements)
    payload = buf.getvalue()

    if generated_by and report_type in {'ATTENDANCE', 'RESULT', 'PAYMENT'}:
        from django.core.files.base import ContentFile
        report = SystemReport(report_type=report_type, generated_by=generated_by)
        report.file.save(filename, ContentFile(payload), save=True)

    response = HttpResponse(payload, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _default_college():
    return College.objects.order_by("id").first()


def _get_registration_invite(token):
    if not token:
        return None
    invite = RegistrationInvite.objects.select_related('college', 'department').filter(token=token).first()
    if invite and invite.is_usable:
        return invite
    return None


def _build_registration_invite_url(request, invite):
    return request.build_absolute_uri(f"{reverse('register')}?token={invite.token}")


REGISTRATION_ACTIVE_STATUSES = {'SUBMITTED', 'UNDER_REVIEW', 'NEEDS_CORRECTION', 'APPROVED'}
REGISTRATION_CONVERTIBLE_STATUSES = {'APPROVED'}
SECTION_LABEL_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def _deliver_registration_request_update(reg_request, subject, body, user=None):
    from django.conf import settings
    from django.core.mail import send_mail

    recipient_email = (reg_request.email or '').strip()
    if recipient_email:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient_email], fail_silently=True)

    notification_user = user
    if notification_user is None and recipient_email:
        notification_user = User.objects.filter(email__iexact=recipient_email).order_by('id').first()
    if notification_user:
        Notification.objects.create(user=notification_user, message=body)


def _notify_registration_request_submitted(reg_request):
    college_name = reg_request.college.name if reg_request.college else 'the college'
    dept_name = reg_request.desired_department.name if reg_request.desired_department else 'the selected department'
    body = (
        f"Your registration request for {college_name} has been received for {dept_name}. "
        "The admissions team will review it and contact you if corrections are needed."
    )
    _deliver_registration_request_update(reg_request, f"{college_name} registration request received", body)


def _notify_registration_request_status(reg_request):
    college_name = reg_request.college.name if reg_request.college else 'the college'
    status_messages = {
        'UNDER_REVIEW': (
            f"Your registration request for {college_name} is now under review."
            + (f" Note: {reg_request.review_notes}" if reg_request.review_notes else "")
        ),
        'NEEDS_CORRECTION': (
            f"Your registration request for {college_name} needs correction."
            f" Please review the requested updates: {reg_request.correction_fields}"
            + (f" Note: {reg_request.review_notes}" if reg_request.review_notes else "")
        ),
        'APPROVED': (
            f"Your registration request for {college_name} has been approved."
            " The admissions team can now convert it into a student account."
            + (f" Note: {reg_request.review_notes}" if reg_request.review_notes else "")
        ),
        'REJECTED': (
            f"Your registration request for {college_name} has been rejected."
            + (f" Note: {reg_request.review_notes}" if reg_request.review_notes else "")
        ),
    }
    body = status_messages.get(reg_request.status)
    if body:
        _deliver_registration_request_update(
            reg_request,
            f"{college_name} registration request {reg_request.get_status_display().lower()}",
            body,
        )


def _notify_registration_request_converted(reg_request, user, password_generated=False, password_value=''):
    college_name = reg_request.college.name if reg_request.college else 'the college'
    body = (
        f"Your student account for {college_name} has been created. "
        f"Username: {user.username}."
    )
    if password_generated and password_value:
        body += f" Temporary password: {password_value}."
    body += " Please sign in and update your password after your first login."
    _deliver_registration_request_update(
        reg_request,
        f"{college_name} student account created",
        body,
        user=user,
    )


def _section_label_for_index(index):
    index = max(index, 0)
    label = ''
    while True:
        index, remainder = divmod(index, 26)
        label = SECTION_LABEL_ALPHABET[remainder] + label
        if index == 0:
            break
        index -= 1
    return label


def _determine_student_section(department, admission_year):
    capacity = max(getattr(department, 'section_capacity', 60) or 60, 1)
    existing_count = Student.objects.filter(
        department=department,
        admission_year=admission_year,
        is_deleted=False,
    ).count()
    return _section_label_for_index(existing_count // capacity)


def _build_weekly_timetable_matrix(entries, breaks=None, days=None):
    days = days or [('MON', 'Monday'), ('TUE', 'Tuesday'), ('WED', 'Wednesday'), ('THU', 'Thursday'), ('FRI', 'Friday'), ('SAT', 'Saturday')]
    slot_map = defaultdict(lambda: {'entries': [], 'break_label': ''})
    slot_times = set()

    for entry in entries:
        key = (entry.day_of_week, entry.start_time, entry.end_time)
        slot_map[key]['entries'].append(entry)
        slot_times.add((entry.start_time, entry.end_time))

    for brk in breaks or []:
        key = (brk.day_of_week, brk.start_time, brk.end_time)
        slot_map[key]['break_label'] = brk.label
        slot_times.add((brk.start_time, brk.end_time))

    ordered_times = sorted(slot_times, key=lambda item: (item[0], item[1]))
    rows = []
    for start_time, end_time in ordered_times:
        row = {
            'label': f"{start_time.strftime('%I:%M %p').lstrip('0')} - {end_time.strftime('%I:%M %p').lstrip('0')}",
            'cells': [],
        }
        row_is_break = True
        for day_code, day_label in days:
            cell = slot_map.get((day_code, start_time, end_time), {'entries': [], 'break_label': ''})
            if cell['entries']:
                row_is_break = False
            row['cells'].append({
                'day_code': day_code,
                'day_label': day_label,
                'entries': cell['entries'],
                'break_label': cell['break_label'],
            })
        row['is_break_row'] = row_is_break and any(cell['break_label'] for cell in row['cells'])
        rows.append(row)
    return rows


def _generate_roll_number(department, admission_year):
    college = department.college
    rule = getattr(college, 'student_id_rule', '{YEAR}-{CODE}-{DEPT}-{SERIAL}')

    prefix_template = rule.split('{SERIAL}')[0]
    prefix = prefix_template.format(
        YEAR=str(admission_year),
        CODE=college.code.upper(),
        DEPT=department.code.upper()
    )

    # Scope to this college only to prevent cross-college serial collisions
    latest_roll = (
        Student.objects.filter(
            roll_number__startswith=prefix,
            department__college=college
        )
        .order_by('-roll_number')
        .values_list('roll_number', flat=True)
        .first()
    )

    next_serial = 1
    if latest_roll:
        try:
            serial_str = latest_roll[len(prefix):].split('-')[0].split('/')[0]
            next_serial = int(serial_str) + 1
        except (TypeError, ValueError):
            next_serial = Student.objects.filter(
                roll_number__startswith=prefix,
                department__college=college
            ).count() + 1

    return rule.format(
        YEAR=str(admission_year),
        CODE=college.code.upper(),
        DEPT=department.code.upper(),
        SERIAL=f"{next_serial:03d}"
    )

def _generate_faculty_id(department):
    college = department.college
    rule = getattr(college, 'faculty_id_rule', 'FAC-{CODE}-{SERIAL}')
    count = Faculty.objects.filter(department__college=college).count() + 1
    return rule.format(
        CODE=college.code.upper(),
        DEPT=department.code.upper(),
        SERIAL=f"{count:03d}"
    )


def _create_default_fee(student):
    """Automates fee record creation upon student onboarding — one record per semester."""
    from datetime import date as _date
    structure = FeeStructure.objects.filter(
        department=student.department,
        semester=student.current_semester
    ).first()
    total = structure.total_fees if structure else 50000.0
    # Academic year: e.g. admission 2022, sem 1 → "2022-23", sem 3 → "2023-24"
    year_offset = (student.current_semester - 1) // 2
    start_year = student.admission_year + year_offset
    academic_year = f"{start_year}-{str(start_year + 1)[-2:]}"
    Fee.objects.get_or_create(
        student=student,
        semester=student.current_semester,
        defaults={
            'total_amount': total,
            'paid_amount': 0.0,
            'status': 'PENDING',
            'academic_year': academic_year,
        }
    )


def _student_result_breakdown(student):
    results = Result.objects.filter(student=student).order_by('semester')
    marks = (
        Marks.objects.filter(student=student)
        .select_related('subject', 'exam')
        .order_by('subject__semester', 'subject__name')
    )

    # Group marks by subject's semester (most reliable — subject always has a semester)
    marks_by_semester = {}
    for mark in marks:
        # Use subject.semester as the primary key — it's always set
        semester = mark.subject.semester
        marks_by_semester.setdefault(semester, []).append(mark)

    # Build breakdown: one entry per semester that has either a Result or Marks
    result_by_sem = {r.semester: r for r in results}
    all_semesters = sorted(set(list(result_by_sem.keys()) + list(marks_by_semester.keys())))

    breakdown = []
    for semester in all_semesters:
        result = result_by_sem.get(semester)
        sem_marks = marks_by_semester.get(semester, [])
        breakdown.append({
            'result': result,
            'semester': semester,
            'marks': sem_marks,
        })

    return breakdown, results


def _scope_helpdesk_tickets(request):
    college = _get_admin_college(request)
    qs = HelpDeskTicket.objects.select_related('college', 'submitted_by').order_by('-created_at')
    if request.user.is_superuser or college is None:
        return qs
    return qs.filter(Q(college=college) | Q(college__isnull=True))


def _auto_generate_timetable(department, semester):
    """
    Real-college timetable generator — section-aware, L-T-P-C aware, conflict-free.

    Logic:
    - Each FacultySubject assignment = one section of that subject.
      If a subject has 2 faculty assigned → Section A and Section B.
    - Lecture slots (L) are scheduled Mon–Fri, 1 hr each.
    - Tutorial slots (T) are scheduled separately (usually 1 hr/week).
    - Practical slots (P) are scheduled as 2-hr lab blocks.
    - Faculty and room conflicts are checked across the ENTIRE college (not just dept).
    - Existing timetable for this dept+semester is cleared before regeneration.
    """
    from datetime import time as dt_time

    subjects = list(Subject.objects.filter(department=department, semester=semester).order_by('name'))
    if not subjects:
        return 0

    # Group faculty assignments per subject → determines sections
    # subject_id → list of Faculty (each = one section)
    assignments_qs = (
        FacultySubject.objects
        .filter(subject__in=subjects)
        .select_related('faculty__user', 'subject')
        .order_by('subject__name', 'faculty__user__first_name')
    )
    subject_faculty_map = {}  # subject_id → [Faculty, ...]
    for fa in assignments_qs:
        subject_faculty_map.setdefault(fa.subject_id, []).append(fa.faculty)

    if not subject_faculty_map:
        return 0

    # Classrooms
    classrooms = list(Classroom.objects.filter(college=department.college).order_by('room_number'))
    if not classrooms:
        classrooms = [Classroom.objects.create(
            college=department.college, room_number=f"{department.code}-101", capacity=60
        )]

    # Faculty availability (optional — fall back to default grid if not set)
    all_faculty_ids = [f.id for flist in subject_faculty_map.values() for f in flist]
    avail_qs = FacultyAvailability.objects.filter(
        faculty_id__in=all_faculty_ids, is_available=True
    ).order_by('day_of_week', 'start_time')
    avail_map = {}  # faculty_id → [(day, start, end), ...]
    for av in avail_qs:
        avail_map.setdefault(av.faculty_id, []).append((av.day_of_week, av.start_time, av.end_time))

    # Standard college time grid (1-hr lecture slots, 2-hr lab slots)
    LECTURE_GRID = [
        ('MON', dt_time(9, 0),  dt_time(10, 0)),
        ('MON', dt_time(10, 0), dt_time(11, 0)),
        ('MON', dt_time(11, 0), dt_time(12, 0)),
        ('MON', dt_time(14, 0), dt_time(15, 0)),
        ('MON', dt_time(15, 0), dt_time(16, 0)),
        ('TUE', dt_time(9, 0),  dt_time(10, 0)),
        ('TUE', dt_time(10, 0), dt_time(11, 0)),
        ('TUE', dt_time(11, 0), dt_time(12, 0)),
        ('TUE', dt_time(14, 0), dt_time(15, 0)),
        ('TUE', dt_time(15, 0), dt_time(16, 0)),
        ('WED', dt_time(9, 0),  dt_time(10, 0)),
        ('WED', dt_time(10, 0), dt_time(11, 0)),
        ('WED', dt_time(11, 0), dt_time(12, 0)),
        ('WED', dt_time(14, 0), dt_time(15, 0)),
        ('THU', dt_time(9, 0),  dt_time(10, 0)),
        ('THU', dt_time(10, 0), dt_time(11, 0)),
        ('THU', dt_time(11, 0), dt_time(12, 0)),
        ('THU', dt_time(14, 0), dt_time(15, 0)),
        ('FRI', dt_time(9, 0),  dt_time(10, 0)),
        ('FRI', dt_time(10, 0), dt_time(11, 0)),
        ('FRI', dt_time(11, 0), dt_time(12, 0)),
        ('FRI', dt_time(14, 0), dt_time(15, 0)),
        ('SAT', dt_time(9, 0),  dt_time(10, 0)),
        ('SAT', dt_time(10, 0), dt_time(11, 0)),
    ]
    LAB_PAIRS = []
    for _day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
        _s1 = dt_time(14, 0);  _e1 = dt_time(14, 50)
        _s2 = dt_time(14, 50); _e2 = dt_time(15, 40)
        LAB_PAIRS.append((_day, _s1, _e1, _s2, _e2))

    # Clear existing timetable for this dept+semester
    Timetable.objects.filter(subject__department=department, subject__semester=semester).delete()

    # Conflict tracking — college-wide (faculty can't be in two places, room can't be double-booked)
    used_faculty: set = set()   # (faculty_id, day, start_time)
    used_rooms: set   = set()   # (room_id, day, start_time)

    # Pre-load existing conflicts from OTHER dept/semesters in same college
    existing = Timetable.objects.filter(
        subject__department__college=department.college
    ).exclude(
        subject__department=department, subject__semester=semester
    ).values_list('faculty_id', 'classroom_id', 'day_of_week', 'start_time')
    for fac_id, room_id, day, start in existing:
        used_faculty.add((fac_id, day, start))
        used_rooms.add((room_id, day, start))

    created_count = 0
    section_labels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    for subj in subjects:
        faculty_list_for_subj = subject_faculty_map.get(subj.id, [])
        if not faculty_list_for_subj:
            continue

        # Determine how many lecture, tutorial, practical slots needed
        L = max(subj.lecture_hours, 1)   # at least 1 lecture/week
        T = subj.tutorial_hours          # 0 or 1
        P = subj.practical_hours         # 0, 2, or 3

        for sec_idx, faculty in enumerate(faculty_list_for_subj):
            section = section_labels[sec_idx] if len(faculty_list_for_subj) > 1 else ''
            fac_avail = avail_map.get(faculty.id)

            # --- Schedule L lecture slots ---
            lecture_candidates = fac_avail if fac_avail else LECTURE_GRID
            lectures_placed = 0
            room_idx = sec_idx  # stagger sections across rooms

            for day, start, end in lecture_candidates:
                if lectures_placed >= L:
                    break
                fkey = (faculty.id, day, start)
                if fkey in used_faculty:
                    continue
                # Pick a room not already used at this slot
                room = None
                for ri in range(len(classrooms)):
                    candidate = classrooms[(room_idx + ri) % len(classrooms)]
                    rkey = (candidate.id, day, start)
                    if rkey not in used_rooms:
                        room = candidate
                        break
                if not room:
                    continue
                rkey = (room.id, day, start)
                Timetable.objects.create(
                    subject=subj, faculty=faculty,
                    day_of_week=day, start_time=start, end_time=end,
                    classroom=room, section=section,
                )
                used_faculty.add(fkey)
                used_rooms.add(rkey)
                lectures_placed += 1
                created_count += 1

            # --- Schedule T tutorial slot (1 hr) ---
            if T > 0:
                for day, start, end in (fac_avail or LECTURE_GRID):
                    fkey = (faculty.id, day, start)
                    if fkey in used_faculty:
                        continue
                    room = None
                    for ri in range(len(classrooms)):
                        candidate = classrooms[(room_idx + ri) % len(classrooms)]
                        rkey = (candidate.id, day, start)
                        if rkey not in used_rooms:
                            room = candidate
                            break
                    if not room:
                        continue
                    rkey = (room.id, day, start)
                    Timetable.objects.create(
                        subject=subj, faculty=faculty,
                        day_of_week=day, start_time=start, end_time=end,
                        classroom=room, section=section,
                    )
                    used_faculty.add(fkey)
                    used_rooms.add(rkey)
                    created_count += 1
                    break

            # --- Schedule P practical slot (2 consecutive 50-min rows) ---
            if P > 0:
                for _day, _s1, _e1, _s2, _e2 in LAB_PAIRS:
                    fkey1 = (faculty.id, _day, _s1)
                    fkey2 = (faculty.id, _day, _s2)
                    if fkey1 in used_faculty or fkey2 in used_faculty:
                        continue
                    room = None
                    for ri in range(len(classrooms)):
                        candidate = classrooms[(room_idx + ri) % len(classrooms)]
                        if (candidate.id, _day, _s1) not in used_rooms and (candidate.id, _day, _s2) not in used_rooms:
                            room = candidate
                            break
                    if not room:
                        continue
                    for _s, _e in [(_s1, _e1), (_s2, _e2)]:
                        Timetable.objects.create(
                            subject=subj, faculty=faculty,
                            day_of_week=_day, start_time=_s, end_time=_e,
                            classroom=room, section=section,
                        )
                        used_faculty.add((faculty.id, _day, _s))
                        used_rooms.add((room.id, _day, _s))
                        created_count += 1
                    break

    return created_count


def _get_user_role(user):
    try:
        return user.userrole
    except UserRole.DoesNotExist:
        return None


def _get_user_college(user):
    role = _get_user_role(user)
    if role and role.college:
        return role.college
    if hasattr(user, "principal"):
        return user.principal.college
    if hasattr(user, "hod"):
        return user.hod.department.college
    if hasattr(user, "faculty"):
        return user.faculty.department.college
    if hasattr(user, "student"):
        return user.student.department.college
    return _default_college()


def _get_admin_college(request):
    if request.user.is_superuser:
        return None
    role = _get_user_role(request.user)
    if not role or role.role != 1:
        return None
    return role.college or _default_college()


def _scope_departments(request, queryset=None):
    queryset = queryset or Department.objects.all()
    college = _get_admin_college(request)
    if request.user.is_superuser or college is None:
        return queryset
    return queryset.filter(college=college)


def _scope_announcements_for_college(college):
    if college:
        return Announcement.objects.filter(Q(college=college) | Q(college__isnull=True))
    return Announcement.objects.all()


def _scope_exams(request, queryset=None):
    queryset = queryset or Exam.objects.all()
    college = _get_admin_college(request)
    if request.user.is_superuser or college is None:
        return queryset
    return queryset.filter(Q(college=college) | Q(college__isnull=True))


# ── ATTENDANCE RULE ENGINE ────────────────────────────────────────────────────

def _get_attendance_rule(college, department=None, semester=None):
    """
    Returns the most specific AttendanceRule for the given context.
    Precedence: dept+sem > dept only > college-wide.
    Falls back to a default rule (75%) if none configured.
    """
    qs = AttendanceRule.objects.filter(college=college, is_active=True)

    # Most specific: dept + semester
    if department and semester:
        rule = qs.filter(department=department, semester=semester).first()
        if rule:
            return rule

    # Dept-level (any semester)
    if department:
        rule = qs.filter(department=department, semester__isnull=True).first()
        if rule:
            return rule

    # College-wide fallback
    rule = qs.filter(department__isnull=True, semester__isnull=True).first()
    if rule:
        return rule

    # Absolute fallback — default 75% rule (not saved to DB)
    default = AttendanceRule(
        college=college,
        min_overall_pct=75.0,
        min_subject_pct=75.0,
        require_both=True,
        grace_pct=0.0,
        min_sessions_for_check=5,
        alert_below_pct=75.0,
        critical_below_pct=65.0,
    )
    return default


def _compute_eligibility(student, semester, college, exam=None):
    """
    Single source of truth for attendance eligibility.
    Returns a dict with:
      - eligible: bool
      - overall_pct: float
      - subject_breakdown: list of {subject, present, total, pct, meets_threshold, is_mandatory}
      - rule: AttendanceRule used
      - reasons: list of human-readable failure reasons
      - has_override: bool (approved override exists)
      - exempted_days: int
    """
    rule = _get_attendance_rule(college, student.department, semester)

    # Check for approved override
    has_override = False
    if exam:
        has_override = EligibilityOverride.objects.filter(
            student=student, exam=exam, status='APPROVED'
        ).exists()
        if has_override:
            return {
                'eligible': True, 'overall_pct': None,
                'subject_breakdown': [], 'rule': rule,
                'reasons': ['Manually approved by authority'],
                'has_override': True, 'exempted_days': 0,
            }

    # Approved exemptions for this student this semester
    exempted_sessions = set()
    if rule.allow_medical_exemption or rule.allow_sports_exemption or rule.allow_od_exemption:
        allowed_types = []
        if rule.allow_medical_exemption: allowed_types.append('MEDICAL')
        if rule.allow_sports_exemption:  allowed_types.append('SPORTS')
        if rule.allow_od_exemption:      allowed_types.append('OD')
        allowed_types.append('OTHER')

        exemptions = AttendanceExemption.objects.filter(
            student=student, status='APPROVED', reason_type__in=allowed_types
        )
        # Get all session IDs that fall within exemption date ranges
        for ex in exemptions:
            sess_ids = AttendanceSession.objects.filter(
                subject__department=student.department,
                subject__semester=semester,
                date__gte=ex.from_date,
                date__lte=ex.to_date,
            ).values_list('id', flat=True)
            exempted_sessions.update(sess_ids)

    # Bulk-fetch attendance per subject
    subjects = Subject.objects.filter(department=student.department, semester=semester)
    att_agg = Attendance.objects.filter(
        student=student,
        session__subject__in=subjects,
    ).exclude(
        session_id__in=exempted_sessions
    ).values('session__subject_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    att_by_subj = {row['session__subject_id']: row for row in att_agg}

    # Also get total sessions per subject (excluding exempted)
    sess_agg = AttendanceSession.objects.filter(
        subject__in=subjects
    ).exclude(
        id__in=exempted_sessions
    ).values('subject_id').annotate(count=Count('id'))
    sess_by_subj = {row['subject_id']: row['count'] for row in sess_agg}

    subject_breakdown = []
    overall_present = 0
    overall_total = 0
    reasons = []

    for subj in subjects:
        agg = att_by_subj.get(subj.id, {'total': 0, 'present': 0})
        total_sessions = sess_by_subj.get(subj.id, 0)
        present = agg['present']
        total = agg['total']
        pct = round(present / total * 100, 1) if total > 0 else 0

        # ALWAYS add to the overall totals, regardless of skipping
        overall_present += present
        overall_total += total
        
        # Skip subjects with too few sessions
        if total_sessions < rule.min_sessions_for_check:
            subject_breakdown.append({
                'subject': subj, 'present': present, 'total': total,
                'pct': pct, 'meets_threshold': True,
                'skipped': True, 'sessions_conducted': total_sessions,
            })
            continue

        threshold = rule.effective_min_subject
        meets = pct >= threshold or total == 0

        if not meets:
            reasons.append(f"{subj.name}: {pct}% < {threshold}% required")

        subject_breakdown.append({
            'subject': subj, 'present': present, 'total': total,
            'pct': pct, 'meets_threshold': meets,
            'skipped': False, 'sessions_conducted': total_sessions,
            'threshold': threshold,
        })
        overall_present += present
        overall_total += total

    overall_pct = round(overall_present / overall_total * 100, 1) if overall_total > 0 else 0
    overall_meets = overall_pct >= rule.effective_min_overall or overall_total == 0

    if not overall_meets:
        reasons.insert(0, f"Overall: {overall_pct}% < {rule.effective_min_overall}% required")

    subject_fails = [s for s in subject_breakdown if not s.get('skipped') and not s['meets_threshold']]

    if rule.require_both:
        eligible = overall_meets and len(subject_fails) == 0
    else:
        eligible = overall_meets or len(subject_fails) == 0

    return {
        'eligible': eligible,
        'overall_pct': overall_pct,
        'overall_meets': overall_meets,
        'subject_breakdown': subject_breakdown,
        'subject_fails': subject_fails,
        'rule': rule,
        'reasons': reasons,
        'has_override': has_override,
        'exempted_sessions': len(exempted_sessions),
    }


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    platform_announcements = Announcement.objects.filter(college__isnull=True).order_by('-created_at')[:5]
    stats = {
        'colleges': College.objects.filter(is_active=True).count(),
        'students': Student.objects.filter(is_deleted=False).count(),
        'faculty':  Faculty.objects.count(),
        'departments': Department.objects.filter(is_deleted=False).count(),
    }
    return render(request, "home.html", {
        'platform_announcements': platform_announcements,
        'stats': stats,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    # Show a friendly message when the session timed out.
    if request.GET.get("timeout"):
        messages.warning(request, "Your session expired due to inactivity. Please sign in again.")

    # Generate math captcha
    import random as _random
    if request.method != 'POST':
        a, b = _random.randint(1, 9), _random.randint(1, 9)
        request.session['captcha_answer'] = a + b
        request.session['captcha_q'] = f"{a} + {b}"

    captcha_q = request.session.get('captcha_q', '? + ?')

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        remember_me = request.POST.get("remember_me")
        captcha_input = request.POST.get("captcha", "").strip()

        # Validate captcha first
        try:
            captcha_valid = int(captcha_input) == request.session.get('captcha_answer')
        except (ValueError, TypeError):
            captcha_valid = False

        if not captcha_valid:
            # Regenerate captcha on failure
            a, b = _random.randint(1, 9), _random.randint(1, 9)
            request.session['captcha_answer'] = a + b
            request.session['captcha_q'] = f"{a} + {b}"
            captcha_q = request.session['captcha_q']
            messages.error(request, "Incorrect answer. Please try again.")
            return render(request, "auth/login.html", {'captcha_q': captcha_q})

        existing_user = User.objects.filter(username=username).first()

        # Check lockout BEFORE attempting authentication
        if existing_user is not None:
            security = _get_or_create_security(existing_user)
            if security.login_attempts >= 5:
                # Check if lockout window (15 min) has passed
                from django.utils import timezone as _tz
                lockout_until = security.locked_until if hasattr(security, 'locked_until') and security.locked_until else None
                if lockout_until and _tz.now() < lockout_until:
                    remaining = int((lockout_until - _tz.now()).total_seconds() / 60) + 1
                    messages.error(request, f"Account temporarily locked due to too many failed attempts. Try again in {remaining} minute(s).")
                    return render(request, "auth/login.html", {'captcha_q': captcha_q})
                elif not lockout_until:
                    # Legacy: no locked_until field, just block if >= 5 attempts
                    messages.error(request, "Account temporarily locked. Contact your admin to reset.")
                    return render(request, "auth/login.html", {'captcha_q': captcha_q})

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            # Super admins must use the dedicated login page
            messages.error(request, "Please use the admin portal to sign in.")
            user = None
        if user is not None:
            login(request, user)

            if remember_me:
                from django.conf import settings as _s
                request.session.set_expiry(_s.SESSION_COOKIE_AGE)
            else:
                request.session.set_expiry(0)

            import time as _time
            request.session['_last_activity'] = _time.time()

            security = _get_or_create_security(user)
            security.login_attempts = 0
            security.last_login_ip = get_client_ip(request)
            security.save(update_fields=["login_attempts", "last_login_ip"])
            ActivityLog.objects.create(user=user, action="User logged in", ip_address=get_client_ip(request))
            next_url = request.GET.get("next", "dashboard")
            if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                next_url = reverse("dashboard")
            return redirect(next_url)
        else:
            if existing_user is not None:
                security = _get_or_create_security(existing_user)
                security.login_attempts += 1
                security.last_login_ip = get_client_ip(request)
                # Lock account for 15 minutes after 5 failed attempts
                if security.login_attempts >= 5:
                    from django.utils import timezone as _tz
                    from datetime import timedelta as _td
                    if hasattr(security, 'locked_until'):
                        security.locked_until = _tz.now() + _td(minutes=15)
                        security.save(update_fields=["login_attempts", "last_login_ip", "locked_until"])
                    else:
                        security.save(update_fields=["login_attempts", "last_login_ip"])
                    messages.error(request, "Too many failed attempts. Account locked for 15 minutes.")
                    return render(request, "auth/login.html", {'captcha_q': captcha_q})
                else:
                    security.save(update_fields=["login_attempts", "last_login_ip"])
                    remaining = 5 - security.login_attempts
                    messages.error(request, f"Invalid username or password. {remaining} attempt(s) remaining before lockout.")
                    return render(request, "auth/login.html", {'captcha_q': captcha_q})
            # Regenerate captcha
            a, b = _random.randint(1, 9), _random.randint(1, 9)
            request.session['captcha_answer'] = a + b
            request.session['captcha_q'] = f"{a} + {b}"
            captcha_q = request.session['captcha_q']
            messages.error(request, "Invalid username or password.")
    return render(request, "auth/login.html", {'captcha_q': captcha_q})


def logout_view(request):
    if request.user.is_authenticated:
        ActivityLog.objects.create(user=request.user, action="User logged out", ip_address=get_client_ip(request))
    logout(request)
    return redirect("home")


def super_admin_login_view(request):
    """Dedicated login for super admins — only accessible by direct URL.
    Regular logged-in users are NOT redirected here — they get a 403."""
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("super_admin_dashboard")
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access denied.")

    import random as _random
    if request.method != 'POST':
        a, b = _random.randint(1, 9), _random.randint(1, 9)
        request.session['sa_captcha_answer'] = a + b
        request.session['sa_captcha_q'] = f"{a} + {b}"

    captcha_q = request.session.get('sa_captcha_q', '? + ?')

    if request.method == "POST":
        captcha_input = request.POST.get("captcha", "").strip()
        try:
            captcha_valid = int(captcha_input) == request.session.get('sa_captcha_answer')
        except (ValueError, TypeError):
            captcha_valid = False

        if not captcha_valid:
            a, b = _random.randint(1, 9), _random.randint(1, 9)
            request.session['sa_captcha_answer'] = a + b
            request.session['sa_captcha_q'] = f"{a} + {b}"
            captcha_q = request.session['sa_captcha_q']
            messages.error(request, "Incorrect answer. Please try again.")
            return render(request, "auth/superadmin_login.html", {'captcha_q': captcha_q})

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            import time as _time
            request.session['_last_activity'] = _time.time()
            security = _get_or_create_security(user)
            security.login_attempts = 0
            security.last_login_ip = get_client_ip(request)
            security.save(update_fields=["login_attempts", "last_login_ip"])
            ActivityLog.objects.create(user=user, action="Super admin logged in", ip_address=get_client_ip(request))
            return redirect("super_admin_dashboard")
        else:
            a, b = _random.randint(1, 9), _random.randint(1, 9)
            request.session['sa_captcha_answer'] = a + b
            request.session['sa_captcha_q'] = f"{a} + {b}"
            captcha_q = request.session['sa_captcha_q']
            messages.error(request, "Invalid credentials.")

    return render(request, "auth/superadmin_login.html", {'captcha_q': captcha_q})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    invite_token = request.GET.get("token") or request.POST.get("token")
    invite = _get_registration_invite(invite_token)
    departments = Department.objects.filter(college=invite.college).order_by('name') if invite else Department.objects.none()

    if request.method == "POST":
        if not invite:
            messages.error(request, "This access link is missing, expired, or already used. Contact your college admin or use the help desk.")
            return redirect("helpdesk")
        email      = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name  = request.POST.get("last_name", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        desired_department = request.POST.get("desired_department")
        admission_year = request.POST.get("admission_year", "").strip()
        current_semester = request.POST.get("current_semester", "").strip()
        message = request.POST.get("message", "").strip()
        dob = request.POST.get("date_of_birth")
        gender = request.POST.get("gender", "").strip()
        
        # New Education and ID data
        photo_id = request.FILES.get("photo_id")
        aadhaar = request.POST.get("aadhaar_number", "").strip()
        inter_name = request.POST.get("inter_college_name", "").strip()
        inter_year = _safe_int(request.POST.get("inter_passed_year"))
        inter_pct = _safe_float(request.POST.get("inter_percentage"))
        school_name = request.POST.get("school_name", "").strip()
        school_year = _safe_int(request.POST.get("school_passed_year"))
        school_pct = _safe_float(request.POST.get("school_percentage"))

        if not first_name or not last_name or not email:
            messages.error(request, "First name, last name, and email are required.")
        elif email.lower() != invite.invited_email.lower():
            messages.error(request, "This one-time access link is tied to a different email address.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists. Please sign in.")
        elif RegistrationRequest.objects.filter(email=email, status__in=REGISTRATION_ACTIVE_STATUSES).exists():
            messages.warning(request, "A registration request for this email is already pending.")
        else:
            department = None
            if desired_department:
                department = departments.filter(pk=desired_department).first()
            with transaction.atomic():
                registration_request = RegistrationRequest.objects.create(
                    college=invite.college,
                    desired_department=department or invite.department,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone_number=phone_number,
                    admission_year=_safe_int(admission_year) or invite.admission_year,
                    current_semester=_safe_int(current_semester) or invite.current_semester,
                    message=message,
                    date_of_birth=dob if dob else None,
                    gender=gender,
                    photo_id=photo_id,
                    aadhaar_number=aadhaar,
                    inter_college_name=inter_name,
                    inter_passed_year=inter_year,
                    inter_percentage=inter_pct,
                    school_name=school_name,
                    school_passed_year=school_year,
                    school_percentage=school_pct,
                    status='SUBMITTED',
                )
                invite.used_at = timezone.now()
                invite.save(update_fields=["used_at"])

                _notify_registration_request_submitted(registration_request)

            messages.success(request, "Request submitted. The college admin will review it and contact you if corrections are needed.")
            return redirect("login")
    return render(request, "auth/register.html", {
        'departments': departments,
        'invite': invite,
        'invite_required': invite is None,
    })


def helpdesk_view(request):
    colleges = College.objects.order_by('name')
    initial_college = _get_user_college(request.user) if request.user.is_authenticated else None
    if request.method == "POST":
        college_id = request.POST.get("college")
        college = College.objects.filter(pk=college_id).first() if college_id else None
        name = request.POST.get("name", "").strip() or (request.user.get_full_name().strip() if request.user.is_authenticated else "")
        email = request.POST.get("email", "").strip() or (request.user.email.strip() if request.user.is_authenticated else "")
        issue_type = request.POST.get("issue_type", "GENERAL")
        subject = request.POST.get("subject", "").strip()
        description = request.POST.get("description", "").strip()

        if not name or not email or not subject or not description:
            messages.error(request, "Name, email, subject, and description are required.")
        else:
            ticket = HelpDeskTicket.objects.create(
                college=college,
                submitted_by=request.user if request.user.is_authenticated else None,
                name=name,
                email=email,
                issue_type=issue_type,
                subject=subject,
                description=description,
            )
            # Notify the student
            if request.user.is_authenticated:
                Notification.objects.create(user=request.user, message=f"Support Ticket #{ticket.id} has been raised: {subject}")

            messages.success(request, "Support request submitted. The college team can review it from the help desk." if college else "Support request submitted. The platform team will review and route your ticket.")
            return redirect("helpdesk")

    my_tickets = []
    if request.user.is_authenticated:
        my_tickets = HelpDeskTicket.objects.filter(submitted_by=request.user).order_by('-created_at')

    return render(request, "helpdesk.html", {
        "colleges": colleges,
        "initial_college": initial_college,
        "my_tickets": my_tickets,
    })


@login_required
def ticket_detail_view(request, pk):
    """Allows chat-based interaction between support and student."""
    ticket = get_object_or_404(HelpDeskTicket, pk=pk)
    
    # Security: Only owner or any staff role of that college can view
    is_owner = (ticket.submitted_by == request.user)
    role = _get_user_role(request.user)
    is_staff = (
        request.user.is_superuser or
        (role and role.role in (1, 2, 6) and (
            ticket.college is None or
            ticket.college == _get_user_college(request.user)
        ))
    )

    if not (is_owner or is_staff):
        raise PermissionDenied

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'comment':
            msg = request.POST.get('message', '').strip()
            if msg:
                TicketComment.objects.create(
                    ticket=ticket, author=request.user, 
                    message=msg, is_admin_reply=is_staff
                )
                # Notify the other party
                recipient = ticket.submitted_by if is_staff else None
                if recipient:
                    Notification.objects.create(user=recipient, message=f"New reply on Support Ticket #{ticket.id}")
                messages.success(request, "Reply posted.")
        
        elif action == 'status_update' and is_owner:
            new_status = request.POST.get('status') # 'RESOLVED' or 'OPEN'
            if new_status in {'RESOLVED', 'OPEN'}:
                ticket.status = new_status
                ticket.save(update_fields=['status', 'updated_at'])
                messages.success(request, f"Ticket marked as {new_status.lower()}.")

        return redirect('ticket_detail', pk=pk)

    comments = ticket.comments.all().select_related('author').order_by('created_at')
    return render(request, 'helpdesk_detail.html', {
        'ticket': ticket, 'comments': comments, 'is_staff': is_staff
    })


@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_superuser:
        return redirect("super_admin_dashboard")
    try:
        role = user.userrole.role
    except UserRole.DoesNotExist:
        messages.warning(request, "Your account has no role assigned. Contact admin.")
        logout(request)
        return redirect("login")
    role_map = {
        1: "admin_dashboard",
        2: "hod_dashboard",
        3: "faculty_dashboard",
        4: "student_dashboard",
        5: "lab_staff_dashboard",
        6: "principal_dashboard",
        7: "exam_dashboard",
    }
    return redirect(role_map.get(role, "student_dashboard"))


@login_required
def lab_staff_dashboard(request):
    """Dedicated dashboard for Lab Staff (Role 5)."""
    try:
        if request.user.userrole.role != 5:
            return redirect('dashboard')
    except UserRole.DoesNotExist:
        return redirect('login')
    
    college = _get_user_college(request.user)
    
    # Real-time: Identify classes happening in labs right now
    now_time = timezone.localtime(timezone.now()).time()
    today_day = {0:'MON',1:'TUE',2:'WED',3:'THU',4:'FRI',5:'SAT',6:'SUN'}.get(timezone.localtime(timezone.now()).weekday())

    active_lab_sessions = Timetable.objects.filter(
        classroom__college=college,
        day_of_week=today_day,
        start_time__lte=now_time,
        end_time__gte=now_time
    ).select_related('subject', 'faculty__user', 'classroom')

    today_schedule = Timetable.objects.filter(
        classroom__college=college,
        day_of_week=today_day,
    ).select_related('subject', 'faculty__user', 'classroom').order_by('start_time')

    classrooms = Classroom.objects.filter(college=college).order_by('room_number')
    announcements = _scope_announcements_for_college(college).order_by('-created_at')[:5]

    context = {
        'college': college,
        'classrooms': classrooms,
        'active_lab_sessions': active_lab_sessions,
        'today_schedule': today_schedule,
        'announcements': announcements,
        'role_name': 'Lab Technician',
        'branding': _get_college_branding(college),
    }
    return render(request, 'dashboards/lab_staff.html', context)


@login_required
@super_admin_required
def super_admin_dashboard(request):
    colleges = College.objects.annotate(
        department_count=Count('departments', distinct=True),
        admin_count=Count('user_roles', filter=Q(user_roles__role=1), distinct=True),
        # student/faculty counts shown as aggregate only — no PII exposed
        student_count=Count('departments__student', distinct=True),
        faculty_count=Count('departments__faculty', distinct=True),
    ).order_by('name')
    college_admins = UserRole.objects.filter(role=1).select_related('user', 'college').order_by('college__name', 'user__username')
    platform_announcements = Announcement.objects.filter(college__isnull=True).select_related('created_by').order_by('-created_at')[:5]

    # Activity log: only super-admin actions, NOT college user activity
    recent_activity = ActivityLog.objects.filter(
        user__is_superuser=True
    ).select_related('user').order_by('-timestamp')[:15]

    context = {
        'colleges': colleges,
        'college_admins': college_admins,
        'recent_activity': recent_activity,
        'platform_announcements': platform_announcements,
        'total_colleges': colleges.count(),
        'total_college_admins': college_admins.count(),
        # Platform-level counts only — no breakdown by college
        'total_users': User.objects.count(),
        'total_students': Student.objects.count(),
        'total_faculty': Faculty.objects.count(),
        'total_departments': Department.objects.count(),
    }
    return render(request, 'dashboards/super_admin.html', context)


@login_required
@super_admin_required
def super_admin_college_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        student_rule = request.POST.get('student_id_rule', '{YEAR}-{CODE}-{DEPT}-{SERIAL}')
        faculty_rule = request.POST.get('faculty_id_rule', 'FAC-{CODE}-{SERIAL}')
        logo = request.FILES.get('logo')
        if not name or not code:
            messages.error(request, 'College name and code are required.')
        elif College.objects.filter(Q(name=name) | Q(code=code)).exists():
            messages.error(request, 'A college with this name or code already exists.')
        else:
            College.objects.create(
                name=name, code=code, 
                city=city, state=state, 
                logo=logo,
                student_id_rule=student_rule,
                faculty_id_rule=faculty_rule
            )
            messages.success(request, 'College created successfully.')
            return redirect('super_admin_dashboard')

    return render(request, 'super_admin/college_form.html')


@login_required
@super_admin_required
def super_admin_college_admin_add(request):
    colleges = College.objects.order_by('name')
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        college_id = request.POST.get('college')

        if not college_id:
            messages.error(request, 'Select a college for the college admin.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
        else:
            college = get_object_or_404(College, pk=college_id)
            password_value, password_generated = _resolve_password(password)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password_value,
                first_name=first_name,
                last_name=last_name,
            )
            UserRole.objects.create(user=user, role=1, college=college)
            if password_generated:
                messages.success(request, f'College admin created successfully. Temporary password: {password_value}')
            else:
                messages.success(request, 'College admin created successfully.')
            return redirect('super_admin_dashboard')

    return render(request, 'super_admin/college_admin_form.html', {'colleges': colleges})


@login_required
@super_admin_required
def super_admin_college_edit(request, pk):
    college = get_object_or_404(College, pk=pk)
    if request.method == 'POST':
        college.name  = request.POST.get('name', college.name).strip()
        college.code  = request.POST.get('code', college.code).strip().upper()
        college.city  = request.POST.get('city', '').strip()
        college.state = request.POST.get('state', '').strip()
        college.email   = request.POST.get('email', '').strip() or None
        college.website = request.POST.get('website', '').strip() or None
        college.student_id_rule = request.POST.get('student_id_rule', college.student_id_rule)
        college.faculty_id_rule = request.POST.get('faculty_id_rule', college.faculty_id_rule)
        if request.FILES.get('logo'):
            college.logo = request.FILES['logo']
        college.save()
        messages.success(request, f'College "{college.name}" updated.')
        return redirect('super_admin_dashboard')
    return render(request, 'super_admin/college_edit_form.html', {'college': college})


@login_required
@super_admin_required
def super_admin_college_toggle(request, pk):
    """Toggle a college active/inactive without deleting it."""
    college = get_object_or_404(College, pk=pk)
    if request.method == 'POST':
        college.is_active = not college.is_active
        college.save(update_fields=['is_active'])
        state = 'activated' if college.is_active else 'deactivated'
        messages.success(request, f'College "{college.name}" {state}.')
    return redirect('super_admin_dashboard')


@login_required
@super_admin_required
def super_admin_college_admin_delete(request, pk):
    """Remove a college admin account."""
    role = get_object_or_404(UserRole, pk=pk, role=1)
    if request.method == 'POST':
        user = role.user
        role.delete()
        user.delete()
        messages.success(request, 'College admin account removed.')
    return redirect('super_admin_dashboard')


@login_required
@super_admin_required
def super_admin_college_detail(request, pk):
    """
    Per-college overview for the platform operator.
    Shows only structural/operational data — NO student PII, NO financial details,
    NO user activity. Colleges trust the platform to not expose their data.
    """
    college = get_object_or_404(College, pk=pk)
    departments = Department.objects.filter(college=college).annotate(
        student_count=Count('student', distinct=True),
        faculty_count=Count('faculty', distinct=True),
    ).order_by('name')
    admins = UserRole.objects.filter(role=1, college=college).select_related('user')
    # Counts only — no names, no PII, no financials
    total_students = Student.objects.filter(department__college=college).count()
    total_faculty  = Faculty.objects.filter(department__college=college).count()
    return render(request, 'super_admin/college_detail.html', {
        'college': college,
        'departments': departments,
        'admins': admins,
        'total_students': total_students,
        'total_faculty': total_faculty,
        # Financial and activity data intentionally excluded —
        # platform operator has no business need to see college finances or user activity
    })


@login_required
@super_admin_required
def super_admin_platform_announcement(request):
    """Broadcast an announcement to all colleges."""
    if request.method == 'POST':
        title   = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        if not title or not message:
            messages.error(request, 'Title and message are required.')
        else:
            # college=None means visible to all colleges
            Announcement.objects.create(
                title=title, message=message,
                created_by=request.user, college=None
            )
            messages.success(request, f'Platform announcement "{title}" broadcast to all colleges.')
            return redirect('super_admin_dashboard')
    recent = Announcement.objects.filter(college__isnull=True).select_related('created_by').order_by('-created_at')[:10]
    return render(request, 'super_admin/platform_announcement.html', {'recent': recent})


@login_required
@super_admin_required
def super_admin_platform_announcement_delete(request, pk):
    ann = get_object_or_404(Announcement, pk=pk, college__isnull=True)
    if request.method == 'POST':
        ann.delete()
        messages.success(request, 'Announcement deleted.')
    return redirect('super_admin_platform_announcement')


@login_required
def admin_dashboard(request):
    if not _admin_guard(request):
        return redirect("dashboard")

    college = _get_admin_college(request)
    department_qs = _scope_departments(request)
    student_qs = Student.objects.select_related("user", "department").filter(department__in=department_qs)
    faculty_qs = Faculty.objects.select_related("user", "department").filter(department__in=department_qs)
    hod_qs = HOD.objects.select_related("user", "department").filter(department__in=department_qs)
    fee_qs = Fee.objects.select_related("student__department").filter(student__department__in=department_qs)
    announcement_qs = _scope_announcements_for_college(college).select_related("created_by")
    request_qs = RegistrationRequest.objects.filter(college=college).select_related('desired_department').order_by('-created_at')
    invite_qs = RegistrationInvite.objects.filter(college=college).order_by('-created_at')
    helpdesk_qs = HelpDeskTicket.objects.filter(Q(college=college) | Q(college__isnull=True)).order_by('-created_at')

    # System Health Dashboard Metrics
    active_users_count = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(hours=24),
        userrole__college=college
    ).count()
    
    # Attendance Completion Rate: (Marked Sessions Today / Scheduled Slots Today)
    today_day = {0:'MON',1:'TUE',2:'WED',3:'THU',4:'FRI',5:'SAT',6:'SUN'}.get(timezone.localtime(timezone.now()).weekday())
    scheduled_today = Timetable.objects.filter(subject__department__college=college, day_of_week=today_day).count()
    marked_today = AttendanceSession.objects.filter(subject__department__college=college, date=timezone.localtime(timezone.now()).date()).count()
    attendance_rate = round((marked_today / scheduled_today * 100), 1) if scheduled_today > 0 else 100.0

    total_students    = student_qs.count()
    total_faculty     = faculty_qs.count()
    total_departments = department_qs.count()
    total_hods        = hod_qs.count()
    pending_fees      = fee_qs.filter(Q(status="PENDING") | Q(status="PARTIAL")).count()
    recent_students   = student_qs.order_by("-created_at")[:5]
    recent_announcements = announcement_qs.order_by("-created_at")[:5]
    recent_requests = request_qs[:5]
    recent_helpdesk_tickets = helpdesk_qs[:10]
    departments       = department_qs
    total_collected   = fee_qs.aggregate(s=Sum("paid_amount"))["s"] or 0
    total_pending_agg = fee_qs.exclude(status="PAID").aggregate(
        pending=Sum(F('total_amount') - F('paid_amount'))
    )
    total_pending = total_pending_agg['pending'] or 0

    context = {
        "total_students": total_students, "total_faculty": total_faculty,
        "total_departments": total_departments, "total_hods": total_hods,
        "pending_fees": pending_fees, "recent_students": recent_students,
        "recent_announcements": recent_announcements, "departments": departments,
        "fee_summary": {"total_collected": total_collected, "total_pending": total_pending},
        "pending_requests": request_qs.filter(status__in=['SUBMITTED', 'UNDER_REVIEW', 'NEEDS_CORRECTION', 'APPROVED']).count(),
        "recent_requests": recent_requests,
        "recent_helpdesk_tickets": recent_helpdesk_tickets,
        "active_invites": invite_qs.filter(used_at__isnull=True).count(),
        "open_helpdesk_tickets": helpdesk_qs.exclude(status='RESOLVED').count(),
        "active_users_24h": active_users_count,
        "attendance_completion_rate": attendance_rate,
        "college": college,
        "branding": _get_college_branding(college),
        "exams_without_schedule": _scope_exams(request).exclude(
            pk__in=ExamSchedule.objects.values_list('exam_id', flat=True)
        ).count(),
        "all_helpdesk_tickets": helpdesk_qs,
        "exams": _scope_exams(request).select_related('created_by').order_by('-start_date'),
        "all_departments": department_qs.annotate(
            student_count=Count('student', distinct=True),
            faculty_count=Count('faculty', distinct=True),
            subject_count=Count('subject', distinct=True),
        ).order_by('name'),
        # Subjects: capped at 100 per page; filter by dept/semester via GET params
        "all_subjects": Subject.objects.filter(department__in=department_qs).select_related('department').order_by('department__code', 'semester', 'name')[:100],
        "all_subjects_total": Subject.objects.filter(department__in=department_qs).count(),
        "all_students_full": student_qs.order_by('-created_at')[:100],
        "all_students_total": student_qs.count(),
        "all_faculty_full": faculty_qs.select_related('user', 'department').order_by('department__name', 'user__first_name')[:100],
        "all_faculty_total": faculty_qs.count(),
        "all_hods_full": hod_qs.filter(is_active=True).select_related('user', 'department').order_by('department__name')[:50],
        "all_fees": Fee.objects.select_related('student__user', 'student__department').filter(
            student__department__in=department_qs
        ).annotate(balance=ExpressionWrapper(F('total_amount') - F('paid_amount'), output_field=FloatField())).order_by('status', 'student__roll_number')[:100],
        "all_fees_total": fee_qs.count(),
        "all_announcements": announcement_qs.order_by('-created_at')[:50],
        "all_invites": invite_qs.order_by('-created_at')[:50],
        "all_requests": request_qs.select_related('desired_department').order_by('-created_at')[:50],
        "now": timezone.now(),
        "color_presets": [
            {"name": "Ocean",   "primary": "#0d7377", "accent": "#e6a817", "deep": "#071e26"},
            {"name": "Royal",   "primary": "#4f46e5", "accent": "#f59e0b", "deep": "#1e1b4b"},
            {"name": "Forest",  "primary": "#059669", "accent": "#d97706", "deep": "#064e3b"},
            {"name": "Crimson", "primary": "#dc2626", "accent": "#7c3aed", "deep": "#1c0a0a"},
            {"name": "Slate",   "primary": "#475569", "accent": "#f59e0b", "deep": "#0f172a"},
        ],
    }
    return render(request, "dashboards/admin.html", context)


@login_required
def principal_dashboard(request):
    try:
        principal = Principal.objects.select_related("college").get(user=request.user)
    except Principal.DoesNotExist:
        messages.error(request, "Principal profile not found. Contact admin.")
        return redirect("home")

    college = principal.college
    departments = Department.objects.filter(college=college).annotate(
        student_count=Count('student', distinct=True),
        faculty_count=Count('faculty', distinct=True),
        subject_count=Count('subject', distinct=True),
    ).order_by("name")
    faculty_list = Faculty.objects.filter(department__college=college).select_related("user", "department")[:100]
    students_list = Student.objects.filter(department__college=college).select_related("user", "department")[:100]
    hod_list = HOD.objects.filter(department__college=college).select_related("user", "department")[:50]
    total_faculty_count = Faculty.objects.filter(department__college=college).count()
    total_students_count = Student.objects.filter(department__college=college).count()
    announcements = _scope_announcements_for_college(college).order_by("-created_at")[:8]
    recent_students = Student.objects.filter(department__college=college).select_related("user", "department").order_by("-created_at")[:8]

    # Fee summary
    fee_qs = Fee.objects.filter(student__department__college=college)
    total_collected = fee_qs.aggregate(s=Sum('paid_amount'))['s'] or 0
    total_pending   = fee_qs.exclude(status='PAID').aggregate(
        p=Sum(F('total_amount') - F('paid_amount'))
    )['p'] or 0
    pending_fee_count = fee_qs.filter(status__in=['PENDING', 'PARTIAL']).count()
    paid_fee_count = fee_qs.filter(status='PAID').count()
    total_fee_count = fee_qs.count()

    # Attendance health per department — single bulk query instead of N×2 queries
    dept_ids = list(departments.values_list('id', flat=True))
    att_agg = Attendance.objects.filter(
        student__department_id__in=dept_ids
    ).values('student__department_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    att_by_dept = {row['student__department_id']: row for row in att_agg}

    # Defaulters: one query across all departments
    student_att_all = Attendance.objects.filter(
        student__department_id__in=dept_ids
    ).values('student', 'student__department_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    defaulters_by_dept = {}
    for row in student_att_all:
        if row['total'] > 0 and (row['present'] / row['total'] * 100) < 75:
            did = row['student__department_id']
            defaulters_by_dept[did] = defaulters_by_dept.get(did, 0) + 1

    dept_attendance = []
    for dept in departments:
        agg = att_by_dept.get(dept.id, {'total': 0, 'present': 0})
        pct = round(agg['present'] / agg['total'] * 100, 1) if agg['total'] else 0
        dept_attendance.append({'dept': dept, 'pct': pct, 'total': agg['total'], 'defaulters': defaulters_by_dept.get(dept.id, 0)})

    # Students by semester across college
    sem_distribution = students_list.values('current_semester').annotate(
        count=Count('id')
    ).order_by('current_semester')

    # Top performing departments by avg GPA — single query instead of N queries
    dept_gpa_agg = Result.objects.filter(
        student__department__college=college
    ).values('student__department_id').annotate(avg_gpa=Avg('gpa'))
    dept_gpa_map = {row['student__department_id']: row['avg_gpa'] for row in dept_gpa_agg}
    dept_gpa = []
    for dept in departments:
        avg = dept_gpa_map.get(dept.id)
        if avg is not None:
            dept_gpa.append({'dept': dept, 'avg_gpa': round(avg, 2)})
    dept_gpa = sorted(dept_gpa, key=lambda x: x['avg_gpa'], reverse=True)

    # Recent activity — last 5 announcements + recent students
    recent_activity = []
    for ann in announcements[:3]:
        recent_activity.append({'type': 'notice', 'text': ann.title, 'date': ann.created_at})
    for s in recent_students[:3]:
        recent_activity.append({'type': 'student', 'text': f"{s.user.get_full_name()} joined {s.department.code}", 'date': s.created_at})
    recent_activity.sort(key=lambda x: x['date'], reverse=True)

    context = {
        "principal": principal,
        "college": college,
        "departments": departments,
        "faculty_list": faculty_list,
        "students_list": students_list,
        "hod_list": hod_list,
        "announcements": announcements,
        "recent_students": recent_students,
        "total_departments": departments.count(),
        "total_faculty": total_faculty_count,
        "total_students": total_students_count,
        "total_hods": hod_list.count(),
        "total_collected": total_collected,
        "total_pending": total_pending,
        "pending_fee_count": pending_fee_count,
        "paid_fee_count": paid_fee_count,
        "total_fee_count": total_fee_count,
        "dept_attendance": dept_attendance,
        "sem_distribution": sem_distribution,
        "dept_gpa": dept_gpa,
        "recent_activity": recent_activity,
        "branding": _get_college_branding(college),
    }
    return render(request, "dashboards/principal.html", context)


@login_required
def hod_dashboard(request):
    user = request.user
    try:
        hod = HOD.objects.select_related('department').get(user=user)
    except HOD.DoesNotExist:
        messages.error(request, 'HOD profile not found. Contact admin.')
        return redirect('home')

    dept = hod.department
    faculty_list   = Faculty.objects.filter(department=dept).select_related('user')[:100]
    total_faculty_count = Faculty.objects.filter(department=dept).count()
    students_list  = Student.objects.filter(department=dept, status='ACTIVE').select_related('user').order_by('roll_number')[:100]
    total_students_count = Student.objects.filter(department=dept, status='ACTIVE').count()
    subjects_list  = Subject.objects.filter(department=dept)
    pending_approvals = HODApproval.objects.filter(department=dept, status='PENDING').select_related('requested_by')
    recent_approvals  = HODApproval.objects.filter(department=dept).order_by('-created_at')[:10]

    # Leave applications from faculty in this department — shown to relevant HOD only
    pending_leaves = LeaveApplication.objects.filter(
        faculty__department=dept, status='PENDING'
    ).select_related('faculty__user', 'suggested_substitute__user').order_by('from_date')
    recent_leaves = LeaveApplication.objects.filter(
        faculty__department=dept
    ).order_by('-created_at')[:10]
    announcements  = _scope_announcements_for_college(dept.college).order_by('-created_at')[:5]

    today_day = {0:'MON',1:'TUE',2:'WED',3:'THU',4:'FRI',5:'SAT',6:'SUN'}.get(timezone.localtime(timezone.now()).weekday(), '')
    today_timetable = Timetable.objects.filter(
        subject__department=dept, day_of_week=today_day
    ).select_related('subject', 'faculty__user', 'classroom').order_by('start_time')

    # Attendance per subject — bulk queries, threshold from rule engine
    subject_ids = list(subjects_list.values_list('id', flat=True))
    hod_att_rule = _get_attendance_rule(dept.college, dept)
    defaulter_threshold = hod_att_rule.effective_min_subject

    session_counts = AttendanceSession.objects.filter(subject_id__in=subject_ids).values('subject_id').annotate(count=Count('id'))
    sessions_by_subj = {row['subject_id']: row['count'] for row in session_counts}

    att_agg = Attendance.objects.filter(session__subject_id__in=subject_ids).values('session__subject_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    att_by_subj = {row['session__subject_id']: row for row in att_agg}

    # Defaulters per subject — single query
    student_att_per_subj = Attendance.objects.filter(
        session__subject_id__in=subject_ids
    ).values('student', 'session__subject_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    defaulters_by_subj = {}
    for row in student_att_per_subj:
        if row['total'] > 0 and (row['present'] / row['total'] * 100) < defaulter_threshold:
            sid = row['session__subject_id']
            defaulters_by_subj[sid] = defaulters_by_subj.get(sid, 0) + 1

    subject_attendance = []
    for subj in subjects_list:
        agg = att_by_subj.get(subj.id, {'total': 0, 'present': 0})
        pct = round(agg['present'] / agg['total'] * 100, 1) if agg['total'] > 0 else 0
        subject_attendance.append({
            'subject': subj,
            'sessions': sessions_by_subj.get(subj.id, 0),
            'pct': pct,
            'defaulters': defaulters_by_subj.get(subj.id, 0),
            'total_records': agg['total'],
        })

    # Faculty workload — bulk queries instead of N×3 per faculty
    faculty_ids = list(faculty_list.values_list('id', flat=True))
    faculty_user_ids = list(faculty_list.values_list('user_id', flat=True))

    subj_counts = FacultySubject.objects.filter(faculty_id__in=faculty_ids).values('faculty_id').annotate(count=Count('id'))
    subj_count_map = {row['faculty_id']: row['count'] for row in subj_counts}

    sessions_month = AttendanceSession.objects.filter(
        faculty_id__in=faculty_ids,
        date__month=timezone.now().month,
        date__year=timezone.now().year
    ).values('faculty_id').annotate(count=Count('id'))
    sessions_month_map = {row['faculty_id']: row['count'] for row in sessions_month}

    pending_reviews_agg = AssignmentSubmission.objects.filter(
        assignment__created_by_id__in=faculty_user_ids, marks__isnull=True
    ).values('assignment__created_by_id').annotate(count=Count('id'))
    pending_reviews_map = {row['assignment__created_by_id']: row['count'] for row in pending_reviews_agg}

    faculty_workload = []
    for f in faculty_list:
        faculty_workload.append({
            'faculty': f,
            'subj_count': subj_count_map.get(f.id, 0),
            'sessions_this_month': sessions_month_map.get(f.id, 0),
            'pending_reviews': pending_reviews_map.get(f.user_id, 0),
        })

    # Students by semester breakdown — use unsliced count query
    sem_breakdown = Student.objects.filter(department=dept, status='ACTIVE').values('current_semester').annotate(count=Count('id')).order_by('current_semester')

    # Approval stats
    approval_stats = {
        'pending': pending_approvals.count() + pending_leaves.count(),
        'approved': HODApproval.objects.filter(department=dept, status='APPROVED').count(),
        'rejected': HODApproval.objects.filter(department=dept, status='REJECTED').count(),
    }

    context = {
        'hod': hod, 'dept': dept,
        'college': dept.college,
        'total_faculty': total_faculty_count,
        'total_students': total_students_count,
        'total_subjects': subjects_list.count(),
        'pending_approvals_count': pending_approvals.count() + pending_leaves.count(),
        'faculty_list': faculty_list,
        'students_list': students_list,
        'pending_approvals': pending_approvals,
        'recent_approvals': recent_approvals,
        'pending_leaves': pending_leaves,
        'recent_leaves': recent_leaves,
        'subject_attendance': subject_attendance,
        'today_timetable': today_timetable,
        'today_day': today_day,
        'announcements': announcements,
        'faculty_workload': faculty_workload,
        'sem_breakdown': sem_breakdown,
        'approval_stats': approval_stats,
        'branding': _get_college_branding(dept.college),
    }
    return render(request, 'dashboards/hod.html', context)


@login_required
def hod_approve(request, pk):
    """Approve or reject a HODApproval request."""
    try:
        hod = HOD.objects.get(user=request.user)
    except HOD.DoesNotExist:
        return redirect('dashboard')

    approval = get_object_or_404(HODApproval, pk=pk, department=hod.department)
    action = request.POST.get('action')
    if action in ('APPROVED', 'REJECTED'):
        approval.status = action
        approval.reviewed_by = request.user
        approval.reviewed_at = timezone.now()
        approval.save()
        messages.success(request, f'Request {action.lower()} successfully.')
    return redirect('hod_dashboard')


@login_required
def hod_leave_review(request, pk):
    """Approve or reject a faculty LeaveApplication."""
    try:
        hod = HOD.objects.get(user=request.user)
    except HOD.DoesNotExist:
        return redirect('dashboard')

    leave = get_object_or_404(LeaveApplication, pk=pk, faculty__department=hod.department)
    action = request.POST.get('action')
    if action in ('APPROVED', 'REJECTED'):
        leave.status = action
        leave.reviewed_by = request.user
        leave.reviewed_at = timezone.now()
        leave.hod_remarks = request.POST.get('remarks', '').strip()
        leave.save()
        # Notify faculty
        Notification.objects.create(
            user=leave.faculty.user,
            message=f'Your {leave.get_leave_type_display()} ({leave.from_date} – {leave.to_date}) has been {action.lower()} by HOD.'
        )
        messages.success(request, f'Leave {action.lower()}.')
    return redirect('hod_dashboard')


@login_required
def hod_substitutions(request):
    """Manage faculty substitutions for the department."""
    try:
        hod = HOD.objects.select_related('department').get(user=request.user)
    except HOD.DoesNotExist:
        return redirect('dashboard')

    dept = hod.department
    today = timezone.now().date()
    substitutions = Substitution.objects.filter(timetable_slot__subject__department=dept, date__gte=today).order_by('date')
    
    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        sub_faculty_id = request.POST.get('substitute_faculty_id')
        sub_date_str = request.POST.get('date', str(today))
        
        slot = get_object_or_404(Timetable, pk=slot_id, subject__department=dept)
        sub_faculty = get_object_or_404(Faculty, pk=sub_faculty_id, department=dept)

        # Prevent assigning the same faculty as their own substitute
        if slot.faculty_id == sub_faculty.id:
            messages.error(request, f"{sub_faculty.user.get_full_name()} is already the assigned faculty for this slot — choose a different substitute.")
            return redirect('hod_substitutions')
        
        try:
            sub_date = datetime.fromisoformat(sub_date_str).date()
        except ValueError:
            sub_date = today

        Substitution.objects.update_or_create(
            timetable_slot=slot,
            date=sub_date,
            defaults={
                'original_faculty': slot.faculty,
                'substitute_faculty': sub_faculty
            }
        )
        messages.success(request, f"Substitution assigned: {sub_faculty.user.get_full_name()} will cover {slot.subject.name} on {sub_date}.")
        return redirect('hod_substitutions')

    # For the form: slots in this department and available faculty
    # Build a map of slot_id → original_faculty_id for JS filtering
    slots = Timetable.objects.filter(subject__department=dept).select_related('subject', 'faculty__user')
    faculty_list = Faculty.objects.filter(department=dept).select_related('user')
    slot_faculty_map = {slot.pk: slot.faculty_id for slot in slots}

    import json
    slot_faculty_json = json.dumps(slot_faculty_map)
    
    return render(request, 'hod/substitutions.html', {
        'substitutions': substitutions, 'slots': slots, 'faculty_list': faculty_list,
        'slot_faculty_map': slot_faculty_map,
        'slot_faculty_json': slot_faculty_json,
        'today': today,
        'college': dept.college,
        'branding': _get_college_branding(dept.college),
    })


@login_required
def hod_student_profile(request, pk):
    """Read-only student profile view for HOD — attendance, results, fees summary, assignments."""
    try:
        hod = HOD.objects.select_related('department').get(user=request.user)
    except HOD.DoesNotExist:
        return redirect('dashboard')

    dept = hod.department
    student = get_object_or_404(Student, pk=pk, department=dept)
    college = dept.college

    # Attendance per subject (current semester)
    subjects = Subject.objects.filter(department=dept, semester=student.current_semester)
    att_agg = Attendance.objects.filter(
        student=student, session__subject__in=subjects
    ).values('session__subject_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    att_map = {r['session__subject_id']: r for r in att_agg}

    attendance_data = []
    for subj in subjects:
        agg = att_map.get(subj.id, {'total': 0, 'present': 0})
        pct = round(agg['present'] / agg['total'] * 100, 1) if agg['total'] > 0 else None
        attendance_data.append({'subject': subj, 'present': agg['present'], 'total': agg['total'], 'pct': pct})

    overall_pct = None
    total_p = sum(a['present'] for a in attendance_data)
    total_t = sum(a['total'] for a in attendance_data)
    if total_t > 0:
        overall_pct = round(total_p / total_t * 100, 1)

    # Eligibility
    elig = _compute_eligibility(student, student.current_semester, college)

    # Results — all semesters
    results = Result.objects.filter(student=student).order_by('semester')
    cgpa = round(sum(r.gpa for r in results) / len(results), 2) if results else None

    # Fee
    fee = Fee.objects.filter(student=student).first()

    # Pending assignments
    pending_assignments = AssignmentSubmission.objects.filter(
        student=student, marks__isnull=True
    ).select_related('assignment__subject').count()

    # Recent attendance sessions (last 10 absences)
    recent_absences = Attendance.objects.filter(
        student=student, status='ABSENT',
        session__subject__in=subjects
    ).select_related('session__subject').order_by('-session__date')[:10]

    return render(request, 'hod/student_profile.html', {
        'hod': hod, 'dept': dept, 'college': college,
        'student': student,
        'attendance_data': attendance_data,
        'overall_pct': overall_pct,
        'elig': elig,
        'results': results,
        'cgpa': cgpa,
        'fee': fee,
        'pending_assignments': pending_assignments,
        'recent_absences': recent_absences,
        'branding': _get_college_branding(college),
    })


@login_required
def hod_faculty_profile(request, pk):
    """HOD views a read-only profile of a faculty member in their department."""
    try:
        hod = HOD.objects.select_related('department').get(user=request.user)
    except HOD.DoesNotExist:
        return redirect('dashboard')

    dept = hod.department
    faculty = get_object_or_404(Faculty.objects.select_related('user', 'department'), pk=pk, department=dept)

    # Subjects assigned
    assigned_subjects = FacultySubject.objects.filter(faculty=faculty).select_related('subject').order_by('subject__semester', 'subject__name')

    # Attendance sessions this month
    from django.utils import timezone as _tz
    now = _tz.now()
    sessions_this_month = AttendanceSession.objects.filter(
        faculty=faculty, date__year=now.year, date__month=now.month
    ).count()
    sessions_total = AttendanceSession.objects.filter(faculty=faculty).count()

    # Attendance per subject (class average)
    subject_ids = [fs.subject_id for fs in assigned_subjects]
    att_agg = Attendance.objects.filter(
        session__faculty=faculty, session__subject_id__in=subject_ids
    ).values('session__subject_id').annotate(
        total=Count('id'), present=Count('id', filter=Q(status='PRESENT'))
    )
    att_map = {r['session__subject_id']: r for r in att_agg}

    subject_stats = []
    for fs in assigned_subjects:
        agg = att_map.get(fs.subject_id, {'total': 0, 'present': 0})
        pct = round(agg['present'] / agg['total'] * 100, 1) if agg['total'] > 0 else 0
        subject_stats.append({'subject': fs.subject, 'total': agg['total'], 'present': agg['present'], 'pct': pct})

    # Pending assignment reviews
    pending_reviews = AssignmentSubmission.objects.filter(
        assignment__created_by=faculty.user, marks__isnull=True
    ).count()

    # Leave history
    leave_history = LeaveApplication.objects.filter(faculty=faculty).order_by('-from_date')[:8]

    return render(request, 'hod/faculty_profile.html', {
        'hod': hod, 'dept': dept, 'college': dept.college,
        'faculty': faculty,
        'assigned_subjects': assigned_subjects,
        'subject_stats': subject_stats,
        'sessions_this_month': sessions_this_month,
        'sessions_total': sessions_total,
        'pending_reviews': pending_reviews,
        'leave_history': leave_history,
        'branding': _get_college_branding(dept.college),
    })


# ── FACULTY DASHBOARD ────────────────────────────────────

@login_required
def faculty_dashboard(request):
    user = request.user
    try:
        faculty = Faculty.objects.select_related('department').get(user=user)
    except Faculty.DoesNotExist:
        messages.error(request, 'Faculty profile not found. Contact admin.')
        return redirect('home')

    assigned_subjects = FacultySubject.objects.filter(faculty=faculty).select_related('subject').annotate(
        total_assignments=Count('subject__assignment', distinct=True)
    )
    subjects = [fs.subject for fs in assigned_subjects]

    # Bulk-fetch all attendance stats for all subjects at once
    subject_ids = [s.id for s in subjects]
    session_counts_qs = AttendanceSession.objects.filter(
        subject_id__in=subject_ids, faculty=faculty
    ).values('subject_id').annotate(count=Count('id'))
    session_counts_map = {row['subject_id']: row['count'] for row in session_counts_qs}

    att_agg_qs = Attendance.objects.filter(
        session__subject_id__in=subject_ids, session__faculty=faculty
    ).values('session__subject_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    att_map = {row['session__subject_id']: row for row in att_agg_qs}

    # Defaulters per subject — single query
    student_att_qs = Attendance.objects.filter(
        session__subject_id__in=subject_ids
    ).values('student', 'session__subject_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    defaulters_map = {}
    for row in student_att_qs:
        if row['total'] > 0 and (row['present'] / row['total'] * 100) < 75:
            sid = row['session__subject_id']
            defaulters_map[sid] = defaulters_map.get(sid, 0) + 1

    # Bulk-fetch enrolled student counts per (department, semester) — single query
    dept_sem_pairs = list({(s.department_id, s.semester) for s in subjects})
    enrolled_counts = {}
    if dept_sem_pairs:
        dept_ids_for_enroll = list({p[0] for p in dept_sem_pairs})
        sems_for_enroll = list({p[1] for p in dept_sem_pairs})
        enroll_agg = Student.objects.filter(
            department_id__in=dept_ids_for_enroll,
            current_semester__in=sems_for_enroll
        ).values('department_id', 'current_semester').annotate(count=Count('id'))
        for row in enroll_agg:
            enrolled_counts[(row['department_id'], row['current_semester'])] = row['count']

    # Bulk-fetch latest exam per semester to avoid N queries
    semesters_needed = list({s.semester for s in subjects})
    college = faculty.department.college
    exams_qs = Exam.objects.filter(
        Q(college=college) | Q(college__isnull=True),
        semester__in=semesters_needed
    ).order_by('-start_date')
    latest_exam_by_sem = {}
    for exam in exams_qs:
        if exam.semester not in latest_exam_by_sem:
            latest_exam_by_sem[exam.semester] = exam

    subject_cards = []
    for subject in subjects:
        agg = att_map.get(subject.id, {'total': 0, 'present': 0})
        att_pct = round(agg['present'] / agg['total'] * 100, 1) if agg['total'] > 0 else 0
        subject_cards.append({
            'subject': subject,
            'exam': latest_exam_by_sem.get(subject.semester),
            'total_sessions': session_counts_map.get(subject.id, 0),
            'att_pct': att_pct,
            'defaulter_count': defaulters_map.get(subject.id, 0),
            'enrolled': enrolled_counts.get((subject.department_id, subject.semester), 0),
        })

    now = timezone.localtime(timezone.now())
    today = now.date()

    marked_subject_ids = set(AttendanceSession.objects.filter(
        faculty=faculty, date=today
    ).values_list('subject_id', flat=True))

    day_map = {0:'MON',1:'TUE',2:'WED',3:'THU',4:'FRI',5:'SAT',6:'SUN'}
    today_day = day_map.get(today.weekday(), '')
    raw_timetable = Timetable.objects.filter(
        Q(faculty=faculty) | Q(substitutions__substitute_faculty=faculty, substitutions__date=today),
        day_of_week=today_day
    ).select_related('subject', 'classroom').order_by('start_time').distinct()
    today_timetable = list(raw_timetable)
    today_sessions = today_timetable

    # Full week timetable + matrix for the new matrix view
    week_days = ['MON','TUE','WED','THU','FRI','SAT']
    week_day_labels = {'MON':'Monday','TUE':'Tuesday','WED':'Wednesday','THU':'Thursday','FRI':'Friday','SAT':'Saturday'}
    all_week_slots = Timetable.objects.filter(faculty=faculty).select_related('subject','classroom').order_by('day_of_week','start_time').distinct()
    week_tt = {d: [] for d in week_days}
    for slot in all_week_slots:
        if slot.day_of_week in week_tt:
            week_tt[slot.day_of_week].append(slot)
    faculty_week_timetable = [(d, week_day_labels[d], week_tt[d]) for d in week_days]
    week_timetable_matrix = _build_weekly_timetable_matrix(
        all_week_slots,
        breaks=TimetableBreak.objects.filter(college=faculty.department.college, applies_to_all=True).order_by('day_of_week','start_time')
    )

    # Faculty availability slots
    availability_slots = FacultyAvailability.objects.filter(
        faculty=faculty, is_available=True
    ).order_by('day_of_week', 'start_time')

    my_requests_qs = HODApproval.objects.filter(requested_by=user).order_by('-created_at')

    # Recent attendance sessions — bulk fetch counts instead of 2 queries per session
    recent_sessions_qs = AttendanceSession.objects.filter(faculty=faculty).order_by('-date')[:10].select_related('subject')
    recent_session_list = list(recent_sessions_qs)
    recent_session_ids = [s.id for s in recent_session_list]
    sess_att_agg = Attendance.objects.filter(session_id__in=recent_session_ids).values('session_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    sess_att_map = {row['session_id']: row for row in sess_att_agg}
    recent_sessions = []
    for sess in recent_session_list:
        agg = sess_att_map.get(sess.id, {'total': 0, 'present': 0})
        recent_sessions.append({'session': sess, 'total': agg['total'], 'present': agg['present'],
                                 'absent': agg['total'] - agg['present']})

    pending_submissions_qs = AssignmentSubmission.objects.filter(
        assignment__created_by=user, marks__isnull=True
    ).select_related('student__user', 'assignment__subject')

    my_assignments = Assignment.objects.filter(created_by=user).select_related('subject').annotate(
        submission_count=Count('assignmentsubmission')
    ).order_by('-deadline')[:10]

    # Leave applications
    leave_history = LeaveApplication.objects.filter(faculty=faculty).order_by('-from_date')[:8]

    announcements = _scope_announcements_for_college(faculty.department.college).order_by('-created_at')[:5]

    # Today's breaks for faculty's college
    faculty_today_breaks = list(TimetableBreak.objects.filter(
        college=faculty.department.college, day_of_week=today_day, applies_to_all=True
    ).order_by('start_time'))

    context = {
        'faculty': faculty,
        'college': faculty.department.college,
        'subjects': subjects,
        'subject_cards': subject_cards,
        'total_subjects': len(subjects),
        'today_timetable': today_timetable,
        'today_sessions': today_sessions,
        'today_day': today_day,
        'today_breaks': faculty_today_breaks,
        'faculty_week_timetable': faculty_week_timetable,
        'week_timetable_matrix': week_timetable_matrix,
        'availability_slots': availability_slots,
        'marked_subject_ids': marked_subject_ids,
        'recent_sessions': recent_sessions,
        'pending_submissions': pending_submissions_qs[:10],
        'pending_submissions_count': pending_submissions_qs.count(),
        'my_requests': my_requests_qs[:5],
        'my_requests_count': my_requests_qs.filter(status='PENDING').count(),
        'my_assignments': my_assignments,
        'leave_history': leave_history,
        'announcements': announcements,
        'branding': _get_college_branding(faculty.department.college),
    }
    return render(request, 'dashboards/faculty.html', context)


@login_required
def faculty_request_add(request):
    """Allows faculty to submit requests to HOD."""
    try:
        faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        return redirect('dashboard')

    if request.method == 'POST':
        approval_type = request.POST.get('approval_type')
        description = request.POST.get('description', '').strip()
        
        if not description:
            messages.error(request, 'Please provide details for your request.')
        else:
            HODApproval.objects.create(
                requested_by=request.user,
                department=faculty.department,
                approval_type=approval_type,
                description=description
            )
            messages.success(request, 'Request submitted to HOD.')
            return redirect('faculty_dashboard')
    return render(request, 'faculty/request_form.html')


@login_required
def faculty_mark_attendance(request, subject_id):
    """Create an attendance session and mark students with Smart Locking."""
    subject = get_object_or_404(Subject, pk=subject_id)

    # Resolve the faculty doing the marking (could be a substitute)
    try:
        faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        faculty = None

    allowed, msg = _check_attendance_permission(request.user, subject)
    if not allowed:
        messages.error(request, msg)
        return redirect('dashboard')

    if msg: messages.info(request, msg)

    students = Student.objects.filter(
        department=subject.department,
        current_semester=subject.semester,
        status='ACTIVE',
        is_deleted=False
    ).select_related('user').order_by('roll_number')

    if request.method == 'POST':
        date_str = request.POST.get('date', str(timezone.now().date()))
        try:
            session_date = datetime.fromisoformat(date_str).date()
        except (ValueError, TypeError):
            session_date = timezone.now().date()

        if session_date > timezone.now().date():
            messages.error(request, 'Cannot mark attendance for a future date.')
            return redirect('faculty_dashboard')

        session = AttendanceSession.objects.filter(subject=subject, date=session_date).first()
        created = session is None
        if created:
            session = AttendanceSession.objects.create(
                subject=subject,
                faculty=faculty,
                date=session_date,
            )
        elif faculty and session.faculty_id != faculty.id:
            # Keep the existing record but reflect who handled the latest update.
            session.faculty = faculty
            session.save(update_fields=['faculty'])

        saved_count = 0
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'ABSENT')
            if status not in {'PRESENT', 'ABSENT', 'LATE'}:
                status = 'ABSENT'
            Attendance.objects.update_or_create(
                session=session,
                student=student,
                defaults={'status': status, 'marked_by': request.user},
            )
            saved_count += 1

        if created:
            messages.success(request, f'Attendance marked for {subject.name} on {session_date} for {saved_count} student(s).')
        else:
            messages.success(request, f'Attendance updated for {subject.name} on {session_date} for {saved_count} student(s).')
        return redirect('faculty_dashboard')

    context = {'subject': subject, 'students': students, 'today': timezone.now().date()}
    return render(request, 'faculty/mark_attendance.html', context)


@login_required
def faculty_enter_marks(request, subject_id, exam_id):
    """Enter marks for students in a subject/exam."""
    try:
        faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        return redirect('dashboard')

    faculty_subject = get_object_or_404(
        FacultySubject.objects.select_related('subject'),
        faculty=faculty,
        subject_id=subject_id,
    )
    subject = faculty_subject.subject
    exam = get_object_or_404(Exam, pk=exam_id, college=faculty.department.college)
    if exam.semester != subject.semester:
        raise PermissionDenied('This exam does not match the subject semester.')
    students = Student.objects.filter(
        department=subject.department,
        current_semester=subject.semester,
        status='ACTIVE'
    ).select_related('user').order_by('roll_number')

    existing_marks = {m.student_id: m for m in Marks.objects.filter(subject=subject, exam=exam)}
    student_rows = [{'student': student, 'existing_mark': existing_marks.get(student.id)} for student in students]

    if request.method == 'POST':
        try:
            max_marks = float(request.POST.get('max_marks', 100))
            if max_marks <= 0:
                raise ValueError
        except (TypeError, ValueError):
            max_marks = 100
        saved_count = 0
        error_count = 0
        for student in students:
            obtained_raw = request.POST.get(f'marks_{student.id}')
            if obtained_raw is not None and obtained_raw.strip() != '':
                try:
                    obtained = float(obtained_raw)
                except ValueError:
                    messages.error(request, f'Invalid marks for {student.roll_number}.')
                    error_count += 1
                    continue
                if obtained < 0:
                    messages.error(request, f'Marks cannot be negative for {student.roll_number}.')
                    error_count += 1
                    continue
                if obtained > max_marks:
                    messages.error(request, f'Marks {obtained} exceed max {max_marks} for {student.roll_number}.')
                    error_count += 1
                    continue
                grade = _calculate_grade(obtained, max_marks,
                    scheme=_get_evaluation_scheme(faculty.department.college, faculty.department))
                mark_obj, created = Marks.objects.update_or_create(
                    student=student, subject=subject, exam=exam,
                    defaults={
                        'marks_obtained': obtained,
                        'max_marks': max_marks,
                        'grade': grade,
                        'grade_point': _grade_to_point(grade),
                    }
                )
                _audit(
                    'MARKS_UPDATED' if not created else 'MARKS_ENTERED',
                    request.user,
                    f"{'Entered' if created else 'Updated'} marks for {student.roll_number} in {subject.code}: {obtained}/{max_marks} ({grade})",
                    student=student, college=faculty.department.college, request=request,
                )
                saved_count += 1
        if saved_count:
            messages.success(request, f'Marks saved for {saved_count} student(s) in {subject.name} — {exam.name}.')
        if error_count and not saved_count:
            messages.warning(request, 'No marks were saved because every entered row had validation issues.')
        return redirect('faculty_dashboard')

    context = {
        'subject': subject, 'exam': exam,
        'students': students,
        'student_rows': student_rows,
    }
    return render(request, 'faculty/enter_marks.html', context)


@login_required
def faculty_assignment_create(request):
    try:
        faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        return redirect('dashboard')

    subject_links = FacultySubject.objects.filter(faculty=faculty).select_related('subject').order_by('subject__name')
    subjects = [link.subject for link in subject_links]
    subject_ids = {subject.id for subject in subjects}

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        deadline_value = request.POST.get('deadline', '').strip()

        if not title or not description or not deadline_value:
            messages.error(request, 'Subject, title, description, and deadline are required.')
        elif not subject_id or int(subject_id) not in subject_ids:
            raise PermissionDenied('You can create assignments only for your own subjects.')
        else:
            Assignment.objects.create(
                subject_id=subject_id,
                title=title,
                description=description,
                deadline=_assignment_deadline_from_input(deadline_value),
                created_by=request.user,
            )
            messages.success(request, 'Assignment created successfully.')
            return redirect(f"{reverse('faculty_dashboard')}#submissions")

    return render(request, 'faculty/assignment_form.html', {'subjects': subjects})


@login_required
def faculty_assignment_publish(request, pk):
    """Finalize evaluation and publish results to students."""
    assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
    
    # Ensure at least some submissions are graded before publishing
    if not AssignmentSubmission.objects.filter(assignment=assignment, marks__isnull=False).exists():
        messages.warning(request, "Please evaluate at least one submission before publishing results.")
        return redirect('faculty_dashboard')

    assignment.is_published = True
    assignment.save(update_fields=['is_published'])
    messages.success(request, f"Results for '{assignment.title}' have been published to students.")
    return redirect('faculty_dashboard')


@login_required
def faculty_review_submission(request, pk):
    submission = get_object_or_404(
        AssignmentSubmission.objects.select_related('assignment__subject', 'student__user'),
        pk=pk,
        assignment__created_by=request.user,
    )
    if request.method == 'POST':
        marks_value = request.POST.get('marks', '').strip()
        if not marks_value:
            messages.error(request, 'Enter marks before saving the review.')
        else:
            submission.marks = float(marks_value)
            submission.feedback = request.POST.get('feedback', '').strip()
            submission.save(update_fields=['marks', 'feedback'])
            messages.success(request, 'Submission reviewed successfully.')
            return redirect(f"{reverse('faculty_dashboard')}#submissions")
    return render(request, 'faculty/review_submission.html', {'submission': submission})


def _get_evaluation_scheme(college, department=None):
    """
    Returns the active EvaluationScheme for a college/department.
    Falls back to college-wide scheme, then to hardcoded defaults.
    """
    qs = EvaluationScheme.objects.filter(college=college, is_active=True)
    if department:
        scheme = qs.filter(department=department).first()
        if scheme:
            return scheme
    return qs.filter(department__isnull=True).first()


def _calculate_grade(obtained, max_marks, scheme=None):
    """
    Calculate letter grade. Uses EvaluationScheme cutoffs if available,
    otherwise falls back to standard 10-point absolute scale.
    """
    if max_marks <= 0:
        return 'F'
    pct = (obtained / max_marks) * 100

    # If scheme defines custom passing minimum, use it for F boundary
    passing_min = scheme.overall_passing_min if scheme else 40.0

    if pct >= 90: return 'O'
    if pct >= 80: return 'A+'
    if pct >= 70: return 'A'
    if pct >= 60: return 'B+'
    if pct >= 50: return 'B'
    if pct >= passing_min: return 'C'
    return 'F'


GRADE_POINTS = {'O': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 'C': 5, 'F': 0}


def _grade_to_point(grade):
    return GRADE_POINTS.get(grade, 0)


def _compute_sgpa(student, semester, exam):
    """
    Compute SGPA for a student for a given semester.
    SGPA = Σ(credit × grade_point) / Σ(credits)
    Uses the Marks records for the given exam.
    """
    marks_qs = Marks.objects.filter(
        student=student, exam=exam,
        subject__semester=semester,
    ).select_related('subject')

    total_credit_points = 0.0
    total_credits = 0
    for m in marks_qs:
        credits = m.subject.credits or 0
        gp = _grade_to_point(m.grade or 'F')
        total_credit_points += credits * gp
        total_credits += credits

    sgpa = round(total_credit_points / total_credits, 2) if total_credits > 0 else 0.0
    return sgpa, total_credits


# ── FACULTY: QUIZ MANAGEMENT ─────────────────────────────────────────────────

@login_required
def faculty_quiz_list(request):
    faculty = get_object_or_404(Faculty, user=request.user)
    subject_ids = FacultySubject.objects.filter(faculty=faculty).values_list('subject_id', flat=True)
    quizzes = Quiz.objects.filter(subject_id__in=subject_ids).select_related('subject').order_by('-created_at')
    return render(request, 'faculty/quiz_list.html', {'quizzes': quizzes, 'faculty': faculty})


@login_required
def faculty_quiz_create(request):
    faculty = get_object_or_404(Faculty, user=request.user)
    subject_ids = list(FacultySubject.objects.filter(faculty=faculty).values_list('subject_id', flat=True))
    subjects = Subject.objects.filter(id__in=subject_ids)

    if request.method == 'POST':
        subject_id = _safe_int(request.POST.get('subject'))
        if subject_id not in subject_ids:
            raise PermissionDenied
        quiz = Quiz.objects.create(
            subject_id=subject_id,
            created_by=request.user,
            title=request.POST.get('title', '').strip(),
            description=request.POST.get('description', '').strip(),
            duration_minutes=_safe_int(request.POST.get('duration_minutes'), 30),
            total_marks=_safe_float(request.POST.get('total_marks'), 10),
        )
        messages.success(request, f'Quiz "{quiz.title}" created. Now add questions.')
        return redirect('faculty_quiz_edit', pk=quiz.pk)
    return render(request, 'faculty/quiz_form.html', {'subjects': subjects})


@login_required
def faculty_quiz_edit(request, pk):
    """Add/edit questions and options for a quiz."""
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    questions = quiz.questions.prefetch_related('options').all()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_question':
            q = QuizQuestion.objects.create(
                quiz=quiz,
                text=request.POST.get('q_text', '').strip(),
                question_type=request.POST.get('q_type', 'MCQ'),
                marks=_safe_float(request.POST.get('q_marks'), 1),
                order=questions.count() + 1,
            )
            # options: up to 4
            for i in range(1, 5):
                opt_text = request.POST.get(f'opt_{i}', '').strip()
                if opt_text:
                    QuizOption.objects.create(
                        question=q,
                        text=opt_text,
                        is_correct=(request.POST.get('correct_opt') == str(i)),
                    )
            messages.success(request, 'Question added.')

        elif action == 'delete_question':
            QuizQuestion.objects.filter(pk=request.POST.get('q_id'), quiz=quiz).delete()
            messages.success(request, 'Question removed.')

        elif action == 'toggle_active':
            if not quiz.questions.exists():
                messages.error(request, 'Add at least one question before activating.')
            else:
                quiz.is_active = not quiz.is_active
                quiz.save(update_fields=['is_active'])
                messages.success(request, f'Quiz {"activated" if quiz.is_active else "deactivated"}.')

        return redirect('faculty_quiz_edit', pk=quiz.pk)

    return render(request, 'faculty/quiz_edit.html', {'quiz': quiz, 'questions': questions})


@login_required
def faculty_quiz_results(request, pk):
    """View all student attempts and scores for a quiz."""
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    attempts = QuizAttempt.objects.filter(quiz=quiz, is_submitted=True).select_related('student__user').order_by('-score')
    return render(request, 'faculty/quiz_results.html', {'quiz': quiz, 'attempts': attempts})


# ── FACULTY: INTERNAL MARKS ──────────────────────────────────────────────────

@login_required
def faculty_internal_marks(request, subject_id):
    """Enter/update IA1, IA2, assignment, attendance marks for all students in a subject."""
    faculty = get_object_or_404(Faculty, user=request.user)
    get_object_or_404(FacultySubject, faculty=faculty, subject_id=subject_id)
    subject = get_object_or_404(Subject, pk=subject_id)

    students = Student.objects.filter(
        department=subject.department,
        current_semester=subject.semester,
        status='ACTIVE', is_deleted=False,
    ).select_related('user').order_by('roll_number')

    existing = {im.student_id: im for im in InternalMark.objects.filter(subject=subject, student__in=students)}

    if request.method == 'POST':
        with transaction.atomic():
            for student in students:
                def _fv(key, max_val):
                    v = request.POST.get(f'{key}_{student.id}', '').strip()
                    if not v:
                        return None
                    try:
                        val = float(v)
                    except ValueError:
                        return None
                    return min(max(val, 0), max_val)

                im, _ = InternalMark.objects.get_or_create(
                    student=student, subject=subject,
                    defaults={'entered_by': request.user}
                )
                im.ia1 = _fv('ia1', 30)
                im.ia2 = _fv('ia2', 30)
                im.assignment_marks = _fv('assignment', 20)
                im.attendance_marks = _fv('attendance', 5)
                im.entered_by = request.user
                im.save()
        messages.success(request, f'Internal marks saved for {subject.name}.')
        return redirect('faculty_dashboard')

    rows = [{'student': s, 'im': existing.get(s.id)} for s in students]
    return render(request, 'faculty/internal_marks.html', {'subject': subject, 'rows': rows})


# ── FACULTY: ATTENDANCE DEFAULTERS ───────────────────────────────────────────

@login_required
def faculty_attendance_defaulters(request, subject_id):
    """Show students below the configured attendance threshold for a subject."""
    faculty = get_object_or_404(Faculty, user=request.user)
    subject = get_object_or_404(Subject, pk=subject_id)

    att_rule = _get_attendance_rule(subject.department.college, subject.department, subject.semester)
    threshold = att_rule.effective_min_subject

    students = Student.objects.filter(
        department=subject.department,
        current_semester=subject.semester,
        status='ACTIVE', is_deleted=False,
    ).select_related('user').order_by('roll_number')

    stats = Attendance.objects.filter(
        session__subject=subject, student__in=students
    ).values('student').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT')),
    )
    stats_map = {s['student']: s for s in stats}

    rows = []
    for student in students:
        s = stats_map.get(student.id, {'total': 0, 'present': 0})
        pct = round(s['present'] / s['total'] * 100, 1) if s['total'] else 0
        rows.append({
            'student': student, 'present': s['present'], 'total': s['total'],
            'pct': pct, 'is_defaulter': pct < threshold and s['total'] > 0,
            'threshold': threshold,
        })

    rows.sort(key=lambda r: r['pct'])
    return render(request, 'faculty/attendance_defaulters.html', {
        'subject': subject, 'rows': rows, 'threshold': threshold,
    })


# ── FACULTY: LESSON PLANS ────────────────────────────────────────────────────

@login_required
def faculty_lesson_plans(request, subject_id):
    faculty = get_object_or_404(Faculty, user=request.user)
    get_object_or_404(FacultySubject, faculty=faculty, subject_id=subject_id)
    subject = get_object_or_404(Subject, pk=subject_id)
    plans = LessonPlan.objects.filter(faculty=faculty, subject=subject).order_by('unit_number', 'planned_date')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            LessonPlan.objects.create(
                subject=subject, faculty=faculty,
                unit_number=_safe_int(request.POST.get('unit_number'), 1),
                unit_title=request.POST.get('unit_title', '').strip(),
                topics=request.POST.get('topics', '').strip(),
                planned_hours=_safe_int(request.POST.get('planned_hours'), 1),
                planned_date=request.POST.get('planned_date'),
                remarks=request.POST.get('remarks', '').strip(),
                file=request.FILES.get('file'),
                status='SUBMITTED',
            )
            messages.success(request, 'Lesson plan entry added.')
        elif action == 'delete':
            LessonPlan.objects.filter(pk=request.POST.get('plan_id'), faculty=faculty).delete()
            messages.success(request, 'Entry removed.')
        elif action == 'mark_done':
            plan = get_object_or_404(LessonPlan, pk=request.POST.get('plan_id'), faculty=faculty)
            plan.actual_date = timezone.now().date()
            plan.status = 'SUBMITTED'
            plan.save(update_fields=['actual_date', 'status'])
            messages.success(request, 'Marked as completed.')
        return redirect('faculty_lesson_plans', subject_id=subject_id)

    return render(request, 'faculty/lesson_plans.html', {'subject': subject, 'plans': plans, 'faculty': faculty})


# ── FACULTY: LEAVE APPLICATION ────────────────────────────────────────────────

@login_required
def faculty_leave_apply(request):
    faculty = get_object_or_404(Faculty, user=request.user)
    # Other faculty in same dept for substitute suggestion
    dept_faculty = Faculty.objects.filter(
        department=faculty.department, is_deleted=False
    ).exclude(pk=faculty.pk).select_related('user')

    my_leaves = LeaveApplication.objects.filter(faculty=faculty).order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action', 'apply')
        if action == 'apply':
            from_date = request.POST.get('from_date')
            to_date = request.POST.get('to_date')
            leave_type = request.POST.get('leave_type', 'CL')
            reason = request.POST.get('reason', '').strip()
            sub_id = _safe_int(request.POST.get('suggested_substitute'), 0)
            substitute = Faculty.objects.filter(pk=sub_id, department=faculty.department).first() if sub_id else None

            if not from_date or not to_date or not reason:
                messages.error(request, 'From date, to date, and reason are required.')
            elif from_date > to_date:
                messages.error(request, 'From date must be before or equal to to date.')
            else:
                from datetime import date as _date
                fd = datetime.fromisoformat(from_date).date()
                td = datetime.fromisoformat(to_date).date()
                if fd < timezone.now().date():
                    messages.error(request, 'Cannot apply for leave in the past.')
                elif LeaveApplication.objects.filter(
                    faculty=faculty,
                    status__in=['PENDING', 'APPROVED'],
                    from_date__lte=td,
                    to_date__gte=fd,
                ).exists():
                    messages.error(request, 'You already have a leave application overlapping these dates.')
                else:
                    LeaveApplication.objects.create(
                        faculty=faculty,
                        leave_type=leave_type,
                        from_date=from_date,
                        to_date=to_date,
                        reason=reason,
                        suggested_substitute=substitute,
                    )
                    messages.success(request, 'Leave application submitted to HOD.')
                    return redirect('faculty_leave_apply')
        elif action == 'cancel':
            LeaveApplication.objects.filter(
                pk=request.POST.get('leave_id'), faculty=faculty, status='PENDING'
            ).delete()
            messages.success(request, 'Application withdrawn.')
            return redirect('faculty_leave_apply')

    # Show affected timetable slots for awareness
    timetable_slots = Timetable.objects.filter(faculty=faculty).select_related('subject', 'classroom').order_by('day_of_week', 'start_time')

    return render(request, 'faculty/leave_apply.html', {
        'faculty': faculty,
        'dept_faculty': dept_faculty,
        'my_leaves': my_leaves,
        'timetable_slots': timetable_slots,
    })


# ── STUDENT DASHBOARD ────────────────────────────────────

@login_required
def faculty_availability_add(request):
    """Faculty adds a free availability slot from their timetable page."""
    if request.method != 'POST':
        return redirect('faculty_dashboard')
    faculty = get_object_or_404(Faculty, user=request.user)
    day   = request.POST.get('day_of_week', '').strip().upper()
    start = request.POST.get('start_time', '').strip()
    end   = request.POST.get('end_time', '').strip()
    if day and start and end:
        FacultyAvailability.objects.get_or_create(
            faculty=faculty, day_of_week=day, start_time=start, end_time=end,
            defaults={'is_available': True}
        )
        messages.success(request, f'Free slot added: {day} {start}–{end}.')
    else:
        messages.error(request, 'Day, start time, and end time are required.')
    return redirect(f"{reverse('faculty_dashboard')}#timetable")


@login_required
def faculty_availability_delete(request, pk):
    """Faculty removes an availability slot."""
    if request.method == 'POST':
        FacultyAvailability.objects.filter(pk=pk, faculty__user=request.user).delete()
        messages.success(request, 'Slot removed.')
    return redirect(f"{reverse('faculty_dashboard')}#timetable")


@login_required
def student_dashboard(request):
    user = request.user
    try:
        student = Student.objects.select_related('user', 'department').get(user=user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Contact admin.')
        return redirect('home')

    # Attendance per subject — rule engine drives all thresholds
    subjects = Subject.objects.filter(
        department=student.department,
        semester=student.current_semester
    )
    college = student.department.college
    att_rule = _get_attendance_rule(college, student.department, student.current_semester)
    alert_threshold   = att_rule.alert_below_pct
    critical_threshold = att_rule.critical_below_pct
    min_threshold     = att_rule.effective_min_subject

    attendance_stats = Attendance.objects.filter(student=student, session__subject__in=subjects).values('session__subject').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    stats_dict = {item['session__subject']: item for item in attendance_stats}

    absence_records = Attendance.objects.filter(
        student=student, session__subject__in=subjects, status='ABSENT'
    ).select_related('session__subject').order_by('session__date')

    # All attendance records for calendar/log view
    all_att_records = Attendance.objects.filter(
        student=student, session__subject__in=subjects
    ).select_related('session__subject', 'session__faculty__user').order_by('-session__date', 'session__subject__name')
    absence_map = {}
    for rec in absence_records:
        sid = rec.session.subject_id
        absence_map.setdefault(sid, []).append(rec.session.date)

    attendance_data = []
    overall_present = 0
    overall_total = 0

    today_date = timezone.now().date()
    existing_notif_messages = set(
        Notification.objects.filter(user=user, created_at__date=today_date)
        .values_list('message', flat=True)
    )

    for subj in subjects:
        s = stats_dict.get(subj.id, {'total': 0, 'present': 0})
        pct = round((s['present'] / s['total'] * 100), 1) if s['total'] > 0 else 0
        is_low = pct < alert_threshold if s['total'] > 0 else False
        is_critical = pct < critical_threshold if s['total'] > 0 else False

        if is_low:
            alert_msg = f"Smart Alert: Your attendance in {subj.name} is below {alert_threshold}% ({pct}%). ⚠️"
            if alert_msg not in existing_notif_messages:
                Notification.objects.create(user=user, message=alert_msg)
                existing_notif_messages.add(alert_msg)

        present = s['present']
        total = s['total']
        classes_needed = None
        if total > 0 and pct < min_threshold:
            x = (min_threshold / 100 * total - present) / (1 - min_threshold / 100)
            classes_needed = max(0, int(x) + (1 if x % 1 > 0 else 0))
        can_miss = None
        if total > 0 and pct >= min_threshold:
            x = present / (min_threshold / 100) - total
            can_miss = max(0, int(x))

        attendance_data.append({
            'subject': subj, 'present': present, 'total': total, 'pct': pct,
            'is_low': is_low, 'is_critical': is_critical,
            'classes_needed': classes_needed, 'can_miss': can_miss,
            'absent_dates': absence_map.get(subj.id, []),
            'threshold': min_threshold,
        })
        overall_present += present
        overall_total += total

    overall_attendance = round((overall_present / overall_total * 100), 1) if overall_total > 0 else None

    # Compute eligibility using rule engine (shown in student dashboard)
    eligibility = _compute_eligibility(student, student.current_semester, college)

    # Results — enrich breakdown with best/worst subject and grade distribution
    result_breakdown, results = _student_result_breakdown(student)
    for item in result_breakdown:
        marks_list = item.get('marks', [])
        if marks_list:
            valid = [m for m in marks_list if m.max_marks > 0]
            if valid:
                scored = lambda m: m.marks_obtained / m.max_marks
                item['best_subject'] = max(valid, key=scored)
                item['worst_subject'] = min(valid, key=scored)
                grade_counts = {}
                for m in valid:
                    g = m.grade or 'NA'
                    grade_counts[g] = grade_counts.get(g, 0) + 1
                item['grade_counts'] = grade_counts
    latest_result = results.first()

    # CGPA — weighted by total marks (more accurate than simple average)
    cgpa = None
    if results.exists():
        total_weighted = sum(r.gpa * r.total_marks for r in results if r.total_marks > 0)
        total_marks_sum = sum(r.total_marks for r in results if r.total_marks > 0)
        if total_marks_sum > 0:
            cgpa = round(total_weighted / total_marks_sum, 2)
        else:
            cgpa = round(sum(r.gpa for r in results) / results.count(), 2)

    # Backlog count — subjects where student has failed (marks < 40% of max)
    all_marks = Marks.objects.filter(student=student).select_related('subject', 'exam')
    backlog_subjects = set()
    passed_subjects = set()
    for m in all_marks:
        passing = m.max_marks * 0.4
        if m.marks_obtained < passing:
            backlog_subjects.add(m.subject_id)
        else:
            passed_subjects.add(m.subject_id)
    # Remove subjects that were later cleared
    active_backlogs = backlog_subjects - passed_subjects
    backlog_count = len(active_backlogs)

    # Academic standing
    year_of_study = ((student.current_semester - 1) // 2) + 1
    if cgpa is None:
        academic_standing = 'No Results'
    elif cgpa >= 8.5:
        academic_standing = 'Distinction'
    elif cgpa >= 7.0:
        academic_standing = 'First Class'
    elif cgpa >= 6.0:
        academic_standing = 'Second Class'
    elif cgpa >= 5.0:
        academic_standing = 'Pass'
    else:
        academic_standing = 'At Risk'

    # Academic probation if attendance < 75% or backlog > 2
    on_probation = (overall_attendance is not None and overall_attendance < 75) or backlog_count > 2

    profile = StudentProfile.objects.filter(user=user).first()
    address = Address.objects.filter(user=user).order_by('id').first()
    parent = Parent.objects.filter(user=user).order_by('id').first()
    emergency_contact = EmergencyContact.objects.filter(user=user).order_by('id').first()

    # Fee — all semester fees for this student
    fee = Fee.objects.filter(student=student).order_by('-semester', '-id').first()
    all_fees = Fee.objects.filter(student=student).order_by('semester')
    balance_due = max((fee.total_amount - fee.paid_amount), 0) if fee else 0
    total_fees_due = sum(max(f.total_amount - f.paid_amount, 0) for f in all_fees)
    if balance_due > 0:
        fee_msg = f"Fee Reminder: A balance of Rs {balance_due:.0f} is pending. Please clear it soon."
        if fee_msg not in existing_notif_messages:
            Notification.objects.create(user=user, message=fee_msg)

    recent_payments = Payment.objects.filter(fee=fee).order_by('-paid_at', '-created_at')[:5] if fee else []

    # Timetable today — use localtime so IST date is correct
    today = timezone.localtime(timezone.now()).date()
    day_map = {0:'MON',1:'TUE',2:'WED',3:'THU',4:'FRI',5:'SAT',6:'SUN'}
    today_day = day_map.get(today.weekday(), '')
    
    now_time = timezone.localtime(timezone.now()).time()
    raw_timetable = Timetable.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
        day_of_week=today_day,
    ).filter(
        Q(section='') | Q(section=student.section)
    ).select_related('subject','faculty__user','classroom').order_by('start_time').distinct()

    today_timetable = list(raw_timetable)

    # Today's attendance status per subject (for timetable view)
    today_sessions = AttendanceSession.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
        date=today
    ).values_list('subject_id', flat=True)
    today_attendance_map = {}
    if today_sessions:
        today_att = Attendance.objects.filter(
            student=student,
            session__date=today,
            session__subject__department=student.department,
        ).select_related('session__subject')
        for att in today_att:
            today_attendance_map[att.session.subject_id] = att.status

    # Enrich today_timetable with attendance status
    today_timetable_enriched = []
    for slot in today_timetable:
        today_timetable_enriched.append({
            'slot': slot,
            'att_status': today_attendance_map.get(slot.subject_id),  # PRESENT/ABSENT/LATE/None
        })

    # Today's breaks for this college
    today_breaks = list(TimetableBreak.objects.filter(
        college=college, day_of_week=today_day, applies_to_all=True
    ).order_by('start_time'))

    # Assignment Tracking: Lifecycle View
    pending_assignments_qs = Assignment.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
        deadline__gte=timezone.now()
    ).exclude(
        assignmentsubmission__student=student
    ).select_related('subject').order_by('deadline')

    # Enrich with urgency flag for template
    from datetime import timedelta as _tdelta
    _now = timezone.now()
    pending_assignments_list = []
    for a in pending_assignments_qs[:5]:
        delta = a.deadline - _now
        if delta.days < 2:
            urgency = 'urgent'
        elif delta.days < 5:
            urgency = 'soon'
        else:
            urgency = 'ok'
        pending_assignments_list.append({'assignment': a, 'urgency': urgency, 'days_left': delta.days})

    # Submitted but evaluation pending
    submitted_assignments = AssignmentSubmission.objects.filter(
        student=student, marks__isnull=True
    ).select_related('assignment__subject').order_by('-submitted_at')[:5]

    # Evaluated and published
    evaluated_assignments = AssignmentSubmission.objects.filter(
        student=student, marks__isnull=False, assignment__is_published=True
    ).select_related('assignment__subject').order_by('-submitted_at')[:5]

    # Announcements
    announcements = _scope_announcements_for_college(student.department.college).order_by('-created_at')[:5]

    # Course structure — all subjects for current semester with faculty
    course_subjects = Subject.objects.filter(
        department=student.department,
        semester=student.current_semester
    ).prefetch_related('facultysubject_set__faculty__user').order_by('name')

    # Internal marks for current semester
    internal_marks = InternalMark.objects.filter(
        student=student,
        subject__department=student.department,
        subject__semester=student.current_semester,
    ).select_related('subject')
    internal_map = {im.subject_id: im for im in internal_marks}
    internal_data = [{'subject': s, 'im': internal_map.get(s.id)} for s in course_subjects]

    # All-semester internal marks grouped by semester
    all_internal_marks = InternalMark.objects.filter(
        student=student,
        subject__department=student.department,
    ).select_related('subject').order_by('subject__semester', 'subject__name')
    all_internal_by_sem = {}
    for im in all_internal_marks:
        sem = im.subject.semester
        all_internal_by_sem.setdefault(sem, []).append(im)
    all_internal_semesters = sorted(all_internal_by_sem.keys())
    all_internal_list = [(sem, all_internal_by_sem[sem]) for sem in all_internal_semesters]

    # Active quizzes for student's subjects
    active_quizzes = Quiz.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
        is_active=True,
    ).select_related('subject').order_by('-created_at')
    attempted_quiz_ids = set(QuizAttempt.objects.filter(student=student, is_submitted=True).values_list('quiz_id', flat=True))

    # What's New feed — last 7 days activity
    from datetime import timedelta as _td
    week_ago = timezone.now() - _td(days=7)
    new_assignments = Assignment.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
        deadline__gte=timezone.now(),
    ).exclude(assignmentsubmission__student=student).order_by('deadline')[:3]
    new_announcements = announcements[:3]
    new_quizzes = active_quizzes.filter(created_at__gte=week_ago)[:3]

    # All-semester attendance (for academic track depth) — scoped to student's dept, capped
    all_att_stats = Attendance.objects.filter(
        student=student, session__subject__department=student.department
    ).values('session__subject__semester').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    ).order_by('session__subject__semester')
    att_by_semester = []
    for row in all_att_stats:
        sem = row['session__subject__semester']
        pct = round(row['present'] / row['total'] * 100, 1) if row['total'] > 0 else 0
        att_by_semester.append({'semester': sem, 'pct': pct, 'present': row['present'], 'total': row['total']})

    # last_semester = None
    # last_sem_pct = None
    # if student.current_semester:
    #     last_semester = student.current_semester - 1
    #     if last_semester >= 1:
    #         for row in att_by_semester:
    #             if row['semester'] == last_semester:
    #                 last_sem_pct = row['pct']
    #                 break
    #     else:
    #         last_semester = None

    # Create a fast lookup dictionary from the existing data
    db_stats = {row['semester']: row['pct'] for row in att_by_semester}
    
    # Generate a padded list of ALL past semesters (Current-1 down to Sem 1)
    past_semesters_summary = []
    if student.current_semester > 1:
        for sem in range(student.current_semester - 1, 0, -1):
            past_semesters_summary.append({
                'semester': sem,
                'pct': db_stats.get(sem, None) # Will be None if no data exists
            })

    # Assignment score trend — capped at 50 most recent graded submissions
    all_graded = AssignmentSubmission.objects.filter(
        student=student, marks__isnull=False
    ).select_related('assignment__subject').order_by('-submitted_at')[:50]
    assignment_score_trend = [
        {
            'title': s.assignment.title,
            'subject': s.assignment.subject.name,
            'marks': s.marks,
            'date': s.submitted_at,
            'feedback': s.feedback,
        }
        for s in all_graded
    ]

    # All payments for fee timeline
    all_payments = Payment.objects.filter(fee=fee).order_by('paid_at', 'created_at') if fee else []
    fee_timeline = []
    running = 0
    for p in all_payments:
        running += p.amount
        fee_timeline.append({'payment': p, 'running_total': running})

    # Track which fee types have already been paid (SUCCESS) for this semester
    # Used to disable already-paid components on the fee page
    paid_fee_types = set(
        Payment.objects.filter(fee=fee, status='SUCCESS')
        .values_list('payment_type', flat=True)
    ) if fee else set()

    # Academic track — CGPA per semester
    semester_results = results.order_by('semester')

    # Full week timetable (Mon–Sat)
    from datetime import timedelta as _td2
    week_days = ['MON','TUE','WED','THU','FRI','SAT']
    week_day_labels = {'MON':'Monday','TUE':'Tuesday','WED':'Wednesday','THU':'Thursday','FRI':'Friday','SAT':'Saturday'}
    all_week_slots = Timetable.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
    ).filter(
        Q(section='') | Q(section=student.section)
    ).select_related('subject','faculty__user','classroom').order_by('day_of_week','start_time').distinct()
    week_timetable = {d: [] for d in week_days}
    for slot in all_week_slots:
        if slot.day_of_week in week_timetable:
            week_timetable[slot.day_of_week].append(slot)
    week_timetable_list = [(d, week_day_labels[d], week_timetable[d]) for d in week_days]
    week_timetable_matrix = _build_weekly_timetable_matrix(all_week_slots, breaks=TimetableBreak.objects.filter(
        college=college,
        applies_to_all=True,
    ).order_by('day_of_week', 'start_time'))

    # Quiz history — submitted attempts
    quiz_history = QuizAttempt.objects.filter(
        student=student, is_submitted=True
    ).select_related('quiz__subject').order_by('-submitted_at')[:20]

    context = {
        'student': student,
        'college': student.department.college,
        'profile': profile,
        'address': address,
        'parent': parent,
        'emergency_contact': emergency_contact,
        'attendance_data': attendance_data,
        'overall_attendance': overall_attendance,
        'results': results,
        'result_breakdown': result_breakdown,
        'latest_result': latest_result,
        'cgpa': cgpa,
        'fee': fee,
        'balance_due': balance_due,
        'recent_payments': recent_payments,
        'today_timetable': today_timetable_enriched,
        'week_timetable_list': week_timetable_list,
        'today_day': today_day,
        'today_attendance_map': today_attendance_map,
        'today_breaks': today_breaks,
        'week_timetable_matrix': week_timetable_matrix,
        'pending_assignments': pending_assignments_list,
        'pending_assignments_count': pending_assignments_qs.count(),
        'submitted_assignments': submitted_assignments,
        'evaluated_assignments': evaluated_assignments,
        'announcements': announcements,
        'notifications': Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:10],
        'course_subjects': course_subjects,
        'internal_data': internal_data,
        'active_quizzes': active_quizzes,
        'attempted_quiz_ids': attempted_quiz_ids,
        'quiz_history': quiz_history,
        'new_assignments': new_assignments,
        'new_announcements': new_announcements,
        'new_quizzes': new_quizzes,
        'semester_results': semester_results,
        'subjects': subjects,
        'branding': _get_college_branding(student.department.college),
        'now': timezone.now(),
        'all_internal_by_sem': all_internal_by_sem,
        'all_internal_semesters': all_internal_semesters,
        'all_internal_list': all_internal_list,
        'att_by_semester': att_by_semester,
        # 'last_semester': last_semester,
        # 'last_sem_pct': last_sem_pct,
        'all_att_records': all_att_records,
        'eligibility': eligibility,
        'att_rule': att_rule,
        'assignment_score_trend': assignment_score_trend,
        'fee_timeline': fee_timeline,
        'backlog_count': backlog_count,
        'year_of_study': year_of_study,
        'academic_standing': academic_standing,
        'on_probation': on_probation,
        'all_fees': all_fees,
        'total_fees_due': total_fees_due,
        'paid_fee_types': paid_fee_types,
        'past_semesters_summary': past_semesters_summary,
    }
    return render(request, 'dashboards/student.html', context)


@login_required
def student_profile_edit(request):
    try:
        student = Student.objects.select_related('user', 'department').get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Contact admin.')
        return redirect('home')

    profile = StudentProfile.objects.filter(user=request.user).first()
    address = Address.objects.filter(user=request.user).order_by('id').first()
    parent = Parent.objects.filter(user=request.user).order_by('id').first()
    emergency_contact = EmergencyContact.objects.filter(user=request.user).order_by('id').first()

    if request.method == 'POST':
        try:
            with transaction.atomic():
                request.user.first_name = request.POST.get('first_name', '').strip()
                request.user.last_name = request.POST.get('last_name', '').strip()
                request.user.email = request.POST.get('email', '').strip()
                request.user.save()

                profile_data = {
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'date_of_birth': request.POST.get('date_of_birth'),
                    'gender': request.POST.get('gender'),
                    'phone_number': request.POST.get('phone_number', '').strip(),
                    'aadhaar_number': request.POST.get('aadhaar_number', '').strip(),
                    'inter_college_name': request.POST.get('inter_college_name', '').strip(),
                    'inter_passed_year': _safe_int(request.POST.get('inter_passed_year')),
                    'inter_percentage': _safe_float(request.POST.get('inter_percentage')),
                    'school_name': request.POST.get('school_name', '').strip(),
                    'school_passed_year': _safe_int(request.POST.get('school_passed_year')),
                    'school_percentage': _safe_float(request.POST.get('school_percentage')),
                    'blood_group': request.POST.get('blood_group', '').strip() or None,
                    'nationality': request.POST.get('nationality', '').strip() or 'Indian',
                    'category': request.POST.get('category', '').strip() or None,
                }
                if profile is None:
                    profile = StudentProfile.objects.create(user=request.user, **profile_data)
                else:
                    for field, value in profile_data.items():
                        setattr(profile, field, value)
                    profile.save()
                
                if request.FILES.get('profile_photo'):
                    profile.profile_photo = request.FILES['profile_photo']
                    profile.save(update_fields=['profile_photo'])

                address_data = {
                    'street': request.POST.get('street', '').strip(),
                    'city': request.POST.get('city', '').strip(),
                    'state': request.POST.get('state', '').strip(),
                    'pincode': request.POST.get('pincode', '').strip(),
                    'country': request.POST.get('country', '').strip() or 'India',
                }
                if address is None:
                    Address.objects.create(user=request.user, **address_data)
                else:
                    for field, value in address_data.items():
                        setattr(address, field, value)
                    address.save()

                parent_data = {
                    'parent_type': request.POST.get('parent_type', '').strip() or 'FATHER',
                    'name': request.POST.get('parent_name', '').strip(),
                    'phone_number': request.POST.get('parent_phone_number', '').strip(),
                    'email': request.POST.get('parent_email', '').strip() or None,
                    'occupation': request.POST.get('parent_occupation', '').strip() or None,
                }
                if parent is None:
                    Parent.objects.create(user=request.user, **parent_data)
                else:
                    for field, value in parent_data.items():
                        setattr(parent, field, value)
                    parent.save()

                emergency_data = {
                    'name': request.POST.get('emergency_name', '').strip(),
                    'relation': request.POST.get('emergency_relation', '').strip(),
                    'phone_number': request.POST.get('emergency_phone_number', '').strip(),
                }
                if emergency_contact is None:
                    EmergencyContact.objects.create(user=request.user, **emergency_data)
                else:
                    for field, value in emergency_data.items():
                        setattr(emergency_contact, field, value)
                    emergency_contact.save()

            messages.success(request, 'Profile updated successfully.')
            return redirect(f"{reverse('student_dashboard')}#profile")
        except Exception as e:
            messages.error(request, f"Error updating profile: {str(e)}")

    context = {
        'student': student,
        'profile': profile,
        'address': address,
        'parent': parent,
        'emergency_contact': emergency_contact,
    }
    return render(request, 'student/profile_form.html', context)


@login_required
def student_submit_assignment(request, pk):
    try:
        student = Student.objects.select_related('department').get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Contact admin.')
        return redirect('home')

    assignment = get_object_or_404(
        Assignment.objects.select_related('subject'),
        pk=pk,
        subject__department=student.department,
        subject__semester=student.current_semester,
    )
    if assignment.deadline < timezone.now():
        messages.error(request, 'This assignment deadline has already passed.')
        return redirect(f"{reverse('student_dashboard')}#assignments")

    existing_submission = AssignmentSubmission.objects.filter(assignment=assignment, student=student).first()
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            messages.error(request, 'Choose a file before submitting.')
        elif existing_submission is None:
            AssignmentSubmission.objects.create(assignment=assignment, student=student, file=uploaded_file)
            messages.success(request, 'Assignment submitted successfully.')
            return redirect(f"{reverse('student_dashboard')}#assignments")
        else:
            existing_submission.file = uploaded_file
            existing_submission.submitted_at = timezone.now()
            existing_submission.save()
            messages.success(request, 'Assignment submission updated successfully.')
            return redirect(f"{reverse('student_dashboard')}#assignments")

    return render(request, 'student/assignment_submit.html', {
        'student': student,
        'assignment': assignment,
        'existing_submission': existing_submission,
    })


def _get_razorpay_client():
    from django.conf import settings as _s
    try:
        import razorpay
    except ImportError:
        raise ImportError("razorpay package is not installed. Run: pip install razorpay")
    key_id = _s.RAZORPAY_KEY_ID
    key_secret = _s.RAZORPAY_KEY_SECRET
    if not key_id or not key_secret:
        raise ValueError("Razorpay keys not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env")
    return razorpay.Client(auth=(key_id, key_secret))


@login_required
def student_fee_payment(request):
    try:
        student = Student.objects.select_related('department').get(user=request.user)
        fee = Fee.objects.filter(student=student).order_by('-semester').first()
        if not fee:
            raise Fee.DoesNotExist
    except (Student.DoesNotExist, Fee.DoesNotExist):
        messages.error(request, 'Fee record not found. Contact admin.')
        return redirect('home')

    from django.conf import settings as _s
    # Backfill semester/academic_year if missing on the fee record
    if fee.semester is None:
        fee.semester = student.current_semester
        year_offset  = (student.current_semester - 1) // 2
        start_year   = student.admission_year + year_offset
        fee.academic_year = fee.academic_year or f"{start_year}-{str(start_year+1)[-2:]}"
        fee.save(update_fields=['semester', 'academic_year'])
    balance_due = max(Decimal(str(fee.total_amount)) - Decimal(str(fee.paid_amount)), Decimal('0'))
    razorpay_enabled = bool(_s.RAZORPAY_KEY_ID and _s.RAZORPAY_KEY_SECRET)
    tuition_fee_types = {'TUITION', 'TUITION_REG', 'TUITION_LATERAL', 'SEM_FEE'}

    # Manual payment fallback (when Razorpay not configured)
    if request.method == 'POST' and request.POST.get('manual_payment'):
        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except InvalidOperation:
            amount = Decimal('0')
        payment_method = request.POST.get('payment_method', 'Cash Counter').strip()
        fee_type = request.POST.get('fee_type', 'TUITION').strip().upper()
        allowed_fee_types = {'TUITION', 'EXAM', 'LIBRARY', 'SPORTS', 'MISC'}
        if fee_type not in allowed_fee_types:
            fee_type = 'TUITION'
        if amount <= 0:
            messages.error(request, 'Enter a valid amount greater than zero.')
        elif fee_type == 'TUITION' and amount > balance_due:
            messages.error(request, f'Amount ₹{amount} exceeds balance due ₹{balance_due:.0f}.')
        else:
            with transaction.atomic():
                payment = Payment.objects.create(
                    user=request.user,
                    fee=fee,
                    amount=float(amount),
                    payment_type=fee_type,
                    transaction_id=f"MAN-{timezone.now():%Y%m%d%H%M%S}-{uuid4().hex[:6].upper()}",
                    status='SUCCESS',
                    payment_method=payment_method,
                    paid_at=timezone.now(),
                )
                if fee_type in tuition_fee_types:
                    fee.paid_amount = float(Decimal(str(fee.paid_amount)) + amount)
                    _sync_fee_status(fee)
                    fee.save(update_fields=['paid_amount', 'status'])
            messages.success(request, 'Payment recorded successfully.')
            return redirect('student_payment_receipt', pk=payment.pk)

    # Load or auto-generate fee breakdown for this student's fee structure
    structure = FeeStructure.objects.filter(
        department=student.department,
        semester=fee.semester or student.current_semester
    ).first()

    fee_breakdown_map = {}
    if structure:
        for bd in structure.breakdowns.all():
            fee_breakdown_map[bd.category] = bd.amount

    # Default amounts if no breakdown configured (realistic Indian college fees)
    DEFAULT_FEE_AMOUNTS = {
        'TUITION_REG':     fee.total_amount,
        'TUITION_LATERAL': fee.total_amount,
        'SEM_FEE':         fee.total_amount,
        'EXAM_REG':        1500.0,
        'EXAM_BACK':       500.0,
        'EXAM_IMPROVE':    750.0,
        'EXAM_REVAL':      300.0,
        'EXAM_PHOTOCOPY':  100.0,
        'LAB_FEE':         2000.0,
        'LIBRARY_FEE':     500.0,
        'SPORTS_FEE':      500.0,
        'TRANSPORT_FEE':   0.0,
        'HOSTEL_FEE':      0.0,
        'CAUTION_DEPOSIT': 2000.0,
        'MISC':            0.0,
    }
    # Merge: configured values override defaults
    fee_amounts = {**DEFAULT_FEE_AMOUNTS, **fee_breakdown_map}

    # Build display list: only components with amount > 0
    COMPONENT_LABELS = {
        'TUITION':  'Tuition Fee',
        'EXAM':     'Exam Fee',
        'LIBRARY':  'Library Fee',
        'SPORTS':   'Sports & Cultural Fee',
        'MISC':     'Miscellaneous',
    }
    # Default amounts if no breakdown configured
    DEFAULT_AMOUNTS = {
        'TUITION': fee.total_amount,  # will be overridden by balance_due in template
        'EXAM':    1500.0,
        'LIBRARY': 500.0,
        'SPORTS':  500.0,
        'MISC':    0.0,
    }
    merged = {**DEFAULT_AMOUNTS, **fee_breakdown_map}
    fee_components_display = [
        (key, COMPONENT_LABELS[key], merged.get(key, 0))
        for key in COMPONENT_LABELS
        if key != 'TUITION'  # Tuition handled separately in template using balance_due
        and merged.get(key, 0) > 0
    ]

    year_of_study = ((student.current_semester - 1) // 2) + 1

    # Which non-tuition fee types have already been paid for this semester
    paid_types = set(
        Payment.objects.filter(fee=fee, status='SUCCESS')
        .exclude(payment_type__in=tuition_fee_types)
        .values_list('payment_type', flat=True)
    ) if fee else set()

    recent_payments = Payment.objects.filter(fee=fee).order_by('-paid_at', '-created_at')[:8]
    all_semester_fees = Fee.objects.filter(student=student).order_by('semester').prefetch_related(
        'payment_set'
    )
    return render(request, 'student/payment_form.html', {
        'student': student,
        'fee': fee,
        'balance_due': balance_due,
        'recent_payments': recent_payments,
        'all_semester_fees': all_semester_fees,
        'razorpay_enabled': razorpay_enabled,
        'razorpay_key_id': _s.RAZORPAY_KEY_ID,
        'fee_components_display': fee_components_display,
        'year_of_study': year_of_study,
        'paid_types': paid_types,
    })

@login_required
def razorpay_create_order(request):
    """Creates a Razorpay order and returns order details as JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        student = Student.objects.select_related('department').get(user=request.user)
        fee = Fee.objects.filter(student=student).order_by('-semester').first()
        if not fee:
            raise Fee.DoesNotExist
    except (Student.DoesNotExist, Fee.DoesNotExist):
        return JsonResponse({'error': 'Fee record not found'}, status=404)

    try:
        amount = Decimal(request.POST.get('amount', '0'))
    except InvalidOperation:
        return JsonResponse({'error': 'Invalid amount'}, status=400)

    fee_type = request.POST.get('fee_type', 'TUITION').strip()
    allowed_fee_types = {'TUITION', 'EXAM', 'LIBRARY', 'SPORTS', 'MISC'}
    if fee_type not in allowed_fee_types:
        fee_type = 'TUITION'
    note = request.POST.get('note', '').strip()[:200]

    balance_due = max(Decimal(str(fee.total_amount)) - Decimal(str(fee.paid_amount)), Decimal('0'))

    if amount <= 0:
        return JsonResponse({'error': 'Amount must be greater than zero'}, status=400)
    # Only enforce balance_due cap for tuition payments
    if fee_type == 'TUITION' and amount > balance_due:
        return JsonResponse({'error': f'Amount exceeds tuition balance due ₹{balance_due:.2f}'}, status=400)

    from django.conf import settings as _s
    if not (_s.RAZORPAY_KEY_ID and _s.RAZORPAY_KEY_SECRET):
        return JsonResponse({'error': 'Payment gateway not configured'}, status=503)

    # Amount in paise (Razorpay requires integer paise)
    amount_paise = int(amount * 100)

    try:
        client = _get_razorpay_client()
        order = client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'payment_capture': 1,
            'notes': {
                'student': student.roll_number,
                'fee_type': fee_type,
                'fee_id': str(fee.pk),
                'note': note,
            }
        })
    except Exception as e:
        return JsonResponse({'error': f'Payment gateway error: {str(e)}'}, status=502)

    # Create a PENDING payment record
    payment = Payment.objects.create(
        user=request.user,
        fee=fee,
        amount=float(amount),
        payment_type=fee_type,
        transaction_id=order['id'],
        status='PENDING',
        payment_method='RAZORPAY',
    )

    return JsonResponse({
        'order_id': order['id'],
        'amount': amount_paise,
        'currency': 'INR',
        'key': _s.RAZORPAY_KEY_ID,
        'payment_pk': payment.pk,
        'student_name': student.user.get_full_name(),
        'student_email': student.user.email,
    })


@login_required
def razorpay_verify_payment(request):
    """Verifies Razorpay signature and marks payment as SUCCESS."""
    if request.method != 'POST':
        messages.error(request, 'Invalid request.')
        return redirect('student_fee_payment')

    razorpay_order_id   = request.POST.get('razorpay_order_id', '')
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
    razorpay_signature  = request.POST.get('razorpay_signature', '')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        messages.error(request, 'Missing payment verification parameters.')
        return redirect('student_fee_payment')

    try:
        client = _get_razorpay_client()
        client.utility.verify_payment_signature({
            'razorpay_order_id':   razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature':  razorpay_signature,
        })
    except Exception:
        payment = Payment.objects.filter(transaction_id=razorpay_order_id).first()
        if payment:
            payment.status = 'FAILED'
            payment.save(update_fields=['status'])
        messages.error(request, 'Payment verification failed. Contact support if money was deducted.')
        return redirect('student_fee_payment')

    # Categories that reduce the semester fee balance
    TUITION_CATEGORIES = {'TUITION', 'SEM_FEE'}

    with transaction.atomic():
        payment = Payment.objects.select_for_update().filter(
            transaction_id=razorpay_order_id, user=request.user
        ).first()
        if not payment:
            messages.error(request, 'Payment record not found.')
            return redirect('student_fee_payment')

        if payment.status != 'SUCCESS':
            payment.status = 'SUCCESS'
            payment.paid_at = timezone.now()
            payment.save(update_fields=['status', 'paid_at'])

            # Only update semester fee balance for tuition/semester fee payments.
            # Exam fee, lab fee, library fee etc. are standalone — do NOT touch fee.paid_amount.
            fee = payment.fee
            if fee and payment.payment_type in TUITION_CATEGORIES:
                fee.paid_amount = float(Decimal(str(fee.paid_amount)) + Decimal(str(payment.amount)))
                _sync_fee_status(fee)
                fee.save(update_fields=['paid_amount', 'status'])

    messages.success(request, f'Payment of Rs {payment.amount:.0f} successful.')
    _audit('FEE_PAYMENT', request.user,
           f"Fee payment Rs {payment.amount:.0f} ({payment.payment_type}) via {payment.payment_method}. Txn: {payment.transaction_id}",
           student=Student.objects.filter(user=request.user).first(),
           college=getattr(getattr(Student.objects.filter(user=request.user).first(), 'department', None), 'college', None),
           request=request, new_value=str(payment.amount))

    # Notify college admin(s) about the payment
    try:
        student = Student.objects.select_related('department__college', 'user').filter(user=request.user).first()
        if student:
            from django.core.mail import send_mail
            from django.conf import settings as _s
            paid_at_str = timezone.localtime(payment.paid_at).strftime('%d %b %Y, %I:%M %p') + ' IST'
            college_name = student.department.college.name if student.department.college else 'EduTrack'

            # ── Email to student ──────────────────────────────────────────────
            student_email = student.user.email
            if student_email:
                student_subject = f'Payment Confirmation — Rs {payment.amount:.0f} received'
                student_body = (
                    f'Dear {student.user.get_full_name()},\n\n'
                    f'Your payment has been successfully processed.\n\n'
                    f'  Amount    : Rs {payment.amount:.2f}\n'
                    f'  Type      : {payment.payment_type}\n'
                    f'  Method    : {payment.payment_method}\n'
                    f'  Txn ID    : {payment.transaction_id}\n'
                    f'  Date/Time : {paid_at_str}\n\n'
                    f'You can download your receipt from the EduTrack student portal.\n\n'
                    f'Regards,\n{college_name}'
                )
                send_mail(student_subject, student_body, _s.DEFAULT_FROM_EMAIL,
                          [student_email], fail_silently=True)

            # ── Email to college admin(s) ─────────────────────────────────────
            admin_emails = list(
                UserRole.objects.filter(role=1, college=student.department.college)
                .values_list('user__email', flat=True)
            )
            admin_emails = [e for e in set(admin_emails) if e]
            if admin_emails:
                subject = f'[{college_name}] Fee Payment Received — {student.roll_number}'
                body = (
                    f'A fee payment has been received.\n\n'
                    f'Student   : {student.user.get_full_name()} ({student.roll_number})\n'
                    f'Department: {student.department.name}\n'
                    f'Amount    : Rs {payment.amount:.2f}\n'
                    f'Type      : {payment.payment_type}\n'
                    f'Method    : {payment.payment_method}\n'
                    f'Txn ID    : {payment.transaction_id}\n'
                    f'Date/Time : {paid_at_str}\n\n'
                    f'Log in to EduTrack admin panel to verify.\n'
                )
                send_mail(subject, body, _s.DEFAULT_FROM_EMAIL, admin_emails, fail_silently=True)
    except Exception:
        pass  # Never block the student flow due to email errors

    return redirect('student_payment_receipt', pk=payment.pk)


@login_required
def razorpay_payment_failed(request):
    """Marks a payment as FAILED when user cancels or payment fails."""
    order_id = request.GET.get('order_id', '')
    if order_id:
        Payment.objects.filter(transaction_id=order_id, user=request.user, status='PENDING').update(status='FAILED')
    messages.warning(request, 'Payment was cancelled or failed. No amount was deducted.')
    return redirect('student_fee_payment')


# ── SUPPLY EXAM REGISTRATION & PAYMENT ───────────────────────────────────────

def _get_supply_fee_per_subject(college, department, semester):
    """Returns the configured supply exam fee per subject, or default Rs 500."""
    structure = FeeStructure.objects.filter(
        college=college, department=department, semester=semester
    ).first()
    if structure:
        bd = structure.breakdowns.filter(category='SUPPLY_PER_SUBJECT').first()
        if bd:
            return bd.amount
    return 500.0


def _get_reval_fee_per_subject(college, department, semester):
    """Returns the configured revaluation fee per subject, or default Rs 300."""
    structure = FeeStructure.objects.filter(
        college=college, department=department, semester=semester
    ).first()
    if structure:
        bd = structure.breakdowns.filter(category='REVAL_PER_SUBJECT').first()
        if bd:
            return bd.amount
    return 300.0


@login_required
def student_supply_exam_register(request):
    """
    Student selects failed subjects to register for supply/backlog exam.
    Shows all failed subjects across all semesters, grouped by semester.
    """
    try:
        student = Student.objects.select_related('department__college').get(user=request.user)
    except Student.DoesNotExist:
        return redirect('dashboard')

    college = student.department.college

    # Find the latest supply exam for this college (not semester-restricted)
    latest_exam = Exam.objects.filter(college=college).order_by('-end_date').first()

    # Get ALL failed subjects across ALL semesters, grouped by semester
    # A subject is "failed" if the student's best mark is still below 40%
    all_marks = Marks.objects.filter(
        student=student,
        subject__department=student.department,
    ).select_related('subject', 'exam').order_by('subject__semester', 'subject__name')

    # Build best mark per subject
    best_mark_per_subject = {}
    for m in all_marks:
        sid = m.subject_id
        if sid not in best_mark_per_subject:
            best_mark_per_subject[sid] = m
        else:
            if m.marks_obtained > best_mark_per_subject[sid].marks_obtained:
                best_mark_per_subject[sid] = m

    # Collect failed subjects (best attempt still < 40%)
    failed_by_semester = {}
    for sid, m in best_mark_per_subject.items():
        passing = m.max_marks * 0.4
        if m.marks_obtained < passing:
            sem = m.subject.semester
            failed_by_semester.setdefault(sem, []).append(m)

    # Sort semesters
    failed_semesters = sorted(failed_by_semester.keys())
    failed_grouped = [(sem, failed_by_semester[sem]) for sem in failed_semesters]

    # Flat list for fee calculation
    all_failed_marks = [m for marks in failed_by_semester.values() for m in marks]
    failed_subject_ids = {m.subject_id for m in all_failed_marks}

    fee_per_subject = _get_supply_fee_per_subject(college, student.department, student.current_semester)

    # Check existing registration
    existing_reg = None
    if latest_exam:
        existing_reg = SupplyExamRegistration.objects.filter(
            student=student, exam=latest_exam
        ).first()

    if request.method == 'POST' and latest_exam:
        if existing_reg and existing_reg.status == 'PAID':
            messages.info(request, 'You have already completed payment for this supply registration.')
            return redirect('student_dashboard')
        subject_ids = request.POST.getlist('subjects')
        if not subject_ids:
            messages.error(request, 'Select at least one subject to register.')
        else:
            selected_subject_ids = set(subject_ids)
            subjects = Subject.objects.filter(
                department=student.department,
                pk__in=selected_subject_ids.intersection(failed_subject_ids),
            )
            if subjects.count() != len(selected_subject_ids):
                messages.error(request, 'One or more selected subjects are not eligible for supply registration.')
                return redirect('student_supply_exam_register')
            total_fee = fee_per_subject * subjects.count()

            with transaction.atomic():
                reg, created = SupplyExamRegistration.objects.get_or_create(
                    student=student, exam=latest_exam,
                    defaults={'total_fee': total_fee, 'status': 'PENDING'}
                )
                if not created:
                    if reg.payment_id and reg.payment and reg.payment.status == 'PENDING':
                        reg.payment.status = 'FAILED'
                        reg.payment.save(update_fields=['status'])
                    reg.total_fee = total_fee
                    reg.status = 'PENDING'
                    reg.payment = None
                    reg.save(update_fields=['total_fee', 'status', 'payment'])
                reg.subjects.set(subjects)

            return redirect('student_supply_exam_pay', reg_id=reg.pk)

    return render(request, 'student/supply_exam_register.html', {
        'student': student,
        'latest_exam': latest_exam,
        'failed_grouped': failed_grouped,
        'all_failed_marks': all_failed_marks,
        'fee_per_subject': fee_per_subject,
        'existing_reg': existing_reg,
    })


@login_required
def student_supply_exam_pay(request, reg_id):
    """Razorpay payment for supply exam registration."""
    reg = get_object_or_404(
        SupplyExamRegistration.objects.select_related('student__user', 'exam'),
        pk=reg_id, student__user=request.user
    )
    if reg.status == 'PAID':
        messages.info(request, 'You have already paid for this supply exam registration.')
        return redirect('student_dashboard')

    from django.conf import settings as _s
    razorpay_enabled = bool(_s.RAZORPAY_KEY_ID and _s.RAZORPAY_KEY_SECRET)

    return render(request, 'student/supply_exam_pay.html', {
        'reg': reg,
        'razorpay_enabled': razorpay_enabled,
        'razorpay_key_id': _s.RAZORPAY_KEY_ID,
    })


@login_required
def razorpay_supply_create_order(request):
    """Creates Razorpay order for supply exam fee."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    reg_id = request.POST.get('reg_id')
    reg = get_object_or_404(SupplyExamRegistration, pk=reg_id, student__user=request.user)

    if reg.status == 'PAID':
        return JsonResponse({'error': 'Already paid.'}, status=400)

    from django.conf import settings as _s
    amount_paise = int(reg.total_fee * 100)

    try:
        client = _get_razorpay_client()
        order = client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'payment_capture': 1,
            'notes': {
                'type': 'SUPPLY_EXAM',
                'student': reg.student.roll_number,
                'exam': reg.exam.name,
                'subjects': ', '.join(reg.subjects.values_list('code', flat=True)),
            }
        })
    except Exception as e:
        return JsonResponse({'error': f'Gateway error: {str(e)}'}, status=502)

    payment = Payment.objects.create(
        user=request.user,
        fee=None,
        amount=reg.total_fee,
        payment_type='SUPPLY_EXAM',
        transaction_id=order['id'],
        status='PENDING',
        payment_method='RAZORPAY',
    )
    reg.payment = payment
    reg.save(update_fields=['payment'])

    return JsonResponse({
        'order_id': order['id'],
        'amount': amount_paise,
        'currency': 'INR',
        'key': _s.RAZORPAY_KEY_ID,
        'student_name': reg.student.user.get_full_name(),
        'student_email': reg.student.user.email,
    })


@login_required
def razorpay_supply_verify(request):
    """Verifies supply exam payment and marks registration as PAID."""
    if request.method != 'POST':
        messages.error(request, 'Invalid request.')
        return redirect('student_supply_exam_register')

    razorpay_order_id   = request.POST.get('razorpay_order_id', '')
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
    razorpay_signature  = request.POST.get('razorpay_signature', '')

    try:
        client = _get_razorpay_client()
        client.utility.verify_payment_signature({
            'razorpay_order_id':   razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature':  razorpay_signature,
        })
    except Exception:
        Payment.objects.filter(transaction_id=razorpay_order_id).update(status='FAILED')
        messages.error(request, 'Payment verification failed. Contact support.')
        return redirect('student_supply_exam_register')

    with transaction.atomic():
        payment = Payment.objects.select_for_update().filter(
            transaction_id=razorpay_order_id, user=request.user
        ).first()
        if payment and payment.status != 'SUCCESS':
            payment.status = 'SUCCESS'
            payment.paid_at = timezone.now()
            payment.save(update_fields=['status', 'paid_at'])

        reg = SupplyExamRegistration.objects.filter(payment=payment).first()
        if reg:
            reg.status = 'PAID'
            reg.save(update_fields=['status'])

    messages.success(request, 'Supply exam registration confirmed.')
    return redirect('student_dashboard')


# ── REVALUATION FEE PAYMENT ───────────────────────────────────────────────────

@login_required
def student_reval_fee_pay(request, marks_id):
    """
    Student pays revaluation fee for a specific marks record before
    the revaluation request is submitted.
    """
    try:
        student = Student.objects.select_related('department__college').get(user=request.user)
    except Student.DoesNotExist:
        return redirect('dashboard')

    marks = get_object_or_404(
        Marks.objects.select_related('subject', 'exam'),
        pk=marks_id, student=student
    )

    college = student.department.college
    fee_per_subject = _get_reval_fee_per_subject(college, student.department, student.current_semester)

    # Check if reval request already exists
    existing_reval = RevaluationRequest.objects.filter(student=student, marks=marks).first()
    if existing_reval:
        messages.info(request, 'A revaluation request already exists for this subject.')

    from django.conf import settings as _s
    razorpay_enabled = bool(_s.RAZORPAY_KEY_ID and _s.RAZORPAY_KEY_SECRET)

    if request.method == 'POST' and request.POST.get('confirm_pay'):
        if existing_reval:
            messages.warning(request, 'This revaluation request has already been submitted.')
            return redirect(f"{reverse('student_dashboard')}#results")
        amount_paise = int(fee_per_subject * 100)
        try:
            client = _get_razorpay_client()
            order = client.order.create({
                'amount': amount_paise,
                'currency': 'INR',
                'payment_capture': 1,
                'notes': {
                    'type': 'REVALUATION',
                    'student': student.roll_number,
                    'subject': marks.subject.code,
                    'exam': marks.exam.name,
                }
            })
        except Exception as e:
            messages.error(request, f'Gateway error: {str(e)}')
            return redirect('student_dashboard')

        payment = Payment.objects.create(
            user=request.user,
            fee=None,
            amount=fee_per_subject,
            payment_type='REVALUATION',
            transaction_id=order['id'],
            status='PENDING',
            payment_method='RAZORPAY',
        )
        return render(request, 'student/reval_fee_pay.html', {
            'marks': marks,
            'student': student,
            'fee': fee_per_subject,
            'order_id': order['id'],
            'payment_pk': payment.pk,
            'razorpay_key_id': _s.RAZORPAY_KEY_ID,
            'razorpay_enabled': razorpay_enabled,
        })

    return render(request, 'student/reval_fee_pay.html', {
        'marks': marks,
        'student': student,
        'fee': fee_per_subject,
        'existing_reval': existing_reval,
        'razorpay_enabled': razorpay_enabled,
        'razorpay_key_id': _s.RAZORPAY_KEY_ID,
    })


@login_required
def razorpay_reval_verify(request):
    """Verifies reval fee payment and auto-creates the RevaluationRequest."""
    if request.method != 'POST':
        messages.error(request, 'Invalid request.')
        return redirect('student_dashboard')

    razorpay_order_id   = request.POST.get('razorpay_order_id', '')
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
    razorpay_signature  = request.POST.get('razorpay_signature', '')
    marks_id            = request.POST.get('marks_id', '')

    try:
        client = _get_razorpay_client()
        client.utility.verify_payment_signature({
            'razorpay_order_id':   razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature':  razorpay_signature,
        })
    except Exception:
        Payment.objects.filter(transaction_id=razorpay_order_id).update(status='FAILED')
        messages.error(request, 'Payment verification failed. Contact support.')
        return redirect('student_dashboard')

    with transaction.atomic():
        payment = Payment.objects.select_for_update().filter(
            transaction_id=razorpay_order_id, user=request.user
        ).first()
        if payment and payment.status != 'SUCCESS':
            payment.status = 'SUCCESS'
            payment.paid_at = timezone.now()
            payment.save(update_fields=['status', 'paid_at'])

        student = Student.objects.get(user=request.user)
        marks = get_object_or_404(Marks, pk=marks_id, student=student)
        RevaluationRequest.objects.get_or_create(
            student=student, marks=marks,
            defaults={'reason': 'Fee paid online', 'status': 'PENDING'}
        )

    messages.success(request, 'Revaluation request submitted successfully.')
    return redirect(f"{reverse('student_dashboard')}#results")


@login_required
def student_payment_receipt(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related(
            'fee__student__user',
            'fee__student__department__college',
        ),
        pk=pk, user=request.user
    )
    fee = payment.fee
    student = fee.student if fee else None
    college = student.department.college if student else None
    branding = _get_college_branding(college)
    profile = getattr(student.user, 'studentprofile', None) if student else None
    balance_due = max(fee.total_amount - fee.paid_amount, 0) if fee else 0

    # Compute year of study from admission year and current semester
    year_of_study = None
    if student:
        year_of_study = ((student.current_semester - 1) // 2) + 1

    return render(request, 'student/payment_receipt.html', {
        'payment': payment,
        'fee': fee,
        'student': student,
        'college': college,
        'branding': branding,
        'profile': profile,
        'balance_due': balance_due,
        'year_of_study': year_of_study,
    })


@login_required
def student_payment_receipt_pdf(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related('fee__student__user', 'fee__student__department__college'),
        pk=pk, user=request.user
    )
    fee     = payment.fee
    student = fee.student if fee else None
    college = student.department.college if student else None
    profile = getattr(student.user, 'studentprofile', None) if student else None

    from io import BytesIO
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER

    PRIMARY = colors.HexColor('#0d7377')
    if college:
        try:
            branding_color = college.branding.primary_color
            PRIMARY = colors.HexColor(branding_color)
        except Exception:
            pass

    DARK  = colors.HexColor('#1e293b')
    MUTED = colors.HexColor('#64748b')
    WHITE = colors.white
    LIGHT_BG = colors.HexColor('#f8fafc')
    AMOUNT_BG = colors.HexColor('#f0fdfa')
    BORDER    = colors.HexColor('#e2e8f0')

    def ps(name, **kw):
        return ParagraphStyle(name, **kw)

    lbl  = ps('lbl',  fontName='Helvetica',      fontSize=8,  textColor=MUTED,  spaceAfter=1)
    val  = ps('val',  fontName='Helvetica-Bold',  fontSize=9,  textColor=DARK,   spaceAfter=5)
    hdr  = ps('hdr',  fontName='Helvetica-Bold',  fontSize=8,  textColor=PRIMARY, spaceAfter=4)
    wht  = ps('wht',  fontName='Helvetica-Bold',  fontSize=11, textColor=WHITE)
    whtS = ps('whts', fontName='Helvetica',        fontSize=8,  textColor=colors.HexColor('#cce8e9'))
    whtR = ps('whtr', fontName='Helvetica-Bold',  fontSize=10, textColor=WHITE,  alignment=TA_RIGHT)
    whtRS= ps('whtrs',fontName='Helvetica',        fontSize=8,  textColor=colors.HexColor('#cce8e9'), alignment=TA_RIGHT)
    amt  = ps('amt',  fontName='Helvetica-Bold',  fontSize=16, textColor=PRIMARY)
    ftr  = ps('ftr',  fontName='Helvetica',        fontSize=7,  textColor=MUTED,  alignment=TA_CENTER)
    tid  = ps('tid',  fontName='Helvetica-Bold',  fontSize=8,  textColor=DARK,   wordWrap='CJK')

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=10*mm, bottomMargin=15*mm)
    elements = []

    # ── HEADER BAND (mirrors screen: logo | college name + location | FEE RECEIPT + txn + badge) ──
    college_name = college.name if college else 'EduTrack'
    tagline = ''
    city_state = ''
    if college:
        try: tagline = college.branding.tagline or ''
        except Exception: pass
        if college.city:
            city_state = college.city + (f', {college.state}' if college.state else '')

    status_color = {'SUCCESS': colors.HexColor('#22c55e'), 'PENDING': colors.HexColor('#f59e0b'), 'FAILED': colors.HexColor('#ef4444')}.get(payment.status, MUTED)
    status_text  = {'SUCCESS': 'PAID', 'PENDING': 'PENDING', 'FAILED': 'FAILED'}.get(payment.status, payment.status)

    # Logo cell
    logo_cell = [Paragraph(college_name, wht)]
    if city_state:
        logo_cell.append(Paragraph(city_state, whtS))

    # Right cell: FEE RECEIPT label, txn id, status badge
    badge_para = Paragraph(f'  {status_text}  ', ps('badge', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE, backColor=status_color, borderPadding=3))
    right_cell = [
        Paragraph('FEE RECEIPT', whtR),
        Paragraph(payment.transaction_id, whtRS),
        Spacer(1, 4),
        badge_para,
    ]

    header_table = Table([[logo_cell, right_cell]], colWidths=['60%', '40%'])
    header_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), PRIMARY),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',   (0,0), (-1,-1), 14),
        ('RIGHTPADDING',  (0,0), (-1,-1), 14),
        ('TOPPADDING',    (0,0), (-1,-1), 16),
        ('BOTTOMPADDING', (0,0), (-1,-1), 16),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 14))

    # ── SECTION HEADERS ──
    def section_head(text):
        t = Table([[Paragraph(text, hdr)]], colWidths=['100%'])
        t.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 1.5, PRIMARY),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
        ]))
        return t

    def row(label, value):
        return [Paragraph(label, lbl), Paragraph(str(value) if value else '-', val)]

    # ── LEFT COLUMN: Student Details ──
    year_of_study = ((student.current_semester - 1) // 2) + 1 if student else '-'
    sem_label = f"Semester {fee.semester}" if fee and fee.semester else (f"Semester {student.current_semester}" if student else '-')

    left_items = [
        section_head('STUDENT DETAILS'),
        Spacer(1, 6),
    ]
    for label, value in [
        ('Full Name',     student.user.get_full_name() if student else '-'),
        ('Roll Number',   student.roll_number if student else '-'),
        ('Department',    student.department.name if student else '-'),
        ('Branch',        student.department.code if student else '-'),
        ('Semester',      sem_label),
        ('Year of Study', f'Year {year_of_study}'),
        ('Academic Year', fee.academic_year if fee and fee.academic_year else '-'),
        ('Admission Year',str(student.admission_year) if student else '-'),
        ('Mobile',        profile.phone_number if profile else '-'),
        ('Email',         student.user.email if student else '-'),
    ]:
        left_items.append(Paragraph(label, lbl))
        left_items.append(Paragraph(value, val))

    # ── RIGHT COLUMN: Payment Details + Amount Box ──
    balance_due = max(fee.total_amount - fee.paid_amount, 0) if fee else 0
    paid_at_local = timezone.localtime(payment.paid_at) if payment.paid_at else None

    right_items = [
        section_head('PAYMENT DETAILS'),
        Spacer(1, 6),
    ]
    for label, value in [
        ('Transaction ID',  payment.transaction_id),
        ('Payment Date',    paid_at_local.strftime('%d %b %Y') if paid_at_local else '-'),
        ('Payment Time',    paid_at_local.strftime('%I:%M %p') + ' IST' if paid_at_local else '-'),
        ('Paid Through',    payment.payment_method),
        ('Fee Type',        payment.payment_type),
        ('Status',          payment.get_status_display()),
    ]:
        right_items.append(Paragraph(label, lbl))
        right_items.append(Paragraph(value, val))

    # Amount box — only show semester fee breakdown for tuition payments
    TUITION_CATEGORIES = {'TUITION', 'SEM_FEE'}
    is_tuition = payment.payment_type in TUITION_CATEGORIES

    if is_tuition and fee:
        amount_rows = [
            [Paragraph('Total Fee',       lbl), Paragraph(f'Rs {fee.total_amount:.2f}', val)],
            [Paragraph('Previously Paid', lbl), Paragraph(f'Rs {fee.paid_amount:.2f}', val)],
            [Paragraph('Amount Paid Now', ps('apn', fontName='Helvetica-Bold', fontSize=10, textColor=PRIMARY)),
             Paragraph(f'Rs {payment.amount:.2f}', ps('apnv', fontName='Helvetica-Bold', fontSize=10, textColor=PRIMARY))],
            [Paragraph('Balance Due',     lbl),
             Paragraph(f'Rs {balance_due:.2f}', ps('bd', fontName='Helvetica-Bold', fontSize=9,
                       textColor=colors.HexColor('#dc2626') if balance_due > 0 else colors.HexColor('#16a34a')))],
        ]
    else:
        # Standalone fee (exam, lab, library, etc.) — just show amount paid
        amount_rows = [
            [Paragraph('Amount Paid', ps('apn', fontName='Helvetica-Bold', fontSize=10, textColor=PRIMARY)),
             Paragraph(f'Rs {payment.amount:.2f}', ps('apnv', fontName='Helvetica-Bold', fontSize=10, textColor=PRIMARY))],
        ]
    amount_table = Table(amount_rows, colWidths=['50%', '50%'])
    amount_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), AMOUNT_BG),
        ('BOX',           (0,0), (-1,-1), 0.5, PRIMARY),
        ('LINEABOVE',     (0,2), (-1,2),  0.5, BORDER),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    right_items.append(Spacer(1, 8))
    right_items.append(amount_table)

    # ── TWO-COLUMN LAYOUT ──
    two_col = Table([[left_items, right_items]], colWidths=['48%', '52%'])
    two_col.setStyle(TableStyle([
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (1,0), (1,0),   0),
        ('RIGHTPADDING',  (0,0), (0,0),   12),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(two_col)
    elements.append(Spacer(1, 14))

    # ── COLLEGE CONTACT STRIP ──
    if college:
        contact_parts = []
        if college.email:    contact_parts.append(college.email)
        if college.website:  contact_parts.append(college.website)
        if city_state:       contact_parts.append(city_state)
        if contact_parts:
            contact_table = Table([[Paragraph('  |  '.join(contact_parts), ps('ct', fontName='Helvetica', fontSize=8, textColor=MUTED))]])
            contact_table.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,-1), LIGHT_BG),
                ('BOX',           (0,0), (-1,-1), 0.5, BORDER),
                ('LEFTPADDING',   (0,0), (-1,-1), 10),
                ('RIGHTPADDING',  (0,0), (-1,-1), 10),
                ('TOPPADDING',    (0,0), (-1,-1), 7),
                ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ]))
            elements.append(contact_table)
            elements.append(Spacer(1, 10))

    # ── FOOTER ──
    elements.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceAfter=6))
    gen_str = paid_at_local.strftime('%d %b %Y, %I:%M %p') + ' IST via EduTrack' if paid_at_local else 'EduTrack'
    footer_left  = f'This is a computer-generated receipt and does not require a physical signature.\nFor queries, contact the accounts office with your Transaction ID.\nGenerated on {gen_str}'
    footer_right = f'Authorised Signatory\n\n\n{college_name}'

    footer_table = Table([
        [Paragraph(footer_left,  ps('fl', fontName='Helvetica', fontSize=7, textColor=MUTED, leading=10)),
         Paragraph(footer_right, ps('fr', fontName='Helvetica', fontSize=7, textColor=MUTED, alignment=TA_RIGHT, leading=10))]
    ], colWidths=['60%', '40%'])
    footer_table.setStyle(TableStyle([
        ('VALIGN',        (0,0), (-1,-1), 'BOTTOM'),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LINEABOVE',     (1,0), (1,0),   0.5, BORDER),
    ]))
    elements.append(footer_table)

    doc.build(elements)
    payload = buf.getvalue()

    from django.core.files.base import ContentFile
    existing = SystemReport.objects.filter(report_type='PAYMENT', generated_by=request.user,
                                           file__contains=f"payment-receipt-{payment.pk}.pdf").first()
    if not existing:
        report = SystemReport(report_type='PAYMENT', generated_by=request.user)
        report.file.save(f"payment-receipt-{payment.pk}.pdf", ContentFile(payload), save=True)

    response = HttpResponse(payload, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="payment-receipt-{payment.pk}.pdf"'
    return response


@login_required
def student_mark_notifications_read(request):
    """Mark all unread notifications as read for the current user."""
    from django.http import JsonResponse
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=405)


@login_required
def student_quiz_attempt(request, quiz_id):
    """Student takes a quiz — timed, auto-graded on submit."""
    student = get_object_or_404(Student, user=request.user)
    quiz = get_object_or_404(Quiz, pk=quiz_id, is_active=True,
                             subject__department=student.department,
                             subject__semester=student.current_semester)

    # One attempt per student per quiz — get or create
    attempt, created = QuizAttempt.objects.get_or_create(quiz=quiz, student=student)
    if attempt.is_submitted:
        messages.info(request, f'You already submitted this quiz. Score: {attempt.score}/{quiz.total_marks}')
        return redirect('student_dashboard')

    # Enforce timer: if attempt started and duration exceeded, auto-submit
    elapsed = (timezone.now() - attempt.started_at).total_seconds()
    time_limit_secs = quiz.duration_minutes * 60
    time_expired = elapsed > time_limit_secs + 30  # 30s grace

    questions = quiz.questions.prefetch_related('options').all()

    if request.method == 'POST' or time_expired:
        # Hard block re-submission at view level
        if attempt.is_submitted:
            messages.warning(request, 'This quiz was already submitted.')
            return redirect('student_dashboard')
        score = 0.0
        with transaction.atomic():
            for question in questions:
                opt_id = request.POST.get(f'q_{question.pk}')
                selected = QuizOption.objects.filter(pk=opt_id, question=question).first() if opt_id else None
                QuizAnswer.objects.update_or_create(
                    attempt=attempt, question=question,
                    defaults={'selected_option': selected}
                )
                if selected and selected.is_correct:
                    score += question.marks
            attempt.score = round(min(score, quiz.total_marks), 2)
            attempt.is_submitted = True
            attempt.submitted_at = timezone.now()
            attempt.save(update_fields=['score', 'is_submitted', 'submitted_at'])
        if time_expired and request.method != 'POST':
            messages.warning(request, f'Time expired. Quiz auto-submitted. Score: {attempt.score}/{quiz.total_marks}')
        else:
            messages.success(request, f'Quiz submitted! Your score: {attempt.score}/{quiz.total_marks}')
        return redirect('student_dashboard')

    seconds_remaining = max(0, int(time_limit_secs - elapsed))
    return render(request, 'student/quiz_attempt.html', {
        'quiz': quiz, 'questions': questions, 'attempt': attempt,
        'seconds_remaining': seconds_remaining,
    })


@login_required
def student_result_report_pdf(request):
    try:
        student = Student.objects.select_related('department__college', 'user').get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Contact admin.')
        return redirect('home')

    result_breakdown, results = _student_result_breakdown(student)
    if not results.exists():
        return redirect(f"{reverse('student_dashboard')}#results")

    college = student.department.college

    from io import BytesIO
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors

    styles, PRIMARY, DARK, MUTED = _get_pdf_styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=10*mm, bottomMargin=15*mm)
    elements = []

    generated_on = timezone.localtime(timezone.now()).strftime('%d %b %Y, %I:%M %p')
    _build_pdf_header(elements, college, 'STUDENT RESULT REPORT', f'Generated: {generated_on} IST', styles=styles, PRIMARY=PRIMARY)
    elements.append(Spacer(1, 10))

    # ── Student info strip ──
    year_of_study = ((student.current_semester - 1) // 2) + 1
    info_data = [
        [Paragraph('Name', styles['FieldLabel']),        Paragraph(student.user.get_full_name() or student.user.username, styles['FieldValue']),
         Paragraph('Roll No.', styles['FieldLabel']),     Paragraph(student.roll_number, styles['FieldValue'])],
        [Paragraph('Department', styles['FieldLabel']),   Paragraph(student.department.name, styles['FieldValue']),
         Paragraph('Branch', styles['FieldLabel']),       Paragraph(student.department.code, styles['FieldValue'])],
        [Paragraph('Current Semester', styles['FieldLabel']), Paragraph(str(student.current_semester), styles['FieldValue']),
         Paragraph('Year of Study', styles['FieldLabel']), Paragraph(f'Year {year_of_study}', styles['FieldValue'])],
        [Paragraph('Admission Year', styles['FieldLabel']), Paragraph(str(student.admission_year), styles['FieldValue']),
         Paragraph('Status', styles['FieldLabel']),        Paragraph(student.status, styles['FieldValue'])],
    ]
    info_table = Table(info_data, colWidths=['25%', '25%', '25%', '25%'])
    info_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID',     (0,0), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 12))

    # ── Per-semester results ──
    for item in reversed(result_breakdown):
        result = item.get('result')
        semester = result.semester if result else item.get('semester', '?')

        # Semester header
        if result:
            sem_header = f"Semester {semester}  —  GPA: {result.gpa:.2f}  |  {result.percentage:.1f}%  |  Total: {result.total_marks:.0f}"
            status_color = colors.HexColor('#16a34a') if result.percentage >= 40 else colors.HexColor('#dc2626')
            status_text  = 'PASS' if result.percentage >= 40 else 'FAIL'
        else:
            sem_header = f"Semester {semester}  —  Marks available"
            status_color = MUTED
            status_text  = '—'

        sem_row = Table([[
            Paragraph(sem_header, styles['SectionHead']),
            Paragraph(status_text, styles['StatusBadge'])
        ]], colWidths=['80%', '20%'])
        sem_row.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), colors.HexColor('#f0fdfa')),
            ('BACKGROUND',    (1,0), (1,0),   status_color),
            ('LEFTPADDING',   (0,0), (-1,-1), 8),
            ('RIGHTPADDING',  (0,0), (-1,-1), 8),
            ('TOPPADDING',    (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(sem_row)

        # Marks table
        marks = item.get('marks', [])
        if marks:
            header_row = [
                Paragraph('Code',    styles['TableHeader']),
                Paragraph('Subject', styles['TableHeader']),
                Paragraph('Obtained',styles['TableHeader']),
                Paragraph('Max',     styles['TableHeader']),
                Paragraph('Grade',   styles['TableHeader']),
            ]
            rows = [header_row]
            for mark in marks:
                rows.append([
                    Paragraph(mark.subject.code,  styles['TableCell']),
                    Paragraph(mark.subject.name,  styles['TableCell']),
                    Paragraph(f"{mark.marks_obtained:.0f}", styles['TableCell']),
                    Paragraph(f"{mark.max_marks:.0f}",      styles['TableCell']),
                    Paragraph(mark.grade or '—',            styles['TableCell']),
                ])
            marks_table = Table(rows, colWidths=['15%', '45%', '15%', '12%', '13%'])
            marks_table.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,0),  PRIMARY),
                ('ROWBACKGROUNDS',(0,1), (-1,-1),  [colors.white, colors.HexColor('#f8fafc')]),
                ('BOX',           (0,0), (-1,-1),  0.5, colors.HexColor('#e2e8f0')),
                ('INNERGRID',     (0,0), (-1,-1),  0.3, colors.HexColor('#e2e8f0')),
                ('LEFTPADDING',   (0,0), (-1,-1),  6),
                ('RIGHTPADDING',  (0,0), (-1,-1),  6),
                ('TOPPADDING',    (0,0), (-1,-1),  4),
                ('BOTTOMPADDING', (0,0), (-1,-1),  4),
                ('VALIGN',        (0,0), (-1,-1),  'MIDDLE'),
            ]))
            elements.append(marks_table)
        elements.append(Spacer(1, 8))

    _build_pdf_footer_note(elements, college, styles)
    doc.build(elements)
    payload = buf.getvalue()

    from django.core.files.base import ContentFile
    existing = SystemReport.objects.filter(report_type='RESULT', generated_by=request.user,
                                           file__contains=f"student-result-{student.roll_number}.pdf").first()
    if not existing:
        report = SystemReport(report_type='RESULT', generated_by=request.user)
        report.file.save(f"student-result-{student.roll_number}.pdf", ContentFile(payload), save=True)

    response = HttpResponse(payload, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="student-result-{student.roll_number}.pdf"'
    return response


# ═══════════════════════════════════════════════════════
# COLLEGE ADMIN — CRUD VIEWS
# ═══════════════════════════════════════════════════════

def _admin_guard(request):
    """Returns True if user is allowed to access college admin."""
    if request.user.is_superuser:
        return True
    try:
        return request.user.userrole.role == 1
    except UserRole.DoesNotExist:
        return False


def _scope_registration_requests(request):
    college = _get_admin_college(request)
    qs = RegistrationRequest.objects.select_related('desired_department', 'college').order_by('-created_at')
    if request.user.is_superuser or college is None:
        return qs
    return qs.filter(college=college)


# ── DEPARTMENTS ─────────────────────────────────────────

@login_required
def admin_departments(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    return redirect('/dashboard/admin/#departments')


@login_required
def admin_department_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    if request.method == 'POST':
        name  = request.POST.get('name', '').strip()
        code  = request.POST.get('code', '').strip().upper()
        desc  = request.POST.get('description', '').strip()
        year  = request.POST.get('established_year', '').strip()
        if not name or not code:
            messages.error(request, 'Name and code are required.')
        elif Department.objects.filter(college=college, code=code).exists():
            messages.error(request, f'Department code "{code}" already exists in this college.')
        elif Department.objects.filter(college=college, name__iexact=name).exists():
            messages.error(request, f'Department "{name}" already exists in this college.')
        else:
            Department.objects.create(
                college=college,
                name=name, code=code,
                description=desc or None,
                established_year=_safe_int(year) if year else None
            )
            messages.success(request, f'Department "{name}" added.')
            return redirect('/dashboard/admin/#departments')
    return render(request, 'admin_panel/department_form.html', {'action': 'Add'})


@login_required
def admin_department_edit(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    dept = get_object_or_404(_scope_departments(request), pk=pk)
    if request.method == 'POST':
        old_code = dept.code
        new_name   = request.POST.get('name', dept.name).strip()
        new_code   = request.POST.get('code', dept.code).strip().upper()
        if not new_name or not new_code:
            messages.error(request, 'Name and code are required.')
            return render(request, 'admin_panel/department_form.html', {'action': 'Edit', 'dept': dept})
        if Department.objects.filter(college=dept.college, code=new_code).exclude(pk=dept.pk).exists():
            messages.error(request, f'Department code "{new_code}" already exists in this college.')
            return render(request, 'admin_panel/department_form.html', {'action': 'Edit', 'dept': dept})
        if Department.objects.filter(college=dept.college, name__iexact=new_name).exclude(pk=dept.pk).exists():
            messages.error(request, f'Department "{new_name}" already exists in this college.')
            return render(request, 'admin_panel/department_form.html', {'action': 'Edit', 'dept': dept})
        dept.name  = new_name
        dept.description = request.POST.get('description', '').strip() or None
        year = request.POST.get('established_year', '').strip()
        dept.established_year = _safe_int(year) if year else None
        dept.code = new_code
        dept.save()
        # If code changed, update all student roll numbers that contain the old code
        if old_code != new_code:
            students_to_update = Student.objects.filter(department=dept)
            updated = 0
            for s in students_to_update:
                if old_code in s.roll_number:
                    s.roll_number = s.roll_number.replace(f'-{old_code}-', f'-{new_code}-')
                    s.save(update_fields=['roll_number'])
                    updated += 1
            if updated:
                messages.info(request, f'Department code changed: {updated} roll number(s) updated to use "{new_code}".')
        messages.success(request, 'Department updated.')
        return redirect('/dashboard/admin/#departments')
    return render(request, 'admin_panel/department_form.html', {'action': 'Edit', 'dept': dept})


@login_required
def admin_department_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    dept = get_object_or_404(_scope_departments(request), pk=pk)
    if request.method == 'POST':
        dept.delete()
        messages.success(request, 'Department deleted.')
    return redirect('/dashboard/admin/#departments')


# ── STUDENTS ────────────────────────────────────────────

@login_required
def admin_students(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    return redirect('/dashboard/admin/#students')


@login_required
def admin_students_export_csv(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    dept_filter = request.GET.get('dept', '')
    sem_filter  = request.GET.get('sem', '')
    departments = _scope_departments(request).order_by('name')
    students = Student.objects.select_related('user', 'department__college').filter(
        department__in=departments
    ).order_by('department__code', 'current_semester', 'roll_number')
    if dept_filter:
        students = students.filter(department_id=dept_filter)
    if sem_filter:
        students = students.filter(current_semester=sem_filter)

    # Pre-fetch all fee records keyed by (student_id, semester)
    fee_qs = Fee.objects.filter(student__in=students)
    fee_map = {}
    for f in fee_qs:
        fee_map[(f.student_id, f.semester)] = f

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students-export.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Roll Number', 'Username', 'Name', 'Email',
        'College', 'Department Name', 'Department Code',
        'Current Semester', 'Admission Year', 'Status',
        'Fee Semester', 'Academic Year', 'Total Fee', 'Paid', 'Balance', 'Fee Status',
    ])
    for student in students:
        fee = fee_map.get((student.id, student.current_semester))
        writer.writerow([
            student.roll_number,
            student.user.username,
            student.user.get_full_name() or student.user.username,
            student.user.email,
            student.department.college.name if student.department.college else '',
            student.department.name,
            student.department.code,
            student.current_semester,
            student.admission_year,
            student.status,
            fee.semester if fee else '',
            fee.academic_year if fee else '',
            fee.total_amount if fee else '',
            fee.paid_amount if fee else '',
            round(fee.total_amount - fee.paid_amount, 2) if fee else '',
            fee.status if fee else '',
        ])
    return response


@login_required
def admin_registration_requests(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    status_filter = request.GET.get('status', '').strip()
    dept_filter = request.GET.get('department', '').strip()
    requests_list = _scope_registration_requests(request).select_related(
        'desired_department', 'college', 'reviewed_by'
    ).order_by('-created_at')
    if status_filter:
        requests_list = requests_list.filter(status=status_filter)
    if dept_filter:
        requests_list = requests_list.filter(desired_department_id=dept_filter)
    departments = _scope_departments(request).order_by('name')
    return render(request, 'admin_panel/registration_requests.html', {
        'requests_list': requests_list,
        'status_filter': status_filter,
        'dept_filter': dept_filter,
        'departments': departments,
        'college': _get_admin_college(request),
        'branding': _get_college_branding(_get_admin_college(request)),
        'status_choices': RegistrationRequest.STATUS_CHOICES,
    })


@login_required
def admin_registration_request_update(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    reg_request = get_object_or_404(_scope_registration_requests(request), pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action', '').strip().upper()
        review_notes = request.POST.get('review_notes', '').strip()
        correction_fields = request.POST.get('correction_fields', '').strip()
        if action in {'UNDER_REVIEW', 'APPROVED', 'REJECTED'}:
            reg_request.status = action
            reg_request.reviewed_by = request.user
            reg_request.reviewed_at = timezone.now()
            reg_request.review_notes = review_notes
            if action != 'NEEDS_CORRECTION':
                reg_request.correction_fields = ''
            reg_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_notes', 'correction_fields'])
            _notify_registration_request_status(reg_request)
            messages.success(request, f'Request marked as {reg_request.get_status_display().lower()}.')
        elif action == 'NEEDS_CORRECTION':
            if not correction_fields:
                messages.error(request, 'Please specify what needs correction before sending the request back.')
            else:
                reg_request.status = action
                reg_request.reviewed_by = request.user
                reg_request.reviewed_at = timezone.now()
                reg_request.review_notes = review_notes
                reg_request.correction_fields = correction_fields
                reg_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_notes', 'correction_fields'])
                _notify_registration_request_status(reg_request)
                messages.success(request, 'Request marked as needs correction.')
        elif action == 'CONVERTED':
            messages.error(request, 'Use the Convert action to create the student record. The request status will update automatically after conversion.')
    next_url = request.POST.get('next', '').strip()
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)
    return redirect('admin_registration_requests')


@login_required
def admin_registration_invites(request):
    if not _admin_guard(request):
        return redirect('dashboard')

    college = _get_admin_college(request) or _default_college()
    departments = Department.objects.filter(college=college).order_by('name')

    if request.method == 'POST':
        email = request.POST.get('invited_email', '').strip().lower()
        department_id = request.POST.get('department')
        admission_year = request.POST.get('admission_year', '').strip()
        current_semester = request.POST.get('current_semester', '').strip()
        if not email:
            messages.error(request, 'Invite email is required.')
        elif RegistrationInvite.objects.filter(
            invited_email=email,
            college=college,
            used_at__isnull=True,
        ).filter(Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now())).exists():
            messages.error(request, 'An active invite already exists for this email.')
        else:
            department = departments.filter(pk=department_id).first() if department_id else None
            invite = RegistrationInvite.objects.create(
                college=college,
                department=department,
                invited_email=email,
                admission_year=int(admission_year) if admission_year else None,
                current_semester=int(current_semester) if current_semester else None,
                created_by=request.user,
                expires_at=timezone.now() + timedelta(days=7),
            )
            messages.success(request, 'Invite link created successfully.')
        return redirect('/dashboard/admin/#requests')

    return redirect('/dashboard/admin/#requests')


@login_required
def admin_student_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    request_id = request.GET.get('request') or request.POST.get('request_id')
    intake_request = None
    if request_id:
        intake_request = _scope_registration_requests(request).filter(pk=request_id).first()
        if intake_request and intake_request.status not in REGISTRATION_CONVERTIBLE_STATUSES:
            messages.error(request, 'Only approved registration requests can be converted into student accounts.')
            return redirect('admin_registration_requests')
    if request.method == 'POST':
        # User fields
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        username   = request.POST.get('username', '').strip()
        email      = request.POST.get('email', '').strip()
        password   = request.POST.get('password', '')
        # Student fields
        dept_id     = request.POST.get('department')
        adm_year    = request.POST.get('admission_year')
        semester    = request.POST.get('current_semester')
        status      = request.POST.get('status', 'ACTIVE')
        department = departments.filter(pk=dept_id).first() if dept_id else None
        adm_year_int = _safe_int(adm_year)
        roll_number = _generate_roll_number(department, adm_year_int) if department and adm_year_int else ''
        if not username and roll_number:
            username = roll_number.lower()

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        elif not department or not adm_year_int or not semester:
            messages.error(request, 'Department, admission year, and semester are required.')
        elif Student.objects.filter(roll_number=roll_number).exists():
            messages.error(request, 'Roll number already exists.')
        else:
            with transaction.atomic():
                password_value, password_generated = _resolve_password(password)
                # create_user automatically handles secure password hashing
                user = User.objects.create_user(
                    username=username, email=email, password=password_value,
                    first_name=first_name, last_name=last_name
                )
                UserRole.objects.create(user=user, role=4, college=department.college)
                student = Student.objects.create(
                    user=user, roll_number=roll_number,
                    department=department,
                    admission_year=adm_year_int,
                    current_semester=_safe_int(semester),
                    section=_determine_student_section(department, adm_year_int),
                    status=status
                )
                
                # Transfer registration data to Profile automatically
                if intake_request:
                    # first_name/last_name live on User model, not StudentProfile
                    user.first_name = intake_request.first_name
                    user.last_name = intake_request.last_name
                    user.save(update_fields=['first_name', 'last_name'])
                    StudentProfile.objects.update_or_create(
                        user=user,
                        defaults={
                            'date_of_birth': intake_request.date_of_birth or timezone.now().date(),
                            'gender': intake_request.gender or 'Not Specified',
                            'phone_number': intake_request.phone_number,
                            'aadhaar_number': intake_request.aadhaar_number,
                            'inter_college_name': intake_request.inter_college_name,
                            'inter_passed_year': intake_request.inter_passed_year or 0,
                            'inter_percentage': intake_request.inter_percentage or 0.0,
                            'school_name': intake_request.school_name,
                            'school_passed_year': intake_request.school_passed_year or 0,
                            'school_percentage': intake_request.school_percentage or 0.0,
                            'profile_photo': intake_request.photo_id
                        }
                    )

                # Real-time enhancement: Auto-generate fee record
                _create_default_fee(student)

            if intake_request:
                intake_request.status = 'CONVERTED'
                intake_request.reviewed_by = intake_request.reviewed_by or request.user
                intake_request.reviewed_at = intake_request.reviewed_at or timezone.now()
                intake_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
                _notify_registration_request_converted(
                    intake_request,
                    user,
                    password_generated=password_generated,
                    password_value=password_value,
                )
            if password_generated:
                messages.success(request, f'Student {roll_number} added in Section {student.section or "A"}. Temporary password: {password_value}')
            else:
                messages.success(request, f'Student {roll_number} added in Section {student.section or "A"}.')
            return redirect('/dashboard/admin/#students')
    return render(request, 'admin_panel/student_form.html', {
        'departments': departments,
        'action': 'Add',
        'intake_request': intake_request,
    })


@login_required
def admin_student_edit(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    student = get_object_or_404(Student.objects.filter(department__in=departments), pk=pk)
    if request.method == 'POST':
        student.user.first_name = request.POST.get('first_name', '').strip()
        student.user.last_name  = request.POST.get('last_name', '').strip()
        student.user.email      = request.POST.get('email', '').strip()
        student.user.save()
        student.department_id    = request.POST.get('department', student.department_id)
        student.admission_year   = _safe_int(request.POST.get('admission_year', student.admission_year))
        student.current_semester = _safe_int(request.POST.get('current_semester', student.current_semester))
        student.status           = request.POST.get('status', student.status)
        student.save()
        UserRole.objects.filter(user=student.user).update(college=student.department.college)
        messages.success(request, 'Student updated.')
        return redirect('/dashboard/admin/#students')
    return render(request, 'admin_panel/student_form.html', {
        'student': student, 'departments': departments, 'action': 'Edit'
    })


@login_required
def admin_students_bulk_promote(request):
    """Handles end-of-semester batch promotion. Sem 8 → GRADUATED."""
    if not _admin_guard(request):
        return redirect('dashboard')

    departments = _scope_departments(request).order_by('name')
    if request.method == 'POST':
        dept_id = request.POST.get('department')
        from_sem = _safe_int(request.POST.get('from_semester'))

        if not dept_id or not from_sem:
            messages.error(request, 'Please select department and current semester.')
        else:
            with transaction.atomic():
                if from_sem >= 8:
                    students_to_update = Student.objects.filter(
                        department_id=dept_id, current_semester=from_sem,
                        status='ACTIVE', is_deleted=False
                    )
                    affected = students_to_update.count()
                    for student in students_to_update:
                        StudentLifecycleEvent.objects.create(
                            student=student, event_type='GRADUATED',
                            from_status='ACTIVE', to_status='GRADUATED',
                            from_semester=from_sem, to_semester=from_sem,
                            reason='Batch graduation', performed_by=request.user,
                        )
                    students_to_update.update(status='GRADUATED')
                    _audit('USER_PROMOTED', request.user,
                           f"Batch graduation: {affected} students from {dept_id} Sem {from_sem}",
                           college=_get_admin_college(request), request=request)
                    messages.success(request, f'{affected} student(s) marked as Graduated.')
                else:
                    students_to_update = Student.objects.filter(
                        department_id=dept_id, current_semester=from_sem,
                        status='ACTIVE', is_deleted=False
                    )
                    affected = students_to_update.count()
                    for student in students_to_update:
                        StudentLifecycleEvent.objects.create(
                            student=student, event_type='PROMOTED',
                            from_status='ACTIVE', to_status='ACTIVE',
                            from_semester=from_sem, to_semester=from_sem + 1,
                            reason=f'Batch promotion Sem {from_sem} → {from_sem + 1}',
                            performed_by=request.user,
                        )
                    students_to_update.update(current_semester=F('current_semester') + 1)
                    promoted = Student.objects.filter(
                        department_id=dept_id, current_semester=from_sem + 1,
                        status='ACTIVE', is_deleted=False
                    )
                    for student in promoted:
                        _create_default_fee(student)
                    _audit('USER_PROMOTED', request.user,
                           f"Batch promotion: {affected} students from {dept_id} Sem {from_sem} → {from_sem + 1}",
                           college=_get_admin_college(request), request=request)
                    messages.success(request, f'{affected} student(s) promoted to Semester {from_sem + 1}.')
            return redirect('/dashboard/admin/#students')

    return render(request, 'admin_panel/bulk_promote.html', {'departments': departments})


@login_required
def admin_bulk_import(request):
    """Handles CSV bulk import for Students and Faculty."""
    if not _admin_guard(request):
        return redirect('dashboard')
    
    college = _get_admin_college(request)
    departments = _scope_departments(request)

    if request.method == 'POST' and request.FILES.get('csv_file'):
        import_type = request.POST.get('import_type') # 'STUDENT' or 'FACULTY'
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid CSV file.')
            return redirect('admin_bulk_import')

        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()  # utf-8-sig strips Excel BOM
        reader = csv.DictReader(decoded_file)
        
        # Script Break Protection: Ensure mandatory columns exist before processing
        required_cols = ['email', 'first_name', 'last_name', 'dept_code']
        if not all(col in reader.fieldnames for col in required_cols):
            messages.error(request, f"CSV missing required columns: {', '.join(required_cols)}")
            return redirect('admin_bulk_import')

        success_count = 0
        skip_count = 0
        errors = []
        for row in reader:
            try:
                with transaction.atomic():
                    username = (row.get('username') or row.get('email') or '').strip()
                    email = (row.get('email') or '').strip()
                    if not username or not email:
                        errors.append(f"Row {reader.line_num}: username/email missing.")
                        continue
                    if User.objects.filter(username=username).exists():
                        skip_count += 1
                        continue
                    if User.objects.filter(email=email).exists():
                        skip_count += 1
                        continue

                    dept_code = (row.get('dept_code') or '').strip().upper()
                    dept = departments.filter(code=dept_code).first()
                    if not dept:
                        raise ValueError(f"Department code '{dept_code}' not found.")

                    password_value = (row.get('password') or '').strip() or _generate_temporary_password()

                    if import_type == 'STUDENT':
                        adm_year = _safe_int(row.get('admission_year'), default=2024)
                        roll = (row.get('roll_number') or '').strip() or _generate_roll_number(dept, adm_year)
                        if Student.objects.filter(roll_number=roll).exists():
                            skip_count += 1
                            continue
                    else:
                        emp_id = (row.get('employee_id') or '').strip() or _generate_faculty_id(dept)
                        if Faculty.objects.filter(employee_id=emp_id).exists():
                            raise ValueError(f"Employee ID '{emp_id}' already exists.")

                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password_value,
                        first_name=(row.get('first_name') or '').strip(),
                        last_name=(row.get('last_name') or '').strip(),
                    )

                    if import_type == 'STUDENT':
                        UserRole.objects.create(user=user, role=4, college=college)
                        student = Student.objects.create(
                            user=user,
                            roll_number=roll,
                            department=dept,
                            admission_year=adm_year,
                            current_semester=_safe_int(row.get('current_semester'), default=1),
                            section=(row.get('section') or '').strip().upper() or _determine_student_section(dept, adm_year),
                        )
                        _create_default_fee(student)
                    else:
                        UserRole.objects.create(user=user, role=3, college=college)
                        Faculty.objects.create(
                            user=user,
                            employee_id=emp_id,
                            department=dept,
                            designation=(row.get('designation') or 'Assistant Professor').strip(),
                            qualification=(row.get('qualification') or 'M.Tech').strip(),
                            experience_years=_safe_int(row.get('experience_years') or row.get('experience'), default=0),
                            phone_number=(row.get('phone_number') or row.get('phone') or '').strip(),
                        )
                    success_count += 1
            except Exception as e:
                errors.append(f"Row {reader.line_num}: {str(e)}")

        if success_count:
            msg = f"Imported {success_count} {import_type.lower()} record(s)."
            if skip_count:
                msg += f" {skip_count} skipped (already exist)."
            if errors:
                msg += f" {len(errors)} row(s) had errors."
                messages.warning(request, msg)
                for e in errors[:10]:
                    messages.warning(request, e)
            else:
                messages.success(request, msg)
        elif errors:
            messages.error(request, f"Import failed. {len(errors)} error(s):")
            for e in errors[:10]:
                messages.error(request, e)
        else:
            messages.warning(request, "No records were imported. Check your CSV file.")
        return redirect('admin_bulk_import')

    return render(request, 'admin_panel/bulk_import.html', {
        'departments': departments,
        'branding': _get_college_branding(college),
    })


@login_required
def admin_sample_csv(request):
    """Generates sample CSV templates based on type."""
    if not _admin_guard(request):
        return redirect('dashboard')
    
    target_type = request.GET.get('type', 'student').lower()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="edutrack_{target_type}_sample.csv"'
    
    writer = csv.writer(response)
    
    if target_type == 'faculty':
        writer.writerow(['username', 'email', 'first_name', 'last_name', 'dept_code', 'employee_id', 'designation', 'qualification', 'experience_years', 'phone_number', 'password'])
        writer.writerow(['prof_rajesh', 'rajesh@college.edu', 'Rajesh', 'Khanna', 'CSE', 'FAC-001', 'Assistant Professor', 'M.Tech', '5', '9800000001', 'EduTrack@123'])
    else:
        writer.writerow(['username', 'email', 'first_name', 'last_name', 'dept_code', 'admission_year', 'current_semester', 'roll_number', 'password'])
        writer.writerow(['john_doe', 'john@college.edu', 'John', 'Doe', 'CSE', '2024', '1', '', 'EduTrack@123'])
        writer.writerow(['jane_smith', 'jane@college.edu', 'Jane', 'Smith', 'ECE', '2024', '1', '', 'EduTrack@123'])
        
    return response


@login_required
def admin_student_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    student = get_object_or_404(Student.objects.filter(department__in=_scope_departments(request)), pk=pk)
    if request.method == 'POST':
        # Implementation of Soft Delete
        student.is_deleted = True
        student.user.is_active = False
        student.save()
        student.user.save()
        messages.success(request, f'Student {student.roll_number} has been deactivated and archived.')
    return redirect('/dashboard/admin/#students')


# ── FACULTY ─────────────────────────────────────────────

@login_required
def admin_faculty_list(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    return redirect('/dashboard/admin/#faculty')


@login_required
def admin_faculty_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    if request.method == 'POST':
        first_name   = request.POST.get('first_name', '').strip()
        last_name    = request.POST.get('last_name', '').strip()
        username     = request.POST.get('username', '').strip()
        email        = request.POST.get('email', '').strip()
        password     = request.POST.get('password', '')
        employee_id  = request.POST.get('employee_id', '').strip()
        dept_id      = request.POST.get('department')
        designation  = request.POST.get('designation', '').strip()
        qualification= request.POST.get('qualification', '').strip()
        experience   = request.POST.get('experience_years', 0)
        phone        = request.POST.get('phone_number', '').strip()

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        elif Faculty.objects.filter(employee_id=employee_id).exists():
            messages.error(request, 'Employee ID already exists.')
        else:
            department = get_object_or_404(departments, pk=dept_id)
            if not employee_id:
                employee_id = _generate_faculty_id(department)
            password_value, password_generated = _resolve_password(password)
            user = User.objects.create_user(
                username=username, email=email, password=password_value,
                first_name=first_name, last_name=last_name
            )
            UserRole.objects.create(user=user, role=3, college=department.college)
            Faculty.objects.create(
                user=user, employee_id=employee_id, department=department,
                designation=designation, qualification=qualification,
                experience_years=_safe_int(experience), phone_number=phone
            )
            if password_generated:
                messages.success(request, f'Faculty {first_name} {last_name} added. Temporary password: {password_value}')
            else:
                messages.success(request, f'Faculty {first_name} {last_name} added.')
            return redirect('/dashboard/admin/#faculty')
    return render(request, 'admin_panel/faculty_form.html', {'departments': departments, 'action': 'Add'})


@login_required
def admin_faculty_edit(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    faculty = get_object_or_404(Faculty.objects.filter(department__in=departments), pk=pk)
    if request.method == 'POST':
        faculty.user.first_name = request.POST.get('first_name', '').strip()
        faculty.user.last_name  = request.POST.get('last_name', '').strip()
        faculty.user.email      = request.POST.get('email', '').strip()
        faculty.user.save()
        faculty.department_id   = request.POST.get('department', faculty.department_id)
        faculty.designation     = request.POST.get('designation', faculty.designation).strip()
        faculty.qualification   = request.POST.get('qualification', faculty.qualification).strip()
        faculty.experience_years= _safe_int(request.POST.get('experience_years', faculty.experience_years))
        faculty.phone_number    = request.POST.get('phone_number', faculty.phone_number).strip()
        faculty.save()
        UserRole.objects.filter(user=faculty.user).update(college=faculty.department.college)
        messages.success(request, 'Faculty updated.')
        return redirect('/dashboard/admin/#faculty')
    return render(request, 'admin_panel/faculty_form.html', {
        'faculty': faculty, 'departments': departments, 'action': 'Edit'
    })


@login_required
def admin_faculty_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    faculty = get_object_or_404(Faculty.objects.filter(department__in=_scope_departments(request)), pk=pk)
    if request.method == 'POST':
        faculty.user.delete()
        messages.success(request, 'Faculty deleted.')
    return redirect('/dashboard/admin/#faculty')


# ── HODs ────────────────────────────────────────────────

@login_required
def admin_hods(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    hods = HOD.objects.filter(
        department__in=departments,
        is_active=True,
    ).select_related('user', 'department').order_by('department__name', 'user__first_name', 'user__last_name')
    depts_without_hod = departments.exclude(hods__is_active=True)
    return render(request, 'admin_panel/hods.html', {
        'hods': hods,
        'depts_without_hod': depts_without_hod,
        'college': _get_admin_college(request),
        'branding': _get_college_branding(_get_admin_college(request)),
    })


@login_required
def admin_hod_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    if request.method == 'POST':
        first_name   = request.POST.get('first_name', '').strip()
        last_name    = request.POST.get('last_name', '').strip()
        username     = request.POST.get('username', '').strip()
        email        = request.POST.get('email', '').strip()
        password     = request.POST.get('password', '')
        employee_id  = request.POST.get('employee_id', '').strip()
        dept_id      = request.POST.get('department')
        qualification= request.POST.get('qualification', '').strip()
        experience   = request.POST.get('experience_years', 0)
        phone        = request.POST.get('phone_number', '').strip()

        if not dept_id:
            messages.error(request, 'Select a department.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        elif employee_id and HOD.objects.filter(employee_id=employee_id).exists():
            messages.error(request, 'Employee ID already exists.')
        elif HOD.objects.filter(department_id=dept_id, is_active=True).exists():
            messages.error(request, 'This department already has an active HOD.')
        else:
            department = get_object_or_404(departments, pk=dept_id)
            password_value, password_generated = _resolve_password(password)
            user = User.objects.create_user(
                username=username, email=email, password=password_value,
                first_name=first_name, last_name=last_name
            )
            UserRole.objects.create(user=user, role=2, college=department.college)
            HOD.objects.create(
                user=user, employee_id=employee_id, department=department,
                qualification=qualification, experience_years=_safe_int(experience),
                phone_number=phone, is_active=True
            )
            if password_generated:
                messages.success(request, f'HOD {first_name} {last_name} added. Temporary password: {password_value}')
            else:
                messages.success(request, f'HOD {first_name} {last_name} added.')
            return redirect('/dashboard/admin/#faculty')
    return render(request, 'admin_panel/hod_form.html', {'departments': departments})


@login_required
def admin_hod_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    hod = get_object_or_404(HOD.objects.filter(department__in=_scope_departments(request)), pk=pk)
    if request.method == 'POST':
        hod.user.delete()
        messages.success(request, 'HOD deleted.')
    return redirect('/dashboard/admin/#faculty')


# ── SUBJECTS ────────────────────────────────────────────

@login_required
def admin_subjects(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    dept_filter = request.GET.get('dept', '').strip()
    subjects = Subject.objects.filter(
        department__in=departments
    ).select_related('department').order_by('department__code', 'semester', 'code')
    if dept_filter:
        subjects = subjects.filter(department_id=dept_filter)
    return render(request, 'admin_panel/subjects.html', {
        'subjects': subjects,
        'departments': departments,
        'dept_filter': dept_filter,
        'college': _get_admin_college(request),
        'branding': _get_college_branding(_get_admin_college(request)),
    })


@login_required
def admin_subject_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        code    = request.POST.get('code', '').strip().upper()
        dept_id = request.POST.get('department')
        semester= request.POST.get('semester')
        if not all([name, code, dept_id, semester]):
            messages.error(request, 'Subject name, code, department, and semester are required.')
        else:
            department = get_object_or_404(departments, pk=dept_id)
            semester_no = _safe_int(semester)
            duplicate_qs = Subject.objects.filter(
                department=department,
                semester=semester_no,
            )
            if duplicate_qs.filter(code=code).exists():
                messages.error(request, f'Subject code "{code}" already exists for {department.code} semester {semester_no}.')
            elif duplicate_qs.filter(name__iexact=name).exists():
                messages.error(request, f'Subject "{name}" already exists for {department.code} semester {semester_no}.')
            else:
                Subject.objects.create(
                    name=name, code=code, department=department, semester=semester_no,
                    lecture_hours=_safe_int(request.POST.get('lecture_hours')) or 3,
                    tutorial_hours=_safe_int(request.POST.get('tutorial_hours')) or 0,
                    practical_hours=_safe_int(request.POST.get('practical_hours')) or 0,
                    credits=_safe_int(request.POST.get('credits')) or 3,
                    category=request.POST.get('category', 'PC'),
                )
                messages.success(request, f'Subject "{name}" added.')
                return redirect('admin_subjects')
    return render(request, 'admin_panel/subject_form.html', {'departments': departments})


@login_required
def admin_subject_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    subject = get_object_or_404(Subject.objects.filter(department__in=_scope_departments(request)), pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted.')
    return redirect('admin_subjects')


# ── REGULATIONS ───────────────────────────────────────────────────────────────

@login_required
def admin_regulations(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    regulations = Regulation.objects.filter(college=college).order_by('-effective_from_year')
    return render(request, 'admin_panel/regulations.html', {
        'regulations': regulations, 'college': college,
        'branding': _get_college_branding(college),
    })


@login_required
def admin_regulation_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    if request.method == 'POST':
        name  = request.POST.get('name', '').strip()
        code  = request.POST.get('code', '').strip().upper()
        desc  = request.POST.get('description', '').strip()
        year  = _safe_int(request.POST.get('effective_from_year'))
        if not all([name, code, year]):
            messages.error(request, 'Name, code, and effective year are required.')
        elif Regulation.objects.filter(college=college, code=code).exists():
            messages.error(request, f'Regulation code "{code}" already exists.')
        else:
            Regulation.objects.create(college=college, name=name, code=code,
                                      description=desc, effective_from_year=year)
            messages.success(request, f'Regulation "{name}" created.')
            return redirect('admin_regulations')
    return render(request, 'admin_panel/regulation_form.html', {'college': college})


@login_required
def admin_regulation_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    reg = get_object_or_404(Regulation, pk=pk, college=_get_admin_college(request))
    if request.method == 'POST':
        reg.delete()
        messages.success(request, 'Regulation deleted.')
    return redirect('admin_regulations')


# ── CURRICULUM ────────────────────────────────────────────────────────────────

@login_required
def admin_curriculum(request, regulation_pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    regulation = get_object_or_404(Regulation, pk=regulation_pk, college=college)
    departments = _scope_departments(request).order_by('name')
    dept_filter = request.GET.get('dept')
    sem_filter  = _safe_int(request.GET.get('sem'), default=1)
    department  = departments.filter(pk=dept_filter).first() if dept_filter else departments.first()

    entries = CurriculumEntry.objects.filter(
        regulation=regulation,
        department=department,
        semester=sem_filter,
    ).select_related('subject').prefetch_related('prerequisites') if department else []

    # Subjects available to add (in this dept+sem, not already in curriculum)
    existing_ids = [e.subject_id for e in entries]
    available_subjects = Subject.objects.filter(
        department=department, semester=sem_filter
    ).exclude(pk__in=existing_ids) if department else []

    return render(request, 'admin_panel/curriculum.html', {
        'regulation': regulation, 'departments': departments,
        'department': department, 'sem_filter': sem_filter,
        'entries': entries, 'available_subjects': available_subjects,
        'college': college, 'branding': _get_college_branding(college),
        'semesters': range(1, 9),
    })


@login_required
def admin_curriculum_add(request, regulation_pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    regulation = get_object_or_404(Regulation, pk=regulation_pk, college=college)
    if request.method == 'POST':
        dept_id  = request.POST.get('department')
        subj_id  = request.POST.get('subject')
        semester = _safe_int(request.POST.get('semester'))
        el_type  = request.POST.get('elective_type', 'FIXED')
        dept     = get_object_or_404(_scope_departments(request), pk=dept_id)
        subject  = get_object_or_404(Subject, pk=subj_id, department=dept)
        entry, created = CurriculumEntry.objects.get_or_create(
            regulation=regulation, department=dept, subject=subject, semester=semester,
            defaults={'elective_type': el_type}
        )
        if not created:
            entry.elective_type = el_type
            entry.save(update_fields=['elective_type'])
        prereq_ids = request.POST.getlist('prerequisites')
        if prereq_ids:
            entry.prerequisites.set(Subject.objects.filter(pk__in=prereq_ids))
        messages.success(request, f'"{subject.name}" added to curriculum.')
    return redirect(f"{reverse('admin_curriculum', args=[regulation_pk])}?dept={dept_id}&sem={semester}")


@login_required
def admin_curriculum_remove(request, regulation_pk, entry_pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    regulation = get_object_or_404(Regulation, pk=regulation_pk, college=college)
    entry = get_object_or_404(CurriculumEntry, pk=entry_pk, regulation=regulation)
    dept_id = entry.department_id
    sem     = entry.semester
    entry.delete()
    messages.success(request, 'Subject removed from curriculum.')
    return redirect(f"{reverse('admin_curriculum', args=[regulation_pk])}?dept={dept_id}&sem={sem}")


# ── ELECTIVE POOLS ────────────────────────────────────────────────────────────

@login_required
def admin_elective_pools(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    pools = ElectivePool.objects.filter(
        regulation__college=college
    ).select_related('regulation', 'department').prefetch_related('subjects').order_by('-created_at')
    return render(request, 'admin_panel/elective_pools.html', {
        'pools': pools, 'college': college,
        'branding': _get_college_branding(college),
    })


@login_required
def admin_elective_pool_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    regulations = Regulation.objects.filter(college=college, is_active=True)
    departments = _scope_departments(request).order_by('name')
    if request.method == 'POST':
        reg_id   = request.POST.get('regulation')
        dept_id  = request.POST.get('department')
        semester = _safe_int(request.POST.get('semester'))
        slot     = request.POST.get('slot_name', '').strip()
        el_type  = request.POST.get('elective_type', 'PE')
        quota    = _safe_int(request.POST.get('quota_per_subject')) or 60
        deadline_str = request.POST.get('deadline', '').strip()
        subj_ids = request.POST.getlist('subjects')
        regulation = get_object_or_404(Regulation, pk=reg_id, college=college)
        department = get_object_or_404(departments, pk=dept_id)
        if not slot:
            messages.error(request, 'Slot name is required (e.g. PE-1).')
        elif not subj_ids:
            messages.error(request, 'Select at least one subject for this elective pool.')
        else:
            from django.utils.dateparse import parse_datetime
            deadline = parse_datetime(deadline_str) if deadline_str else None
            pool = ElectivePool.objects.create(
                regulation=regulation, department=department, semester=semester,
                slot_name=slot, elective_type=el_type, quota_per_subject=quota,
                deadline=deadline, created_by=request.user,
            )
            pool.subjects.set(Subject.objects.filter(pk__in=subj_ids))
            messages.success(request, f'Elective pool "{slot}" created.')
            return redirect('admin_elective_pools')
    return render(request, 'admin_panel/elective_pool_form.html', {
        'regulations': regulations, 'departments': departments,
        'college': college, 'semesters': range(1, 9),
    })


@login_required
def admin_elective_pool_toggle(request, pk):
    """Open or close an elective pool for student selection."""
    if not _admin_guard(request):
        return redirect('dashboard')
    pool = get_object_or_404(ElectivePool, pk=pk, regulation__college=_get_admin_college(request))
    if pool.status == 'DRAFT':
        pool.status = 'OPEN'
        messages.success(request, f'Pool "{pool.slot_name}" is now open for student selection.')
    elif pool.status == 'OPEN':
        pool.status = 'CLOSED'
        messages.success(request, f'Pool "{pool.slot_name}" closed.')
    else:
        pool.status = 'OPEN'
        messages.success(request, f'Pool "{pool.slot_name}" reopened.')
    pool.save(update_fields=['status'])
    return redirect('admin_elective_pools')


@login_required
def admin_elective_pool_selections(request, pk):
    """View all student selections for a pool; confirm or reassign."""
    if not _admin_guard(request):
        return redirect('dashboard')
    pool = get_object_or_404(ElectivePool, pk=pk, regulation__college=_get_admin_college(request))
    if request.method == 'POST':
        sel_id  = request.POST.get('selection_id')
        action  = request.POST.get('action')
        new_subj= request.POST.get('new_subject')
        sel = get_object_or_404(ElectiveSelection, pk=sel_id, pool=pool)
        if action == 'confirm':
            sel.status = 'CONFIRMED'
            sel.confirmed_at = timezone.now()
            sel.save(update_fields=['status', 'confirmed_at'])
        elif action == 'reject':
            sel.status = 'REJECTED'
            sel.note = request.POST.get('note', 'Quota full')
            sel.save(update_fields=['status', 'note'])
        elif action == 'change' and new_subj:
            subj = get_object_or_404(Subject, pk=new_subj)
            sel.subject = subj
            sel.status  = 'CHANGED'
            sel.note    = request.POST.get('note', 'Changed by admin')
            sel.confirmed_at = timezone.now()
            sel.save(update_fields=['subject', 'status', 'note', 'confirmed_at'])
        messages.success(request, 'Selection updated.')
        return redirect('admin_elective_pool_selections', pk=pk)

    selections = pool.selections.select_related(
        'student__user', 'subject'
    ).order_by('subject__name', 'student__roll_number')
    # Seat counts per subject
    seat_counts = {
        s.pk: {
            'confirmed': ElectiveSelection.objects.filter(pool=pool, subject=s, status='CONFIRMED').count(),
            'pending':   ElectiveSelection.objects.filter(pool=pool, subject=s, status='PENDING').count(),
            'quota':     pool.quota_per_subject,
        }
        for s in pool.subjects.all()
    }
    return render(request, 'admin_panel/elective_pool_selections.html', {
        'pool': pool, 'selections': selections, 'seat_counts': seat_counts,
        'college': _get_admin_college(request),
        'branding': _get_college_branding(_get_admin_college(request)),
    })


# ── STUDENT ELECTIVE SELECTION ────────────────────────────────────────────────

@login_required
def student_elective_select(request):
    """Student views open elective pools and submits their choice."""
    try:
        student = Student.objects.select_related('department').get(user=request.user)
    except Student.DoesNotExist:
        return redirect('home')

    # Find open pools for this student's department + semester
    # Feature gate: check if electives are enabled for this college
    feature_cfg = CollegeFeatureConfig.objects.filter(college=student.department.college).first()
    if feature_cfg and not feature_cfg.enable_electives:
        return render(request, 'student/elective_select.html', {
            'pool_data': [], 'my_selections': [], 'student': student,
            'feature_disabled': True,
        })

    open_pools = ElectivePool.objects.filter(
        department=student.department,
        semester=student.current_semester,
        status='OPEN',
    ).prefetch_related('subjects')

    # Already selected pools
    my_selections_qs = ElectiveSelection.objects.filter(
        student=student, pool__in=open_pools
    ).select_related('subject', 'pool')

    sel_by_pool = {sel.pool_id: sel for sel in my_selections_qs}

    # Build pool_data list for template (no get_item filter needed)
    pool_data = [
        {'pool': pool, 'selection': sel_by_pool.get(pool.pk)}
        for pool in open_pools
    ]
    my_selections = list(my_selections_qs)

    if request.method == 'POST':
        pool_id = request.POST.get('pool_id')
        subj_id = request.POST.get('subject_id')
        pool    = get_object_or_404(open_pools, pk=pool_id)
        subject = get_object_or_404(pool.subjects, pk=subj_id)

        # Check deadline
        if pool.deadline and timezone.now() > pool.deadline:
            messages.error(request, 'Selection deadline has passed.')
            return redirect('student_elective_select')

        # Check quota — add to waitlist if full
        confirmed = ElectiveSelection.objects.filter(pool=pool, subject=subject, status='CONFIRMED').count()
        if confirmed >= pool.quota_per_subject:
            # Add to waitlist instead of rejecting
            student_cgpa = 0.0
            results = Result.objects.filter(student=student)
            if results.exists():
                student_cgpa = round(sum(r.sgpa for r in results) / results.count(), 2)
            position = ElectiveWaitlist.objects.filter(pool=pool, subject=subject, promoted=False).count() + 1
            ElectiveWaitlist.objects.get_or_create(
                student=student, pool=pool, subject=subject,
                defaults={'position': position, 'cgpa': student_cgpa}
            )
            messages.warning(request, f'"{subject.name}" is full. You have been added to the waitlist (position {position}).')
            return redirect('student_elective_select')

        sel, created = ElectiveSelection.objects.update_or_create(
            student=student, pool=pool,
            defaults={'subject': subject, 'status': 'PENDING', 'confirmed_at': None}
        )
        messages.success(request, f'Your choice "{subject.name}" has been submitted and is pending confirmation.')
        return redirect('student_elective_select')

    return render(request, 'student/elective_select.html', {
        'pool_data': pool_data,
        'my_selections': my_selections,
        'student': student,
    })


@login_required
def admin_academic_planner(request):
    if not _admin_guard(request):
        return redirect('dashboard')

    departments = _scope_departments(request).order_by('name')
    dept_filter = request.GET.get('dept') or request.POST.get('department')
    sem_filter = request.GET.get('sem') or request.POST.get('semester') or '1'
    department = departments.filter(pk=dept_filter).first() if dept_filter else departments.first()
    selected_semester = _safe_int(sem_filter, default=1)

    if request.method == 'POST' and department:
        action = request.POST.get('planner_action')
        if action == 'add_subject':
            name = request.POST.get('name', '').strip()
            code = request.POST.get('code', '').strip().upper()
            if not name or not code:
                messages.error(request, 'Subject name and code are required.')
            else:
                existing_subjects = Subject.objects.filter(
                    department=department,
                    semester=selected_semester,
                )
                if existing_subjects.filter(code=code).exists():
                    messages.error(request, f'Subject code "{code}" already exists for {department.code} semester {selected_semester}.')
                elif existing_subjects.filter(name__iexact=name).exists():
                    messages.error(request, f'Subject "{name}" already exists for {department.code} semester {selected_semester}.')
                else:
                    Subject.objects.create(name=name, code=code, department=department, semester=selected_semester)
                    messages.success(request, 'Subject added to the selected semester.')
        elif action == 'assign_faculty':
            subject_id = request.POST.get('subject_id')
            faculty_id = request.POST.get('faculty_id')
            subject = Subject.objects.filter(pk=subject_id, department=department, semester=selected_semester).first()
            # Faculty can be from ANY department (cross-dept teaching is valid)
            faculty = Faculty.objects.filter(pk=faculty_id).first()
            if not subject or not faculty:
                messages.error(request, 'Select a valid subject and faculty member.')
            elif FacultySubject.objects.filter(subject=subject, faculty=faculty).exists():
                messages.warning(request, f'{faculty.user.get_full_name()} is already assigned to {subject.code}.')
            else:
                FacultySubject.objects.create(subject=subject, faculty=faculty)
                # Count assignments to show section label
                count = FacultySubject.objects.filter(subject=subject).count()
                section_label = chr(64 + count)  # A, B, C...
                messages.success(request, f'{faculty.user.get_full_name()} assigned to {subject.code} — Section {section_label}.')
        elif action == 'remove_assignment':
            assignment_id = request.POST.get('assignment_id')
            FacultySubject.objects.filter(pk=assignment_id, subject__department=department, subject__semester=selected_semester).delete()
            messages.success(request, 'Faculty assignment removed.')
        elif action == 'add_availability':
            faculty_id = request.POST.get('faculty_id')
            faculty = Faculty.objects.filter(pk=faculty_id, department=department).first()
            day = request.POST.get('day_of_week')
            start = request.POST.get('start_time')
            end = request.POST.get('end_time')
            
            if not faculty:
                messages.error(request, 'Select a valid faculty member.')
            else:
                FacultyAvailability.objects.update_or_create(
                    faculty=faculty, day_of_week=day,
                    start_time=start, end_time=end,
                    defaults={'is_available': True},
                )
                messages.success(request, 'Faculty availability slot saved.')
        elif action == 'generate_timetable':
            created_count = _auto_generate_timetable(department, selected_semester)
            if created_count:
                messages.success(request, f'Automatic timetable updated with {created_count} scheduled class slot(s).')
            else:
                messages.warning(request, 'No timetable entries could be generated. Add subjects, faculty assignments, and availability first.')
        elif action == 'add_break':
            label = request.POST.get('break_label', 'Break').strip()
            day = request.POST.get('break_day', '').strip().upper()
            start = request.POST.get('break_start', '').strip()
            end = request.POST.get('break_end', '').strip()
            scope = request.POST.get('break_scope', 'all')
            college = _get_admin_college(request)
            if day and start and end and college:
                TimetableBreak.objects.create(
                    college=college, label=label, day_of_week=day,
                    start_time=start, end_time=end,
                    applies_to_all=(scope == 'all'),
                )
                messages.success(request, f'Break "{label}" added for {day}.')
            else:
                messages.error(request, 'Day, start time, and end time are required.')
        elif action == 'delete_break':
            break_id = request.POST.get('break_id')
            college = _get_admin_college(request)
            TimetableBreak.objects.filter(pk=break_id, college=college).delete()
            messages.success(request, 'Break removed.')
        elif action == 'add_classroom':
            room_number = request.POST.get('room_number', '').strip()
            building = request.POST.get('building', '').strip()
            capacity = _safe_int(request.POST.get('capacity', '60'), default=60)
            college = _get_admin_college(request)
            if room_number and college:
                Classroom.objects.get_or_create(
                    college=college, room_number=room_number,
                    defaults={'building': building, 'capacity': capacity}
                )
                messages.success(request, f'Room {room_number} added.')
            else:
                messages.error(request, 'Room number is required.')
        return redirect(f"{reverse('admin_academic_planner')}?dept={department.pk}&sem={selected_semester}")

    college = _get_admin_college(request)
    faculty = Faculty.objects.filter(department__college=college).select_related('user', 'department').order_by('department__code', 'user__first_name') if department else Faculty.objects.none()
    subjects = Subject.objects.filter(department=department, semester=selected_semester).order_by('name') if department else Subject.objects.none()
    subject_assignments = FacultySubject.objects.filter(subject__in=subjects).select_related('subject', 'faculty__user').order_by('subject__name')
    availability = FacultyAvailability.objects.filter(faculty__in=faculty).select_related('faculty__user').order_by('faculty__user__first_name', 'day_of_week', 'start_time')
    timetable_entries = Timetable.objects.filter(subject__in=subjects).select_related('subject', 'faculty__user', 'classroom').order_by('day_of_week', 'start_time')
    college_breaks = TimetableBreak.objects.filter(college=college).order_by('day_of_week', 'start_time') if college else TimetableBreak.objects.none()
    classrooms = Classroom.objects.filter(college=college).order_by('building', 'room_number') if college else Classroom.objects.none()
    section_strength_summary = []
    if department:
        section_counts = (
            Student.objects.filter(
                department=department,
                current_semester=selected_semester,
                is_deleted=False,
            )
            .exclude(section='')
            .values('section')
            .annotate(total=Count('id'))
            .order_by('section')
        )
        section_strength_summary = list(section_counts)
    timetable_matrix = _build_weekly_timetable_matrix(timetable_entries, breaks=college_breaks)

    return render(request, 'admin_panel/academic_planner.html', {
        'departments': departments,
        'department': department,
        'selected_semester': selected_semester,
        'faculty': faculty,
        'subjects': subjects,
        'subject_assignments': subject_assignments,
        'availability': availability,
        'timetable_entries': timetable_entries,
        'timetable_matrix': timetable_matrix,
        'college_breaks': college_breaks,
        'classrooms': classrooms,
        'section_strength_summary': section_strength_summary,
        'branding': _get_college_branding(college),
    })


# ── SECTION MANAGEMENT ────────────────────────────────────────────────────────

@login_required
def admin_sections(request):
    """List and manage sections for a department+semester."""
    if not _admin_guard(request):
        return redirect('dashboard')
    college  = _get_admin_college(request)
    departments = _scope_departments(request).order_by('name')
    dept_id  = request.GET.get('dept') or request.POST.get('department')
    sem      = _safe_int(request.GET.get('sem') or request.POST.get('semester'), default=1)
    department = departments.filter(pk=dept_id).first() if dept_id else departments.first()

    if request.method == 'POST':
        action = request.POST.get('action')
        dept_id = request.POST.get('department')
        sem     = _safe_int(request.POST.get('semester'), default=1)
        department = get_object_or_404(departments, pk=dept_id)

        if action == 'auto_create':
            # Auto-generate sections based on student count and section capacity
            total = Student.objects.filter(
                department=department, current_semester=sem, status='ACTIVE'
            ).count()
            capacity = _safe_int(request.POST.get('capacity')) or department.section_capacity or 60
            if total == 0:
                messages.warning(request, 'No active students found for this semester.')
            else:
                n_sections = max(1, (total + capacity - 1) // capacity)
                created = 0
                for i in range(n_sections):
                    label = chr(65 + i)  # A, B, C...
                    _, c = Section.objects.get_or_create(
                        department=department, semester=sem, label=label,
                        defaults={'capacity': capacity}
                    )
                    if c:
                        created += 1
                # Assign students to sections in order
                students_qs = Student.objects.filter(
                    department=department, current_semester=sem, status='ACTIVE'
                ).order_by('roll_number')
                for idx, student in enumerate(students_qs):
                    student.section = chr(65 + (idx // capacity))
                    student.save(update_fields=['section'])
                messages.success(request, f'{created} section(s) created, {total} students assigned.')

        elif action == 'add':
            label    = request.POST.get('label', '').strip().upper()
            capacity = _safe_int(request.POST.get('capacity')) or 60
            ay       = request.POST.get('academic_year', '').strip()
            if not label:
                messages.error(request, 'Section label is required.')
            else:
                _, c = Section.objects.get_or_create(
                    department=department, semester=sem, label=label,
                    defaults={'capacity': capacity, 'academic_year': ay}
                )
                messages.success(request, f'Section {label} {"created" if c else "already exists"}.')

        elif action == 'delete':
            sec_pk = request.POST.get('section_pk')
            Section.objects.filter(pk=sec_pk, department=department).delete()
            messages.success(request, 'Section deleted.')

        return redirect(f"{reverse('admin_sections')}?dept={department.pk}&sem={sem}")

    sections = Section.objects.filter(
        department=department, semester=sem
    ).order_by('label') if department else []

    return render(request, 'admin_panel/sections.html', {
        'departments': departments, 'department': department,
        'sem': sem, 'sections': sections,
        'college': college, 'branding': _get_college_branding(college),
        'semesters': range(1, 9),
    })


# ── SUBJECT–SECTION–FACULTY MAPPING ──────────────────────────────────────────

@login_required
def admin_ssf_map(request):
    """
    Subject–Section–Faculty mapping UI.
    Admin selects Subject → Faculty → Section → Assign.
    """
    if not _admin_guard(request):
        return redirect('dashboard')
    college     = _get_admin_college(request)
    departments = _scope_departments(request).order_by('name')
    dept_id     = request.GET.get('dept') or request.POST.get('department')
    sem         = _safe_int(request.GET.get('sem') or request.POST.get('semester'), default=1)
    department  = departments.filter(pk=dept_id).first() if dept_id else departments.first()

    if request.method == 'POST':
        action     = request.POST.get('action')
        dept_id    = request.POST.get('department')
        sem        = _safe_int(request.POST.get('semester'), default=1)
        department = get_object_or_404(departments, pk=dept_id)

        if action == 'assign':
            subj_id  = request.POST.get('subject')
            fac_id   = request.POST.get('faculty')
            sec_pk   = request.POST.get('section')
            room_id  = request.POST.get('classroom') or None
            subject  = get_object_or_404(Subject, pk=subj_id, department=department)
            faculty  = get_object_or_404(Faculty, pk=fac_id)
            section  = get_object_or_404(Section, pk=sec_pk, department=department)
            classroom = Classroom.objects.filter(pk=room_id).first() if room_id else None

            # Also ensure FacultySubject exists (for backward compat with timetable gen)
            FacultySubject.objects.get_or_create(faculty=faculty, subject=subject)

            mapping, created = SectionSubjectFacultyMap.objects.update_or_create(
                section=section, subject=subject,
                defaults={'faculty': faculty, 'classroom': classroom}
            )
            action_word = 'assigned' if created else 'updated'
            messages.success(request, f'{faculty.user.get_full_name()} {action_word} to {subject.code} / Sec {section.label}.')

        elif action == 'remove':
            map_pk = request.POST.get('map_pk')
            SectionSubjectFacultyMap.objects.filter(pk=map_pk).delete()
            messages.success(request, 'Mapping removed.')

        return redirect(f"{reverse('admin_ssf_map')}?dept={department.pk}&sem={sem}")

    subjects  = Subject.objects.filter(department=department, semester=sem).order_by('name') if department else []
    sections  = Section.objects.filter(department=department, semester=sem).order_by('label') if department else []
    faculty   = Faculty.objects.filter(department__college=college).select_related('user', 'department').order_by('user__first_name') if college else []
    classrooms = Classroom.objects.filter(college=college).order_by('room_number') if college else []
    mappings  = SectionSubjectFacultyMap.objects.filter(
        section__department=department, section__semester=sem
    ).select_related('subject', 'faculty__user', 'section', 'classroom').order_by('section__label', 'subject__name') if department else []

    return render(request, 'admin_panel/ssf_map.html', {
        'departments': departments, 'department': department,
        'sem': sem, 'subjects': subjects, 'sections': sections,
        'faculty': faculty, 'classrooms': classrooms, 'mappings': mappings,
        'college': college, 'branding': _get_college_branding(college),
        'semesters': range(1, 9),
    })


@login_required
def admin_timetable_template_csv(request):
    """Download a blank CSV template for timetable upload."""
    if not _admin_guard(request):
        return redirect('dashboard')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="timetable_template.csv"'
    writer = csv.writer(response)
    writer.writerow(['day', 'start_time', 'end_time', 'subject_code', 'faculty_employee_id', 'room_number'])
    # Sample rows covering all 6 days
    samples = [
        ('MON', '09:00', '10:00', 'CS101', 'FAC-001', '101'),
        ('MON', '10:00', '11:00', 'CS102', 'FAC-002', '102'),
        ('TUE', '09:00', '10:00', 'CS103', 'FAC-001', '101'),
        ('WED', '11:00', '12:00', 'CS104', 'FAC-003', '103'),
        ('THU', '14:00', '15:00', 'CS105', 'FAC-002', '102'),
        ('FRI', '09:00', '10:00', 'CS106', 'FAC-004', '104'),
        ('SAT', '10:00', '11:00', 'CS107', 'FAC-001', '101'),
    ]
    for row in samples:
        writer.writerow(row)
    return response


@login_required
def admin_timetable_upload_csv(request):
    """Upload a CSV to bulk-create timetable entries for a department/semester."""
    if not _admin_guard(request):
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('admin_academic_planner')

    college = _get_admin_college(request)
    dept_id = request.POST.get('department')
    semester = _safe_int(request.POST.get('semester'), default=1)
    department = get_object_or_404(_scope_departments(request), pk=dept_id)
    csv_file = request.FILES.get('timetable_csv')

    if not csv_file:
        messages.error(request, 'No file uploaded.')
        return redirect(f"{reverse('admin_academic_planner')}?dept={dept_id}&sem={semester}")

    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'Only .csv files are accepted.')
        return redirect(f"{reverse('admin_academic_planner')}?dept={dept_id}&sem={semester}")

    VALID_DAYS = {'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'}

    # Pre-fetch lookups for this dept/semester
    subject_map = {s.code.upper(): s for s in Subject.objects.filter(department=department, semester=semester)}
    faculty_map = {f.employee_id.upper(): f for f in Faculty.objects.filter(department=department)}
    room_map    = {r.room_number.upper(): r for r in Classroom.objects.filter(college=college)}

    created = skipped = errors = 0
    error_lines = []

    try:
        decoded = csv_file.read().decode('utf-8-sig').splitlines()
    except UnicodeDecodeError:
        messages.error(request, 'File encoding error. Save the CSV as UTF-8 and try again.')
        return redirect(f"{reverse('admin_academic_planner')}?dept={dept_id}&sem={semester}")

    reader = csv.DictReader(decoded)
    required_cols = {'day', 'start_time', 'end_time', 'subject_code', 'faculty_employee_id', 'room_number'}
    if not required_cols.issubset({c.strip().lower() for c in (reader.fieldnames or [])}):
        messages.error(request, f'CSV must have columns: {", ".join(sorted(required_cols))}')
        return redirect(f"{reverse('admin_academic_planner')}?dept={dept_id}&sem={semester}")

    for i, row in enumerate(reader, start=2):
        day          = (row.get('day') or '').strip().upper()
        start_raw    = (row.get('start_time') or '').strip()
        end_raw      = (row.get('end_time') or '').strip()
        subject_code = (row.get('subject_code') or '').strip().upper()
        emp_id       = (row.get('faculty_employee_id') or '').strip().upper()
        room_no      = (row.get('room_number') or '').strip().upper()

        # Validate day
        if day not in VALID_DAYS:
            error_lines.append(f'Row {i}: invalid day "{day}"')
            errors += 1
            continue

        # Validate times
        try:
            from datetime import time as _time
            sh, sm = map(int, start_raw.split(':'))
            eh, em = map(int, end_raw.split(':'))
            start_time = _time(sh, sm)
            end_time   = _time(eh, em)
            if end_time <= start_time:
                raise ValueError('end before start')
        except Exception:
            error_lines.append(f'Row {i}: invalid times "{start_raw}" / "{end_raw}"')
            errors += 1
            continue

        subject = subject_map.get(subject_code)
        if not subject:
            error_lines.append(f'Row {i}: subject code "{subject_code}" not found in Sem {semester}')
            errors += 1
            continue

        faculty = faculty_map.get(emp_id)
        if not faculty:
            error_lines.append(f'Row {i}: faculty employee ID "{emp_id}" not found')
            errors += 1
            continue

        classroom = room_map.get(room_no)
        if not classroom:
            # Auto-create the room if it doesn't exist
            classroom, _ = Classroom.objects.get_or_create(
                college=college, room_number=room_no,
                defaults={'capacity': 60}
            )
            room_map[room_no] = classroom

        # Upsert: update if same subject+day+start exists, else create
        _, was_created = Timetable.objects.update_or_create(
            subject=subject, day_of_week=day, start_time=start_time,
            defaults={
                'faculty': faculty,
                'end_time': end_time,
                'classroom': classroom,
            }
        )
        if was_created:
            created += 1
        else:
            skipped += 1

    msg_parts = []
    if created:  msg_parts.append(f'{created} slot(s) created')
    if skipped:  msg_parts.append(f'{skipped} updated')
    if errors:   msg_parts.append(f'{errors} error(s)')
    if msg_parts:
        level = messages.error if errors and not created and not skipped else messages.success
        level(request, 'Timetable upload: ' + ', '.join(msg_parts) + '.')
    if error_lines:
        messages.warning(request, 'Issues: ' + ' | '.join(error_lines[:5]) + ('...' if len(error_lines) > 5 else ''))

    return redirect(f"{reverse('admin_academic_planner')}?dept={dept_id}&sem={semester}")


@login_required
def admin_helpdesk(request):
    """Redirect to the dashboard helpdesk pane — no longer a standalone page."""
    if not _admin_guard(request):
        return redirect('dashboard')
    return redirect('/dashboard/admin/#helpdesk')


@login_required
def admin_helpdesk_update(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    ticket = get_object_or_404(_scope_helpdesk_tickets(request), pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in {'OPEN', 'IN_PROGRESS', 'RESOLVED'}:
            ticket.status = status
            ticket.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Ticket updated.')
    return redirect('/dashboard/admin/#helpdesk')


# ── FEES ────────────────────────────────────────────────

@login_required
def admin_fees(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    return redirect('/dashboard/admin/#finance')


@login_required
def admin_fee_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')

    FEE_COMPONENTS = [
        ('TUITION',   'Tuition Fee',          45000),
        ('EXAM',      'Exam Fee',              1500),
        ('LAB',       'Lab Fee',               2000),
        ('LIBRARY',   'Library Fee',           500),
        ('SPORTS',    'Sports & Cultural Fee', 500),
        ('MISC',      'Miscellaneous',         0),
    ]

    students = Student.objects.select_related('user', 'department').filter(
        department__in=_scope_departments(request)
    ).order_by('roll_number')

    if request.method == 'POST':
        student_id    = request.POST.get('student')
        semester      = _safe_int(request.POST.get('semester', '')) or None
        academic_year = request.POST.get('academic_year', '').strip()
        paid_amount   = float(request.POST.get('paid_amount', 0) or 0)

        # Build total from components
        total_amount = float(request.POST.get('total_amount', 0) or 0)

        if Fee.objects.filter(student_id=student_id, semester=semester).exists():
            messages.error(request, 'Fee record already exists for this student/semester. Use Edit instead.')
        else:
            with transaction.atomic():
                fee = Fee(
                    student_id=student_id,
                    total_amount=total_amount,
                    paid_amount=paid_amount,
                    semester=semester,
                    academic_year=academic_year,
                )
                _sync_fee_status(fee)
                fee.save()

                # Save component breakdown to FeeBreakdown
                student = Student.objects.select_related('department').get(pk=student_id)
                structure, _ = FeeStructure.objects.get_or_create(
                    college=student.department.college,
                    department=student.department,
                    semester=semester or student.current_semester,
                    defaults={'total_fees': total_amount}
                )
                structure.total_fees = total_amount
                structure.save(update_fields=['total_fees'])

                for key, label, _ in FEE_COMPONENTS:
                    amt = float(request.POST.get(f'comp_{key}', 0) or 0)
                    if amt > 0:
                        FeeBreakdown.objects.update_or_create(
                            structure=structure, category=key,
                            defaults={'amount': amt}
                        )

            messages.success(request, 'Fee record added.')
            return redirect('/dashboard/admin/#finance')

    return render(request, 'admin_panel/fee_form.html', {
        'students': students,
        'action': 'Add',
        'fee_components': FEE_COMPONENTS,
        'breakdown_map': {},
    })


@login_required
def admin_fee_edit(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')

    FEE_COMPONENTS = [
        ('TUITION',   'Tuition Fee',          45000),
        ('EXAM',      'Exam Fee',              1500),
        ('LAB',       'Lab Fee',               2000),
        ('LIBRARY',   'Library Fee',           500),
        ('SPORTS',    'Sports & Cultural Fee', 500),
        ('MISC',      'Miscellaneous',         0),
    ]

    fee = get_object_or_404(Fee.objects.filter(student__department__in=_scope_departments(request)), pk=pk)

    # Load existing breakdown
    structure = FeeStructure.objects.filter(
        department=fee.student.department,
        semester=fee.semester or fee.student.current_semester
    ).first()
    breakdown_map = {}
    if structure:
        for bd in structure.breakdowns.all():
            breakdown_map[bd.category] = bd.amount

    if request.method == 'POST':
        fee.total_amount  = float(request.POST.get('total_amount', fee.total_amount) or fee.total_amount)
        fee.paid_amount   = float(request.POST.get('paid_amount', fee.paid_amount) or 0)
        fee.semester      = _safe_int(request.POST.get('semester', '')) or None
        fee.academic_year = request.POST.get('academic_year', fee.academic_year or '').strip()
        _sync_fee_status(fee)
        fee.save()

        # Update breakdown
        if structure:
            for key, label, _ in FEE_COMPONENTS:
                amt = float(request.POST.get(f'comp_{key}', 0) or 0)
                if amt > 0:
                    FeeBreakdown.objects.update_or_create(
                        structure=structure, category=key,
                        defaults={'amount': amt}
                    )
                else:
                    FeeBreakdown.objects.filter(structure=structure, category=key).delete()

        messages.success(request, 'Fee record updated.')
        return redirect('/dashboard/admin/#finance')

    # Build fee_components with current values
    fee_components_with_vals = [
        (key, label, breakdown_map.get(key, default))
        for key, label, default in FEE_COMPONENTS
    ]

    return render(request, 'admin_panel/fee_form.html', {
        'fee': fee,
        'action': 'Edit',
        'fee_components': fee_components_with_vals,
        'breakdown_map': breakdown_map,
    })


# ── ANNOUNCEMENTS ────────────────────────────────────────

@login_required
def admin_announcements(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    return redirect('/dashboard/admin/#announcements')


@login_required
def admin_announcement_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    if request.method == 'POST':
        title   = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        if not title or not message:
            messages.error(request, 'Title and message are required.')
        else:
            Announcement.objects.create(title=title, message=message, created_by=request.user, college=college or _get_user_college(request.user))
            messages.success(request, 'Announcement posted.')
            return redirect('/dashboard/admin/#announcements')
    return render(request, 'admin_panel/announcement_form.html')


@login_required
def admin_announcement_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    ann = get_object_or_404(_scope_announcements_for_college(_get_admin_college(request)), pk=pk)
    if request.method == 'POST':
        ann.delete()
        messages.success(request, 'Announcement deleted.')
    return redirect('/dashboard/admin/#announcements')


@login_required
def admin_save_colors(request):
    """Save dashboard colors for the college — applies on next page load."""
    if request.method != 'POST' or not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    if not college:
        messages.error(request, 'No college found.')
        return redirect('admin_dashboard')

    def _hex_luminance(hex_color):
        """Return relative luminance 0–1. Values below 0.15 are dark enough for a sidebar."""
        try:
            h = hex_color.lstrip('#')
            r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        except Exception:
            return 0.5

    branding, _ = CollegeBranding.objects.get_or_create(college=college)
    primary = request.POST.get('primary_color', '').strip()
    accent  = request.POST.get('accent_color', '').strip()
    deep    = request.POST.get('sidebar_deep', '').strip()

    if primary and primary.startswith('#') and len(primary) == 7:
        branding.primary_color = primary
    if accent and accent.startswith('#') and len(accent) == 7:
        branding.accent_color = accent
    if deep and deep.startswith('#') and len(deep) == 7:
        if _hex_luminance(deep) > 0.25:
            messages.warning(request, 'Sidebar color is too light — it would make text unreadable. Choose a darker color (luminance ≤ 0.25). Sidebar color was not changed.')
        else:
            branding.sidebar_deep = deep
    branding.save()
    messages.success(request, 'Colors saved. They will apply on next page load for all users.')
    return redirect('/dashboard/admin/#profile')


@login_required
def admin_contact_support(request):
    """College admin contacts the platform super-admin for help."""
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)

    if request.method == 'POST':
        issue_type = request.POST.get('issue_type', 'GENERAL')
        subject    = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        if not subject or not description:
            messages.error(request, 'Subject and description are required.')
        else:
            ticket = HelpDeskTicket.objects.create(
                college=college,
                submitted_by=request.user,
                name=request.user.get_full_name() or request.user.username,
                email=request.user.email or '',
                issue_type=issue_type,
                subject=subject,
                description=description,
            )
            Notification.objects.create(
                user=request.user,
                message=f"Support ticket #{ticket.id} submitted to platform team: {subject}"
            )
            messages.success(request, f'Your request has been submitted to the platform team (Ticket #{ticket.id}). We will respond via the ticket thread.')
            return redirect('admin_contact_support')

    # Show this admin's own tickets to platform (college=None means platform-level, but we show college-scoped ones)
    my_tickets = HelpDeskTicket.objects.filter(
        submitted_by=request.user
    ).order_by('-created_at')[:20]

    return render(request, 'admin_panel/contact_support.html', {
        'college': college,
        'branding': _get_college_branding(college),
        'my_tickets': my_tickets,
    })


# ── EXAMS ────────────────────────────────────────────────
@login_required
def admin_exams(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    exams = _scope_exams(request).order_by('-start_date')
    return render(request, 'admin_panel/exams.html', {
        'exams': exams,
        'college': college,
        'branding': _get_college_branding(college),
    })


@login_required
def admin_exam_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    if request.method == 'POST':
        name       = request.POST.get('name', '').strip()
        semester   = request.POST.get('semester')
        start_date = request.POST.get('start_date')
        end_date   = request.POST.get('end_date')
        Exam.objects.create(
            college=college or _get_user_college(request.user),
            name=name, semester=_safe_int(semester),
            start_date=start_date, end_date=end_date,
            created_by=request.user
        )
        messages.success(request, f'Exam "{name}" created.')
        return redirect('/dashboard/admin/#exams')
    return render(request, 'admin_panel/exam_form.html')


@login_required
def admin_exam_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    exam = get_object_or_404(_scope_exams(request), pk=pk)
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted.')
    return redirect('/dashboard/admin/#exams')


@login_required
def admin_attendance_export_csv(request):
    """Exports attendance records with time filters (Daily/Weekly/Monthly)."""
    if not _admin_guard(request):
        return redirect('dashboard')
    
    college = _get_admin_college(request)
    range_type = request.GET.get('range', 'daily')
    today = timezone.now().date()
    
    if range_type == 'monthly':
        start_date = today - timedelta(days=30)
    elif range_type == 'weekly':
        start_date = today - timedelta(days=7)
    else:
        start_date = today

    sessions = AttendanceSession.objects.filter(
        subject__department__college=college,
        date__gte=start_date
    ).select_related('subject', 'faculty__user')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance-{range_type}-{today}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Subject', 'Faculty', 'Student Roll', 'Student Name', 'Status'])
    
    for session in sessions:
        records = Attendance.objects.filter(session=session).select_related('student__user')
        for rec in records:
            writer.writerow([session.date, session.subject.code, session.faculty.user.get_full_name(), rec.student.roll_number, rec.student.user.get_full_name(), rec.status])
    
    return response


@login_required
def admin_report_pdf(request, report_type):
    if not _admin_guard(request):
        return redirect('dashboard')

    departments = _scope_departments(request)
    college = _get_admin_college(request)

    from io import BytesIO
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors

    styles, PRIMARY, DARK, MUTED = _get_pdf_styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=10*mm, bottomMargin=15*mm)
    elements = []
    generated_on = timezone.localtime(timezone.now()).strftime('%d %b %Y, %I:%M %p')
    college_label = college.name if college else 'All Colleges'

    if report_type == 'attendance':
        _build_pdf_header(elements, college, 'ATTENDANCE REPORT', f'{college_label}  |  {generated_on} IST', styles=styles, PRIMARY=PRIMARY)
        elements.append(Spacer(1, 10))

        header = [Paragraph(h, styles['TableHeader']) for h in ['Dept', 'Department Name', 'Present', 'Total', 'Attendance %']]
        rows = [header]
        for dept in departments.order_by('code'):
            total   = Attendance.objects.filter(student__department=dept).count()
            present = Attendance.objects.filter(student__department=dept, status='PRESENT').count()
            pct     = round(present / total * 100, 1) if total else 0
            pct_color = colors.HexColor('#16a34a') if pct >= 75 else colors.HexColor('#dc2626')
            rows.append([
                Paragraph(dept.code,  styles['TableCell']),
                Paragraph(dept.name,  styles['TableCell']),
                Paragraph(str(present), styles['TableCell']),
                Paragraph(str(total),   styles['TableCell']),
                Paragraph(f'{pct}%',    ParagraphStyle_colored(styles, pct_color)),
            ])
        system_report_type = 'ATTENDANCE'
        filename = f'attendance-report-{timezone.now():%Y%m%d%H%M%S}.pdf'

    elif report_type == 'payments':
        _build_pdf_header(elements, college, 'PAYMENTS REPORT', f'{college_label}  |  {generated_on} IST', styles=styles, PRIMARY=PRIMARY)
        elements.append(Spacer(1, 10))

        fee_qs = Fee.objects.filter(student__department__in=departments).select_related('student__user', 'student__department')
        header = [Paragraph(h, styles['TableHeader']) for h in ['Roll No.', 'Name', 'Dept', 'Total (Rs)', 'Paid (Rs)', 'Balance (Rs)', 'Status']]
        rows = [header]
        for fee in fee_qs.order_by('student__roll_number'):
            balance = max(fee.total_amount - fee.paid_amount, 0)
            status_color = {'PAID': colors.HexColor('#16a34a'), 'PARTIAL': colors.HexColor('#d97706'), 'PENDING': colors.HexColor('#dc2626')}.get(fee.status, MUTED)
            rows.append([
                Paragraph(fee.student.roll_number, styles['TableCell']),
                Paragraph(fee.student.user.get_full_name() or fee.student.user.username, styles['TableCell']),
                Paragraph(fee.student.department.code, styles['TableCell']),
                Paragraph(f'{fee.total_amount:.0f}', styles['TableCell']),
                Paragraph(f'{fee.paid_amount:.0f}',  styles['TableCell']),
                Paragraph(f'{balance:.0f}',           styles['TableCell']),
                Paragraph(fee.status, ParagraphStyle_colored(styles, status_color)),
            ])
        system_report_type = 'PAYMENT'
        filename = f'payments-report-{timezone.now():%Y%m%d%H%M%S}.pdf'

    elif report_type == 'results':
        _build_pdf_header(elements, college, 'RESULTS REPORT', f'{college_label}  |  {generated_on} IST', styles=styles, PRIMARY=PRIMARY)
        elements.append(Spacer(1, 10))

        result_qs = Result.objects.filter(student__department__in=departments).select_related('student__user', 'student__department')
        header = [Paragraph(h, styles['TableHeader']) for h in ['Roll No.', 'Name', 'Dept', 'Sem', 'GPA', 'Percentage', 'Result']]
        rows = [header]
        for result in result_qs.order_by('student__roll_number', 'semester'):
            pass_color = colors.HexColor('#16a34a') if result.percentage >= 40 else colors.HexColor('#dc2626')
            pass_label = 'PASS' if result.percentage >= 40 else 'FAIL'
            rows.append([
                Paragraph(result.student.roll_number, styles['TableCell']),
                Paragraph(result.student.user.get_full_name() or result.student.user.username, styles['TableCell']),
                Paragraph(result.student.department.code, styles['TableCell']),
                Paragraph(str(result.semester), styles['TableCell']),
                Paragraph(f'{result.gpa:.2f}',       styles['TableCell']),
                Paragraph(f'{result.percentage:.1f}%', styles['TableCell']),
                Paragraph(pass_label, ParagraphStyle_colored(styles, pass_color)),
            ])
        system_report_type = 'RESULT'
        filename = f'results-report-{timezone.now():%Y%m%d%H%M%S}.pdf'

    else:
        raise PermissionDenied('Invalid report type.')

    # Build the data table
    col_widths = {
        'attendance': ['10%', '40%', '15%', '15%', '20%'],
        'payments':   ['18%', '22%', '10%', '12%', '12%', '13%', '13%'],
        'results':    ['18%', '24%', '10%', '8%',  '10%', '15%', '15%'],
    }
    data_table = Table(rows, colWidths=col_widths[report_type])
    data_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  PRIMARY),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID',     (0,0), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 6),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('WORDWRAP',      (0,0), (-1,-1), True),
    ]))
    elements.append(data_table)
    _build_pdf_footer_note(elements, college, styles)

    doc.build(elements)
    payload = buf.getvalue()

    from django.core.files.base import ContentFile
    report = SystemReport(report_type=system_report_type, generated_by=request.user)
    report.file.save(filename, ContentFile(payload), save=True)

    response = HttpResponse(payload, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def ParagraphStyle_colored(styles, color):
    """Returns a copy of TableCell style with a specific text color."""
    from reportlab.lib.styles import ParagraphStyle
    return ParagraphStyle('_colored', parent=styles['TableCell'], textColor=color, fontName='Helvetica-Bold')


def error_400(request, exception=None):
    return render(request, 'errors/400.html', status=400)


def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    return render(request, 'errors/500.html', status=500)


def csrf_failure(request, reason=''):
    return render(request, 'errors/403.html', {'reason': reason}, status=403)


# ── EXAMINATION DEPARTMENT ────────────────────────────────────────────────────

def _exam_controller_guard(request):
    """
    Returns the ExamStaff instance for the current user, or None.
    Falls back to legacy ExamController for backward compatibility.
    """
    try:
        return ExamStaff.objects.select_related('college').get(user=request.user, is_active=True)
    except ExamStaff.DoesNotExist:
        pass
    # Legacy fallback — wrap ExamController as a duck-typed object
    try:
        ec = ExamController.objects.select_related('college').get(user=request.user)
        # Attach the properties ExamStaff has so views don't break
        ec.exam_role = 'COE'
        ec.get_exam_role_display = lambda: 'Controller of Examinations'
        ec.can_publish = True
        ec.can_verify = True
        ec.can_manage_schedule = True
        ec.can_manage_hall_tickets = True
        ec.departments_list = []
        return ec
    except ExamController.DoesNotExist:
        return None


def _get_exam_college(ec):
    return ec.college


@login_required
def exam_dashboard(request):
    ec = _exam_controller_guard(request)
    if not ec:
        messages.error(request, 'Exam Department access not found. Contact admin.')
        return redirect('dashboard')

    college = ec.college
    exams = Exam.objects.filter(college=college).order_by('-start_date')[:20]
    exam_types = ExamType.objects.filter(college=college, is_active=True)
    departments = Department.objects.filter(college=college, is_deleted=False).order_by('name')

    # Exam staff roster (all active staff for this college)
    exam_staff_list = ExamStaff.objects.filter(college=college, is_active=True).select_related('user').order_by('exam_role')

    # Evaluation schemes
    schemes = EvaluationScheme.objects.filter(college=college, is_active=True).select_related('department').order_by('name')

    # Stats
    total_exams = Exam.objects.filter(college=college).count()
    pending_marks = Marks.objects.filter(
        exam__college=college,
        exam__start_date__lte=timezone.now().date()
    ).count()
    published_results = ExamResult.objects.filter(exam__college=college, status='PUBLISHED').count()
    pending_results = ExamResult.objects.filter(exam__college=college, status='DRAFT').count()
    pending_revals = RevaluationRequest.objects.filter(
        marks__exam__college=college, status='PENDING'
    ).count()
    hall_tickets_issued = HallTicket.objects.filter(exam__college=college, status='ISSUED').count()
    detained_students = HallTicket.objects.filter(exam__college=college, status='DETAINED').count()

    # Recent audit log
    recent_log = ExamStaffLog.objects.filter(exam__college=college).select_related('staff__user', 'exam')[:10]

    context = {
        'ec': ec, 'college': college,
        'exams': exams,
        'exam_types': exam_types,
        'departments': departments,
        'exam_staff_list': exam_staff_list,
        'schemes': schemes,
        'total_exams': total_exams,
        'pending_marks': pending_marks,
        'published_results': published_results,
        'pending_results': pending_results,
        'pending_revals': pending_revals,
        'hall_tickets_issued': hall_tickets_issued,
        'detained_students': detained_students,
        'recent_log': recent_log,
        'branding': _get_college_branding(college),
    }
    return render(request, 'exam/dashboard.html', context)


# ── EXAM STAFF MANAGEMENT ─────────────────────────────────────────────────────

@login_required
def exam_staff_list(request):
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
    staff = ExamStaff.objects.filter(college=ec.college).select_related('user').order_by('exam_role', 'user__first_name')
    return render(request, 'exam/staff_list.html', {
        'ec': ec, 'staff': staff,
        'branding': _get_college_branding(ec.college),
    })


@login_required
def exam_staff_add(request):
    ec = _exam_controller_guard(request)
    if not ec or ec.exam_role not in ('COE', 'DEPUTY_COE'):
        messages.error(request, 'Only COE or Deputy COE can add exam staff.')
        return redirect('exam_dashboard')
    college = ec.college
    departments = Department.objects.filter(college=college, is_deleted=False).order_by('name')

    if request.method == 'POST':
        first_name  = request.POST.get('first_name', '').strip()
        last_name   = request.POST.get('last_name', '').strip()
        username    = request.POST.get('username', '').strip()
        email       = request.POST.get('email', '').strip()
        password    = request.POST.get('password', '').strip()
        employee_id = request.POST.get('employee_id', '').strip()
        phone       = request.POST.get('phone_number', '').strip()
        exam_role   = request.POST.get('exam_role', 'COORDINATOR')
        dept_ids    = request.POST.getlist('departments')

        if not all([first_name, last_name, username, employee_id]):
            messages.error(request, 'First name, last name, username, and employee ID are required.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already taken.')
        elif ExamStaff.objects.filter(employee_id=employee_id).exists():
            messages.error(request, f'Employee ID "{employee_id}" already exists.')
        else:
            password_value, generated = _resolve_password(password)
            user = User.objects.create_user(
                username=username, email=email, password=password_value,
                first_name=first_name, last_name=last_name,
            )
            UserRole.objects.create(user=user, role=7, college=college)
            staff = ExamStaff.objects.create(
                user=user, college=college,
                exam_role=exam_role, employee_id=employee_id, phone_number=phone,
            )
            if dept_ids:
                staff.departments.set(Department.objects.filter(pk__in=dept_ids, college=college))
            msg = f'Exam staff "{user.get_full_name()}" created.'
            if generated:
                msg += f' Temporary password: {password_value}'
            messages.success(request, msg)
            return redirect('exam_staff_list')

    return render(request, 'exam/staff_form.html', {
        'ec': ec, 'departments': departments,
        'roles': ExamStaff.EXAM_ROLE_CHOICES,
        'branding': _get_college_branding(college),
    })


@login_required
def exam_staff_toggle(request, pk):
    ec = _exam_controller_guard(request)
    if not ec or ec.exam_role not in ('COE', 'DEPUTY_COE'):
        return redirect('exam_dashboard')
    staff = get_object_or_404(ExamStaff, pk=pk, college=ec.college)
    if request.method == 'POST':
        staff.is_active = not staff.is_active
        staff.save(update_fields=['is_active'])
        state = 'activated' if staff.is_active else 'deactivated'
        messages.success(request, f'{staff.user.get_full_name()} {state}.')
    return redirect('exam_staff_list')


# ── EXAM TYPES ────────────────────────────────────────────────────────────────

@login_required
def exam_type_list(request):
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
    types = ExamType.objects.filter(college=ec.college).order_by('category', 'name')
    return render(request, 'exam/exam_types.html', {'ec': ec, 'types': types, 'branding': _get_college_branding(ec.college)})


@login_required
def exam_type_add(request):
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'CIE')
        max_marks = float(request.POST.get('max_marks', 100) or 100)
        passing_marks = float(request.POST.get('passing_marks', 40) or 40)
        weightage = float(request.POST.get('weightage_percent', 100) or 100)
        if not name:
            messages.error(request, 'Name is required.')
        elif ExamType.objects.filter(college=ec.college, name=name).exists():
            messages.error(request, f'Exam type "{name}" already exists.')
        else:
            ExamType.objects.create(
                college=ec.college, name=name, category=category,
                max_marks=max_marks, passing_marks=passing_marks,
                weightage_percent=weightage,
            )
            messages.success(request, f'Exam type "{name}" created.')
            return redirect('exam_type_list')
    categories = ExamType.CATEGORY_CHOICES
    return render(request, 'exam/exam_type_form.html', {'ec': ec, 'categories': categories, 'branding': _get_college_branding(ec.college)})


@login_required
def exam_type_delete(request, pk):
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
    et = get_object_or_404(ExamType, pk=pk, college=ec.college)
    if request.method == 'POST':
        et.delete()
        messages.success(request, 'Exam type deleted.')
    return redirect('exam_type_list')


# ── EXAM SCHEDULE ─────────────────────────────────────────────────────────────

@login_required
def exam_schedule(request, exam_id):
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
    exam = get_object_or_404(Exam, pk=exam_id, college=ec.college)
    schedules = ExamSchedule.objects.filter(exam=exam).select_related(
        'subject', 'exam_type', 'invigilator__user'
    ).order_by('date', 'start_time')
    subjects = Subject.objects.filter(
        department__college=ec.college, semester=exam.semester
    ).order_by('department__code', 'name')
    exam_types = ExamType.objects.filter(college=ec.college, is_active=True)
    faculty_list = Faculty.objects.filter(department__college=ec.college).select_related('user').order_by('user__first_name')

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        exam_type_id = request.POST.get('exam_type') or None
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        venue = request.POST.get('venue', '').strip()
        invigilator_id = request.POST.get('invigilator') or None
        max_marks = float(request.POST.get('max_marks', 100) or 100)
        passing_marks = float(request.POST.get('passing_marks', 40) or 40)

        subject = get_object_or_404(Subject, pk=subject_id, department__college=ec.college)
        ExamSchedule.objects.update_or_create(
            exam=exam, subject=subject,
            defaults={
                'exam_type_id': exam_type_id,
                'date': date, 'start_time': start_time, 'end_time': end_time,
                'venue': venue, 'invigilator_id': invigilator_id,
                'max_marks': max_marks, 'passing_marks': passing_marks,
            }
        )
        messages.success(request, f'Schedule set for {subject.name}.')
        return redirect('exam_schedule', exam_id=exam.pk)

    return render(request, 'exam/exam_schedule.html', {
        'ec': ec, 'exam': exam, 'schedules': schedules,
        'subjects': subjects, 'exam_types': exam_types, 'faculty_list': faculty_list,
        'branding': _get_college_branding(ec.college),
    })


@login_required
def exam_schedule_delete(request, exam_id, pk):
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
    slot = get_object_or_404(ExamSchedule, pk=pk, exam__college=ec.college)
    if request.method == 'POST':
        slot.delete()
        messages.success(request, 'Schedule entry removed.')
    return redirect('exam_schedule', exam_id=exam_id)


# ── HALL TICKETS ──────────────────────────────────────────────────────────────

@login_required
def exam_hall_tickets(request, exam_id):
    """Generate eligibility + hall tickets for all students in an exam's semester."""
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
    exam = get_object_or_404(Exam, pk=exam_id, college=ec.college)

    dept_filter = request.GET.get('dept')
    students_qs = Student.objects.filter(
        department__college=ec.college,
        current_semester=exam.semester,
        status='ACTIVE',
    ).select_related('user', 'department').order_by('department__code', 'roll_number')
    if dept_filter:
        students_qs = students_qs.filter(department_id=dept_filter)

    # Bulk-fetch existing hall tickets
    existing_ht = {ht.student_id: ht for ht in HallTicket.objects.filter(exam=exam)}

    # Bulk-fetch attendance % per student for this semester
    att_agg = Attendance.objects.filter(
        student__in=students_qs,
        session__subject__semester=exam.semester,
    ).values('student_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    att_map = {row['student_id']: row for row in att_agg}

    # Bulk-fetch fee dues
    fee_dues = set(
        Fee.objects.filter(
            student__in=students_qs, status__in=['PENDING', 'PARTIAL']
        ).values_list('student_id', flat=True)
    )

    # Load composite eligibility config (ExamEligibilityConfig takes precedence over defaults)
    elig_config = (
        ExamEligibilityConfig.objects.filter(college=ec.college, exam=exam, is_active=True).first()
        or ExamEligibilityConfig.objects.filter(college=ec.college, exam__isnull=True, is_active=True).first()
    )

    # Bulk-fetch internal marks averages if config requires it
    internal_map = {}
    if elig_config and elig_config.check_internal_marks:
        im_agg = InternalMark.objects.filter(
            student__in=students_qs,
            subject__semester=exam.semester,
        ).values('student_id').annotate(
            total_ia=Sum(F('ia1') + F('ia2') + F('assignment_marks') + F('attendance_marks'))
        )
        internal_map = {r['student_id']: r['total_ia'] or 0 for r in im_agg}

    # Bulk-fetch active disciplinary records if config requires it
    disciplinary_set = set()
    if elig_config and elig_config.check_disciplinary:
        disciplinary_set = set(
            DisciplinaryRecord.objects.filter(
                student__in=students_qs, status='ACTIVE'
            ).values_list('student_id', flat=True)
        )

    rows = []
    for student in students_qs:
        att = att_map.get(student.id, {'total': 0, 'present': 0})
        pct = round(att['present'] / att['total'] * 100, 1) if att['total'] > 0 else 0
        has_dues = student.id in fee_dues
        ht = existing_ht.get(student.id)
        exam_rule = _get_attendance_rule(ec.college, student.department, exam.semester)

        # Composite eligibility check
        if elig_config:
            threshold = elig_config.min_attendance_pct
            gates = []
            if elig_config.check_attendance:
                att_ok = pct >= threshold or att['total'] < exam_rule.min_sessions_for_check
                gates.append(att_ok)
            if elig_config.check_fee_clearance:
                fee_ok = not has_dues or (elig_config.allow_partial_fee and student.id in fee_dues)
                gates.append(not has_dues)
            if elig_config.check_internal_marks:
                im_total = internal_map.get(student.id, 0)
                gates.append(im_total >= elig_config.min_internal_marks_pct)
            if elig_config.check_disciplinary:
                gates.append(student.id not in disciplinary_set)
            eligible = all(gates) if elig_config.require_all_gates else any(gates)
            auto_status = 'ELIGIBLE' if eligible else ('DETAINED' if (elig_config.check_attendance and pct < threshold) else 'WITHHELD')
        else:
            threshold = exam_rule.effective_min_overall
            att_fail = att['total'] >= exam_rule.min_sessions_for_check and pct < threshold
            auto_status = 'DETAINED' if att_fail else ('WITHHELD' if has_dues else 'ELIGIBLE')

        rows.append({
            'student': student, 'att_pct': pct,
            'has_dues': has_dues, 'hall_ticket': ht,
            'threshold': threshold if elig_config else exam_rule.effective_min_overall,
            'auto_status': auto_status,
            'has_disciplinary': student.id in disciplinary_set,
        })

    if request.method == 'POST' and request.POST.get('action') == 'generate':
        created = updated = 0
        for student in students_qs:
            att = att_map.get(student.id, {'total': 0, 'present': 0})
            pct = round(att['present'] / att['total'] * 100, 1) if att['total'] > 0 else 0
            has_dues = student.id in fee_dues
            exam_rule = _get_attendance_rule(ec.college, student.department, exam.semester)
            threshold = exam_rule.effective_min_overall
            # Check for approved override
            has_override = EligibilityOverride.objects.filter(
                student=student, exam=exam, status='APPROVED'
            ).exists()
            if has_override:
                status = 'ISSUED'
            elif att['total'] >= exam_rule.min_sessions_for_check and pct < threshold:
                status = 'DETAINED'
            elif has_dues:
                status = 'WITHHELD'
            else:
                status = 'ISSUED'
            ht, was_created = HallTicket.objects.update_or_create(
                student=student, exam=exam,
                defaults={
                    'status': status, 'attendance_pct': pct,
                    'has_fee_dues': has_dues,
                    'issued_at': timezone.now() if status == 'ISSUED' else None,
                    'generated_by': request.user,
                }
            )
            if was_created:
                created += 1
            else:
                updated += 1
        messages.success(request, f'Hall tickets generated: {created} new, {updated} updated.')
        return redirect('exam_hall_tickets', exam_id=exam.pk)

    departments = Department.objects.filter(college=ec.college, is_deleted=False).order_by('name')
    return render(request, 'exam/hall_tickets.html', {
        'ec': ec, 'exam': exam, 'rows': rows,
        'departments': departments, 'dept_filter': dept_filter,
        'branding': _get_college_branding(ec.college),
    })


# ── MARKS OVERVIEW ────────────────────────────────────────────────────────────

@login_required
@login_required
def exam_marks_moderation(request, exam_id):
    """Bulk scale/add/cap marks for a subject. Snapshots results before applying."""
    ec = _exam_controller_guard(request)
    if not ec or not ec.can_verify:
        return redirect('exam_dashboard')
    exam = get_object_or_404(Exam, pk=exam_id, college=ec.college)

    # Block if frozen
    freeze_rec = ResultFreeze.objects.filter(college=ec.college, exam=exam).first()
    if freeze_rec and freeze_rec.is_frozen:
        messages.error(request, 'Results are frozen. Unfreeze before applying moderation.')
        return redirect('exam_results', exam_id=exam.pk)

    subjects = Subject.objects.filter(
        department__college=ec.college, semester=exam.semester
    ).order_by('department__code', 'name')
    moderations = MarksModeration.objects.filter(exam=exam).select_related('subject', 'created_by').order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            subj_id = request.POST.get('subject')
            mod_type = request.POST.get('moderation_type', 'ADD')
            value = _safe_float(request.POST.get('value', '0'))
            reason = request.POST.get('reason', '').strip()
            if not reason:
                messages.error(request, 'Reason is required.')
            else:
                MarksModeration.objects.create(
                    exam=exam,
                    subject_id=subj_id,
                    moderation_type=mod_type,
                    value=value,
                    reason=reason,
                    created_by=request.user,
                )
                messages.success(request, 'Moderation rule created. Apply it to update marks.')

        elif action == 'apply':
            mod_id = request.POST.get('mod_id')
            mod = get_object_or_404(MarksModeration, pk=mod_id, exam=exam, applied=False)
            with transaction.atomic():
                marks_qs = Marks.objects.filter(exam=exam, subject=mod.subject)
                # Snapshot results before moderation
                affected_students = marks_qs.values_list('student_id', flat=True).distinct()
                for sid in affected_students:
                    result_obj = Result.objects.filter(student_id=sid, semester=exam.semester).first()
                    if result_obj:
                        last_v = ResultVersion.objects.filter(result=result_obj).count()
                        ResultVersion.objects.create(
                            result=result_obj, version_no=last_v + 1,
                            sgpa=result_obj.sgpa, total_marks=result_obj.total_marks,
                            percentage=result_obj.percentage,
                            snapshot_reason=f'Before moderation: {mod.get_moderation_type_display()} {mod.value}',
                            created_by=request.user,
                        )
                # Apply moderation
                for mark in marks_qs:
                    if mod.moderation_type == 'ADD':
                        mark.marks_obtained = min(mark.marks_obtained + mod.value, mark.max_marks)
                    elif mod.moderation_type == 'SCALE':
                        mark.marks_obtained = min(mark.marks_obtained * mod.value, mark.max_marks)
                    elif mod.moderation_type == 'CAP':
                        mark.marks_obtained = min(mark.marks_obtained, mod.value)
                    mark.grade = _calculate_grade(mark.marks_obtained, mark.max_marks)
                    mark.grade_point = _grade_to_point(mark.grade)
                    mark.save(update_fields=['marks_obtained', 'grade', 'grade_point'])
                mod.applied = True
                mod.applied_by = request.user
                mod.applied_at = timezone.now()
                mod.save()
                _audit('MARKS_UPDATED', request.user,
                       f"Moderation applied: {mod.subject.code} {mod.get_moderation_type_display()} {mod.value}. Reason: {mod.reason}",
                       college=ec.college, request=request)
                messages.success(request, f'Moderation applied to {marks_qs.count()} marks records.')
        return redirect('exam_marks_moderation', exam_id=exam.pk)

    return render(request, 'exam/moderation.html', {
        'ec': ec, 'exam': exam, 'subjects': subjects, 'moderations': moderations,
        'mod_types': MarksModeration.MODERATION_TYPES,
        'branding': _get_college_branding(ec.college),
    })


@login_required
def exam_marks_overview(request, exam_id):
    """Show marks entry status per subject — how many students have marks entered."""
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
    exam = get_object_or_404(Exam, pk=exam_id, college=ec.college)

    subjects = Subject.objects.filter(
        department__college=ec.college, semester=exam.semester
    ).select_related('department').order_by('department__code', 'name')

    # Total eligible students per subject (by dept + semester)
    enrolled_agg = Student.objects.filter(
        department__college=ec.college,
        current_semester=exam.semester,
        status='ACTIVE',
    ).values('department_id').annotate(count=Count('id'))
    enrolled_by_dept = {row['department_id']: row['count'] for row in enrolled_agg}

    # Marks entered per subject
    marks_agg = Marks.objects.filter(exam=exam).values('subject_id').annotate(count=Count('id'))
    marks_by_subj = {row['subject_id']: row['count'] for row in marks_agg}

    rows = []
    for subj in subjects:
        enrolled = enrolled_by_dept.get(subj.department_id, 0)
        entered = marks_by_subj.get(subj.id, 0)
        rows.append({
            'subject': subj,
            'enrolled': enrolled,
            'entered': entered,
            'pending': max(enrolled - entered, 0),
            'complete': enrolled > 0 and entered >= enrolled,
        })

    return render(request, 'exam/marks_overview.html', {
        'ec': ec, 'exam': exam, 'rows': rows,
        'branding': _get_college_branding(ec.college),
    })


# ── RESULT PUBLISHING ─────────────────────────────────────────────────────────

@login_required
def exam_results(request, exam_id):
    """Compute, verify, and publish results for an exam."""
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
    exam = get_object_or_404(Exam, pk=exam_id, college=ec.college)

    dept_filter = request.GET.get('dept')
    students_qs = Student.objects.filter(
        department__college=ec.college,
        current_semester=exam.semester,
        status='ACTIVE',
    ).select_related('user', 'department').order_by('department__code', 'roll_number')
    if dept_filter:
        students_qs = students_qs.filter(department_id=dept_filter)

    # Bulk-fetch all marks for this exam
    all_marks = Marks.objects.filter(
        exam=exam, student__in=students_qs
    ).values('student_id').annotate(
        total_obtained=Sum('marks_obtained'),
        total_max=Sum('max_marks'),
    )
    marks_map = {row['student_id']: row for row in all_marks}

    # Bulk-fetch existing ExamResult records
    existing_results = {er.student_id: er for er in ExamResult.objects.filter(exam=exam, student__in=students_qs)}

    action = request.POST.get('action')
    if request.method == 'POST' and action in ('compute', 'verify', 'publish', 'freeze', 'unfreeze'):
        # Check freeze state
        freeze_rec = ResultFreeze.objects.filter(college=ec.college, exam=exam).first()
        is_frozen = freeze_rec and freeze_rec.is_frozen

        if is_frozen and action not in ('unfreeze',):
            messages.error(request, 'Results are frozen. Unfreeze before making changes.')
            return redirect('exam_results', exam_id=exam.pk)

        student_ids = list(students_qs.values_list('id', flat=True))
        with transaction.atomic():
            if action == 'freeze':
                obj, _ = ResultFreeze.objects.get_or_create(college=ec.college, exam=exam)
                obj.is_frozen = True
                obj.frozen_by = request.user
                obj.frozen_at = timezone.now()
                obj.save()
                _audit('RESULT_PUBLISHED', request.user,
                       f"Results frozen for {exam.name}", college=ec.college, request=request)
                messages.success(request, f'Results for {exam.name} are now frozen. No further edits allowed.')
                return redirect('exam_results', exam_id=exam.pk)

            elif action == 'unfreeze':
                reason = request.POST.get('unfreeze_reason', '').strip()
                if not reason:
                    messages.error(request, 'A reason is required to unfreeze results.')
                    return redirect('exam_results', exam_id=exam.pk)
                if freeze_rec:
                    freeze_rec.is_frozen = False
                    freeze_rec.unfrozen_by = request.user
                    freeze_rec.unfreeze_reason = reason
                    freeze_rec.save()
                    _audit('RESULT_PUBLISHED', request.user,
                           f"Results unfrozen for {exam.name}. Reason: {reason}",
                           college=ec.college, request=request)
                messages.success(request, 'Results unfrozen.')
                return redirect('exam_results', exam_id=exam.pk)

            elif action == 'compute':
                for sid in student_ids:
                    m = marks_map.get(sid, {'total_obtained': 0, 'total_max': 0})
                    obtained = m['total_obtained'] or 0
                    max_m = m['total_max'] or 0
                    pct = round(obtained / max_m * 100, 1) if max_m > 0 else 0
                    _scheme = _get_evaluation_scheme(ec.college)
                    grade = _calculate_grade(obtained, max_m, scheme=_scheme) if max_m > 0 else 'NA'
                    is_pass = pct >= (_scheme.overall_passing_min if _scheme else 40.0)
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
                    # Compute and store SGPA in Result model
                    student_obj = Student.objects.get(pk=sid)
                    sgpa, total_credits = _compute_sgpa(student_obj, exam.semester, exam)
                    Result.objects.update_or_create(
                        student_id=sid, semester=exam.semester,
                        defaults={
                            'gpa': sgpa,
                            'sgpa': sgpa,
                            'total_marks': obtained,
                            'percentage': pct,
                            'total_credits': total_credits,
                        }
                    )
                messages.success(request, f'Results computed for {len(student_ids)} students. SGPA calculated.')
            elif action == 'verify':
                ExamResult.objects.filter(exam=exam, student_id__in=student_ids, status='DRAFT').update(
                    status='VERIFIED', verified_by=request.user
                )
                messages.success(request, 'Results marked as verified.')
            elif action == 'publish':
                # Snapshot current results before publishing (versioning)
                for sid in student_ids:
                    result_obj = Result.objects.filter(student_id=sid, semester=exam.semester).first()
                    if result_obj:
                        last_v = ResultVersion.objects.filter(result=result_obj).count()
                        ResultVersion.objects.create(
                            result=result_obj,
                            version_no=last_v + 1,
                            sgpa=result_obj.sgpa,
                            total_marks=result_obj.total_marks,
                            percentage=result_obj.percentage,
                            snapshot_reason='Before publication',
                            created_by=request.user,
                        )
                ExamResult.objects.filter(exam=exam, student_id__in=student_ids, status='VERIFIED').update(
                    status='PUBLISHED',
                    published_by=request.user,
                    published_at=timezone.now(),
                )
                _audit('RESULT_PUBLISHED', request.user,
                       f"Results published for {exam.name} ({len(student_ids)} students)",
                       college=ec.college, request=request)
                messages.success(request, 'Results published. Students can now view them.')
        return redirect('exam_results', exam_id=exam.pk)

    rows = []
    for student in students_qs:
        er = existing_results.get(student.id)
        rows.append({'student': student, 'result': er})

    summary = {
        'total': len(rows),
        'computed': sum(1 for r in rows if r['result']),
        'verified': sum(1 for r in rows if r['result'] and r['result'].status == 'VERIFIED'),
        'published': sum(1 for r in rows if r['result'] and r['result'].status == 'PUBLISHED'),
        'passed': sum(1 for r in rows if r['result'] and r['result'].is_pass),
        'failed': sum(1 for r in rows if r['result'] and not r['result'].is_pass),
    }

    freeze_rec = ResultFreeze.objects.filter(college=ec.college, exam=exam).first()
    is_frozen = freeze_rec and freeze_rec.is_frozen

    departments = Department.objects.filter(college=ec.college, is_deleted=False).order_by('name')
    return render(request, 'exam/results.html', {
        'ec': ec, 'exam': exam, 'rows': rows, 'summary': summary,
        'departments': departments, 'dept_filter': dept_filter,
        'freeze_rec': freeze_rec, 'is_frozen': is_frozen,
        'branding': _get_college_branding(ec.college),
    })


# ── REVALUATION ───────────────────────────────────────────────────────────────

@login_required
def exam_revaluations(request):
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
    revals = RevaluationRequest.objects.filter(
        marks__exam__college=ec.college
    ).select_related('student__user', 'marks__subject', 'marks__exam').order_by('-created_at')[:50]
    return render(request, 'exam/revaluations.html', {
        'ec': ec, 'revals': revals, 'branding': _get_college_branding(ec.college),
    })


@login_required
def exam_reval_update(request, pk):
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
    reval = get_object_or_404(RevaluationRequest, pk=pk, marks__exam__college=ec.college)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            revised = request.POST.get('revised_marks', '').strip()
            try:
                revised_val = float(revised)
            except (ValueError, TypeError):
                messages.error(request, 'Enter valid revised marks.')
                return redirect('exam_revaluations')
            reval.status = 'COMPLETED'
            reval.revised_marks = revised_val
            reval.reviewed_by = request.user
            reval.save()
            old_marks = reval.marks.marks_obtained
            reval.marks.marks_obtained = revised_val
            reval.marks.grade = _calculate_grade(revised_val, reval.marks.max_marks)
            reval.marks.grade_point = _grade_to_point(reval.marks.grade)
            reval.marks.save(update_fields=['marks_obtained', 'grade', 'grade_point'])
            # Recalculate SGPA for this student's semester
            sgpa, total_credits = _compute_sgpa(reval.marks.student, reval.marks.subject.semester, reval.marks.exam)
            Result.objects.filter(student=reval.marks.student, semester=reval.marks.subject.semester).update(
                gpa=sgpa, sgpa=sgpa, total_credits=total_credits
            )
            _audit('MARKS_REVAL', request.user,
                   f"Revaluation: {reval.marks.student.roll_number} {reval.marks.subject.code} {old_marks} → {revised_val} ({reval.marks.grade}). SGPA recalculated: {sgpa}",
                   student=reval.marks.student, college=ec.college, request=request,
                   old_value=str(old_marks), new_value=str(revised_val))
            messages.success(request, f'Revaluation completed. Marks updated to {revised_val}. SGPA recalculated.')
        elif action == 'reject':
            reval.status = 'REJECTED'
            reval.reviewed_by = request.user
            reval.save()
            messages.success(request, 'Revaluation request rejected.')
    return redirect('exam_revaluations')


# ── STUDENT: REQUEST REVALUATION ──────────────────────────────────────────────

@login_required
def student_request_revaluation(request, marks_id):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('dashboard')
    marks = get_object_or_404(Marks, pk=marks_id, student=student)
    # Only allow if result is published
    er = ExamResult.objects.filter(student=student, exam=marks.exam, status='PUBLISHED').first()
    if not er:
        messages.error(request, 'Results are not published yet.')
        return redirect('student_dashboard')
    if RevaluationRequest.objects.filter(student=student, marks=marks).exists():
        messages.warning(request, 'You have already requested revaluation for this subject.')
        return redirect('student_dashboard')
    # Redirect to fee payment first — request is created after payment verified
    return redirect('student_reval_fee_pay', marks_id=marks_id)


# ── DASHBOARD REDIRECT ────────────────────────────────────────────────────────

def _exam_controller_redirect(request):
    """Used in dashboard_redirect to route exam controllers."""
    return redirect('exam_dashboard')


# ── EXAM STAFF MANAGEMENT ─────────────────────────────────────────────────────

@login_required
def exam_staff_list(request):
    ec = _exam_controller_guard(request)
    if not ec or not ec.can_publish:  # only CoE / Deputy can manage staff
        messages.error(request, 'Only the Controller of Examinations can manage exam staff.')
        return redirect('exam_dashboard')
    staff = ExamStaff.objects.filter(college=ec.college).select_related('user').prefetch_related('departments').order_by('exam_role', 'user__first_name')
    return render(request, 'exam/staff_list.html', {
        'ec': ec, 'staff': staff, 'branding': _get_college_branding(ec.college),
    })


@login_required
def exam_staff_add(request):
    ec = _exam_controller_guard(request)
    if not ec or not ec.can_publish:
        return redirect('exam_dashboard')
    college = ec.college
    departments = Department.objects.filter(college=college, is_deleted=False).order_by('name')
    role_choices = ExamStaff.EXAM_ROLE_CHOICES

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        exam_role = request.POST.get('exam_role', 'COORDINATOR')
        employee_id = request.POST.get('employee_id', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        dept_ids = request.POST.getlist('departments')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, f'No user with username "{username}" found.')
            return render(request, 'exam/staff_form.html', {'ec': ec, 'departments': departments, 'role_choices': role_choices, 'branding': _get_college_branding(college)})

        if ExamStaff.objects.filter(user=user).exists():
            messages.error(request, f'{username} is already an exam staff member.')
            return render(request, 'exam/staff_form.html', {'ec': ec, 'departments': departments, 'role_choices': role_choices, 'branding': _get_college_branding(college)})

        if ExamStaff.objects.filter(employee_id=employee_id).exists():
            messages.error(request, f'Employee ID "{employee_id}" already exists.')
            return render(request, 'exam/staff_form.html', {'ec': ec, 'departments': departments, 'role_choices': role_choices, 'branding': _get_college_branding(college)})

        staff = ExamStaff.objects.create(
            user=user, college=college, exam_role=exam_role,
            employee_id=employee_id, phone_number=phone,
        )
        if dept_ids:
            staff.departments.set(Department.objects.filter(pk__in=dept_ids, college=college))

        # Set UserRole to 7 (Exam Controller) if not already set
        UserRole.objects.update_or_create(user=user, defaults={'role': 7, 'college': college})

        ExamStaffLog.objects.create(
            staff=ec if isinstance(ec, ExamStaff) else None,
            action='STAFF_ADDED',
            description=f'Added {user.get_full_name()} as {staff.get_exam_role_display()}',
        )
        messages.success(request, f'{user.get_full_name()} added as {staff.get_exam_role_display()}.')
        return redirect('exam_staff_list')

    return render(request, 'exam/staff_form.html', {
        'ec': ec, 'departments': departments, 'role_choices': role_choices,
        'branding': _get_college_branding(college),
    })


@login_required
def exam_staff_toggle(request, pk):
    ec = _exam_controller_guard(request)
    if not ec or not ec.can_publish:
        return redirect('exam_dashboard')
    staff = get_object_or_404(ExamStaff, pk=pk, college=ec.college)
    if request.method == 'POST':
        staff.is_active = not staff.is_active
        staff.save(update_fields=['is_active'])
        messages.success(request, f'{"Activated" if staff.is_active else "Deactivated"} {staff.user.get_full_name()}.')
    return redirect('exam_staff_list')


# ── EVALUATION SCHEMES ────────────────────────────────────────────────────────

@login_required
def exam_scheme_list(request):
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
    schemes = EvaluationScheme.objects.filter(college=ec.college).select_related('department').order_by('name')
    return render(request, 'exam/scheme_list.html', {
        'ec': ec, 'schemes': schemes, 'branding': _get_college_branding(ec.college),
    })


@login_required
def exam_scheme_add(request):
    ec = _exam_controller_guard(request)
    if not ec or not ec.can_verify:
        return redirect('exam_dashboard')
    college = ec.college
    departments = Department.objects.filter(college=college, is_deleted=False).order_by('name')
    grading_choices = EvaluationScheme.GRADING_CHOICES

    if request.method == 'POST':
        p = request.POST
        dept_id = p.get('department') or None
        name = p.get('name', '').strip()
        if not name:
            messages.error(request, 'Scheme name is required.')
        elif EvaluationScheme.objects.filter(college=college, department_id=dept_id, name=name).exists():
            messages.error(request, f'Scheme "{name}" already exists for this department.')
        else:
            scheme = EvaluationScheme.objects.create(
                college=college,
                department_id=dept_id,
                name=name,
                description=p.get('description', '').strip(),
                cie_count=int(p.get('cie_count', 2) or 2),
                cie_best_of=int(p.get('cie_best_of', 2) or 2),
                cie_max_per_test=float(p.get('cie_max_per_test', 30) or 30),
                cie_total_max=float(p.get('cie_total_max', 50) or 50),
                see_max=float(p.get('see_max', 100) or 100),
                see_scaled_to=float(p.get('see_scaled_to', 50) or 50),
                see_passing_min=float(p.get('see_passing_min', 35) or 35),
                has_practical='has_practical' in p,
                practical_internal_max=float(p.get('practical_internal_max', 25) or 25) if 'has_practical' in p else None,
                practical_external_max=float(p.get('practical_external_max', 25) or 25) if 'has_practical' in p else None,
                overall_passing_min=float(p.get('overall_passing_min', 40) or 40),
                grading_type=p.get('grading_type', 'ABSOLUTE'),
            )
            ExamStaffLog.objects.create(
                staff=ec if isinstance(ec, ExamStaff) else None,
                action='SCHEME_CHANGED',
                description=f'Created evaluation scheme "{scheme.name}"',
            )
            messages.success(request, f'Evaluation scheme "{name}" created.')
            return redirect('exam_scheme_list')

    return render(request, 'exam/scheme_form.html', {
        'ec': ec, 'departments': departments, 'grading_choices': grading_choices,
        'branding': _get_college_branding(college),
    })


@login_required
def exam_scheme_delete(request, pk):
    ec = _exam_controller_guard(request)
    if not ec or not ec.can_verify:
        return redirect('exam_dashboard')
    scheme = get_object_or_404(EvaluationScheme, pk=pk, college=ec.college)
    if request.method == 'POST':
        scheme.delete()
        messages.success(request, 'Evaluation scheme deleted.')
    return redirect('exam_scheme_list')


# ── VALUATION ASSIGNMENTS ─────────────────────────────────────────────────────

@login_required
def exam_valuation(request, exam_id):
    """Assign first/second valuators to each subject in an exam."""
    ec = _exam_controller_guard(request)
    if not ec or not ec.can_manage_schedule:
        return redirect('exam_dashboard')
    exam = get_object_or_404(Exam, pk=exam_id, college=ec.college)
    schedules = ExamSchedule.objects.filter(exam=exam).select_related(
        'subject__department'
    ).prefetch_related('valuations__faculty__user').order_by('date', 'subject__name')
    faculty_list = Faculty.objects.filter(department__college=ec.college).select_related('user', 'department').order_by('user__first_name')

    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        valuation_type = request.POST.get('valuation_type', 'FIRST')
        faculty_id = request.POST.get('faculty') or None
        external_name = request.POST.get('external_name', '').strip()
        external_inst = request.POST.get('external_institution', '').strip()

        schedule = get_object_or_404(ExamSchedule, pk=schedule_id, exam=exam)
        ValuationAssignment.objects.update_or_create(
            exam_schedule=schedule, valuation_type=valuation_type,
            defaults={
                'faculty_id': faculty_id,
                'external_name': external_name,
                'external_institution': external_inst,
                'assigned_by': request.user,
                'completed': False,
            }
        )
        messages.success(request, f'{valuation_type.title()} valuation assigned for {schedule.subject.name}.')
        return redirect('exam_valuation', exam_id=exam.pk)

    return render(request, 'exam/valuation.html', {
        'ec': ec, 'exam': exam, 'schedules': schedules,
        'faculty_list': faculty_list,
        'valuation_types': ValuationAssignment.VALUATION_TYPE,
        'branding': _get_college_branding(ec.college),
    })


def _exam_controller_redirect(request):
    """Used in dashboard_redirect to route exam controllers."""
    return redirect('exam_dashboard')


# ── ATTENDANCE RULE ENGINE — ADMIN VIEWS ─────────────────────────────────────

@login_required
def admin_attendance_rules(request):
    """Admin configures attendance eligibility rules per dept/semester."""
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    rules = AttendanceRule.objects.filter(college=college).select_related('department').order_by('department__name', 'semester')
    departments = _scope_departments(request).order_by('name')
    return render(request, 'attendance/admin_rules.html', {
        'rules': rules, 'departments': departments, 'college': college,
        'branding': _get_college_branding(college),
    })


@login_required
def admin_attendance_rule_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    departments = _scope_departments(request).order_by('name')

    if request.method == 'POST':
        p = request.POST
        dept_id  = p.get('department') or None
        semester = _safe_int(p.get('semester')) if p.get('semester') else None

        if AttendanceRule.objects.filter(college=college, department_id=dept_id, semester=semester).exists():
            messages.error(request, 'A rule for this department/semester combination already exists.')
        else:
            AttendanceRule.objects.create(
                college=college,
                department_id=dept_id,
                semester=semester,
                min_overall_pct=float(p.get('min_overall_pct', 75) or 75),
                min_subject_pct=float(p.get('min_subject_pct', 75) or 75),
                require_both='require_both' in p,
                grace_pct=float(p.get('grace_pct', 0) or 0),
                min_sessions_for_check=int(p.get('min_sessions_for_check', 5) or 5),
                mandatory_subject_pct=float(p.get('mandatory_subject_pct', 75) or 75),
                allow_medical_exemption='allow_medical_exemption' in p,
                allow_sports_exemption='allow_sports_exemption' in p,
                allow_od_exemption='allow_od_exemption' in p,
                max_exemption_days=int(p.get('max_exemption_days', 15) or 15),
                alert_below_pct=float(p.get('alert_below_pct', 75) or 75),
                critical_below_pct=float(p.get('critical_below_pct', 65) or 65),
                created_by=request.user,
            )
            messages.success(request, 'Attendance rule created.')
            return redirect('admin_attendance_rules')

    return render(request, 'attendance/admin_rule_form.html', {
        'departments': departments, 'college': college,
        'branding': _get_college_branding(college),
    })


@login_required
def admin_attendance_rule_edit(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    rule = get_object_or_404(AttendanceRule, pk=pk, college=college)
    departments = _scope_departments(request).order_by('name')

    if request.method == 'POST':
        p = request.POST
        rule.min_overall_pct = float(p.get('min_overall_pct', 75) or 75)
        rule.min_subject_pct = float(p.get('min_subject_pct', 75) or 75)
        rule.require_both = 'require_both' in p
        rule.grace_pct = float(p.get('grace_pct', 0) or 0)
        rule.min_sessions_for_check = int(p.get('min_sessions_for_check', 5) or 5)
        rule.mandatory_subject_pct = float(p.get('mandatory_subject_pct', 75) or 75)
        rule.allow_medical_exemption = 'allow_medical_exemption' in p
        rule.allow_sports_exemption = 'allow_sports_exemption' in p
        rule.allow_od_exemption = 'allow_od_exemption' in p
        rule.max_exemption_days = int(p.get('max_exemption_days', 15) or 15)
        rule.alert_below_pct = float(p.get('alert_below_pct', 75) or 75)
        rule.critical_below_pct = float(p.get('critical_below_pct', 65) or 65)
        rule.save()
        messages.success(request, 'Attendance rule updated.')
        return redirect('admin_attendance_rules')

    return render(request, 'attendance/admin_rule_form.html', {
        'rule': rule, 'departments': departments, 'college': college,
        'branding': _get_college_branding(college),
    })


@login_required
def admin_attendance_rule_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    rule = get_object_or_404(AttendanceRule, pk=pk, college=_get_admin_college(request))
    if request.method == 'POST':
        rule.delete()
        messages.success(request, 'Rule deleted.')
    return redirect('admin_attendance_rules')


# ── ATTENDANCE CORRECTION (FACULTY / HOD) ────────────────────────────────────

@login_required
def attendance_correct(request, attendance_id):
    """Faculty or HOD corrects an attendance record with a reason (creates audit log)."""
    att = get_object_or_404(Attendance, pk=attendance_id)
    subject = att.session.subject

    # Permission: must be the faculty who marked it, or HOD of the dept
    is_faculty = FacultySubject.objects.filter(faculty__user=request.user, subject=subject).exists()
    is_hod = HOD.objects.filter(user=request.user, department=subject.department).exists()
    if not is_faculty and not is_hod and not request.user.is_superuser:
        raise PermissionDenied('You cannot correct this attendance record.')

    if request.method == 'POST':
        new_status = request.POST.get('new_status')
        reason = request.POST.get('reason', '').strip()
        if new_status not in ('PRESENT', 'ABSENT', 'LATE'):
            messages.error(request, 'Invalid status.')
        elif not reason:
            messages.error(request, 'Reason is required for corrections.')
        else:
            old_status = att.status
            AttendanceCorrection.objects.create(
                attendance=att,
                old_status=old_status,
                new_status=new_status,
                reason=reason,
                corrected_by=request.user,
            )
            att.status = new_status
            att.save(update_fields=['status'])
            _audit('ATT_CORRECTED', request.user,
                   f"Attendance corrected for {att.student.roll_number} in {subject.code}: {old_status} → {new_status}. Reason: {reason}",
                   student=att.student, college=subject.department.college, request=request,
                   old_value=old_status, new_value=new_status)
            messages.success(request, f'Attendance corrected: {old_status} → {new_status}.')
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

    return render(request, 'attendance/correct_form.html', {
        'att': att, 'subject': subject,
        'status_choices': [('PRESENT', 'Present'), ('ABSENT', 'Absent'), ('LATE', 'Late')],
    })


# ── EXEMPTION MANAGEMENT ──────────────────────────────────────────────────────

@login_required
def student_exemption_apply(request):
    """Student submits an attendance exemption request."""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('dashboard')

    if request.method == 'POST':
        from_date = request.POST.get('from_date')
        to_date   = request.POST.get('to_date')
        reason_type = request.POST.get('reason_type', 'OTHER')
        reason = request.POST.get('reason', '').strip()
        doc = request.FILES.get('document')

        if not from_date or not to_date or not reason:
            messages.error(request, 'All fields are required.')
        else:
            AttendanceExemption.objects.create(
                student=student,
                from_date=from_date, to_date=to_date,
                reason_type=reason_type, reason=reason,
                document=doc,
            )
            messages.success(request, 'Exemption request submitted. Awaiting HOD approval.')
            return redirect('student_dashboard')

    my_exemptions = AttendanceExemption.objects.filter(student=student).order_by('-created_at')[:10]
    return render(request, 'attendance/exemption_form.html', {
        'exemption_types': AttendanceExemption.EXEMPTION_TYPE,
        'my_exemptions': my_exemptions,
    })


@login_required
def hod_exemptions(request):
    """HOD reviews and approves/rejects exemption requests for their department."""
    try:
        hod = HOD.objects.select_related('department').get(user=request.user)
    except HOD.DoesNotExist:
        return redirect('dashboard')

    exemptions = AttendanceExemption.objects.filter(
        student__department=hod.department
    ).select_related('student__user').order_by('-created_at')[:50]

    if request.method == 'POST':
        # Batch action
        batch_ids = request.POST.getlist('exemption_ids')
        action = request.POST.get('action')
        note = request.POST.get('review_note', '').strip()

        if batch_ids and action in ('APPROVED', 'REJECTED'):
            updated = AttendanceExemption.objects.filter(
                pk__in=batch_ids,
                student__department=hod.department,
                status='PENDING'
            ).update(status=action, reviewed_by=request.user, review_note=note)
            messages.success(request, f'{updated} exemption(s) {action.lower()}.')
        elif not batch_ids:
            # Single item (legacy)
            ex_id = request.POST.get('exemption_id')
            ex = get_object_or_404(AttendanceExemption, pk=ex_id, student__department=hod.department)
            if action in ('APPROVED', 'REJECTED'):
                ex.status = action
                ex.reviewed_by = request.user
                ex.review_note = note
                ex.save()
                messages.success(request, f'Exemption {action.lower()}.')
        return redirect('hod_exemptions')

    return render(request, 'attendance/hod_exemptions.html', {
        'exemptions': exemptions, 'hod': hod,
        'college': hod.department.college,
        'branding': _get_college_branding(hod.department.college),
    })


# ── HOD DEFAULTERS REPORT ─────────────────────────────────────────────────────

@login_required
def hod_defaulters_report(request):
    """Full defaulters list for the department with eligibility status per student."""
    try:
        hod = HOD.objects.select_related('department').get(user=request.user)
    except HOD.DoesNotExist:
        return redirect('dashboard')

    dept = hod.department
    college = dept.college
    semester_filter = _safe_int(request.GET.get('semester')) or None

    students_qs = Student.objects.filter(
        department=dept, status='ACTIVE'
    ).select_related('user').order_by('roll_number')

    if semester_filter:
        students_qs = students_qs.filter(current_semester=semester_filter)

    rows = []
    for student in students_qs:
        sem = semester_filter or student.current_semester
        elig = _compute_eligibility(student, sem, college)
        rows.append({
            'student': student,
            'overall_pct': elig['overall_pct'],
            'eligible': elig['eligible'],
            'reasons': elig['reasons'],
            'subject_fails': elig['subject_fails'],
            'rule': elig['rule'],
        })

    # Sort: ineligible first, then by overall_pct ascending
    rows.sort(key=lambda r: (r['eligible'], r['overall_pct'] or 0))

    semesters = Student.objects.filter(department=dept, status='ACTIVE').values_list('current_semester', flat=True).distinct().order_by('current_semester')

    return render(request, 'attendance/hod_defaulters.html', {
        'rows': rows, 'hod': hod, 'dept': dept,
        'college': college,
        'semester_filter': semester_filter,
        'semesters': semesters,
        'branding': _get_college_branding(college),
    })


# ── ELIGIBILITY OVERRIDE (EXAM CELL) ─────────────────────────────────────────

@login_required
def exam_eligibility_overrides(request, exam_id):
    """Exam cell views override requests and approves/rejects them."""
    ec = _exam_controller_guard(request)
    if not ec or not ec.can_manage_hall_tickets:
        return redirect('dashboard')

    exam = get_object_or_404(Exam, pk=exam_id, college=ec.college)
    overrides = EligibilityOverride.objects.filter(exam=exam).select_related(
        'student__user', 'student__department', 'requested_by', 'reviewed_by'
    ).order_by('-created_at')

    if request.method == 'POST':
        ov_id = request.POST.get('override_id')
        action = request.POST.get('action')
        note = request.POST.get('review_note', '').strip()
        ov = get_object_or_404(EligibilityOverride, pk=ov_id, exam=exam)
        if action in ('APPROVED', 'REJECTED'):
            ov.status = action
            ov.reviewed_by = request.user
            ov.review_note = note
            ov.save()
            # If approved, update the hall ticket
            if action == 'APPROVED':
                HallTicket.objects.filter(student=ov.student, exam=exam).update(
                    status='ISSUED', issued_at=timezone.now()
                )
            messages.success(request, f'Override {action.lower()} for {ov.student.roll_number}.')
        return redirect('exam_eligibility_overrides', exam_id=exam.pk)

    return render(request, 'attendance/exam_overrides.html', {
        'ec': ec, 'exam': exam, 'overrides': overrides,
        'branding': _get_college_branding(ec.college),
    })


@login_required
def student_request_override(request, exam_id):
    """Student requests an eligibility override for an exam."""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('dashboard')

    exam = get_object_or_404(Exam, pk=exam_id, college=student.department.college)

    if EligibilityOverride.objects.filter(student=student, exam=exam).exists():
        messages.warning(request, 'You have already submitted an override request for this exam.')
        return redirect('student_dashboard')

    elig = _compute_eligibility(student, exam.semester, student.department.college, exam=exam)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'Please provide a reason.')
        else:
            EligibilityOverride.objects.create(
                student=student, exam=exam,
                requested_by=request.user,
                reason=reason,
                attendance_pct_at_request=elig['overall_pct'] or 0,
            )
            messages.success(request, 'Override request submitted. The exam cell will review it.')
            return redirect('student_dashboard')

    return render(request, 'attendance/student_override_form.html', {
        'exam': exam, 'elig': elig,
    })


# ── SUBJECT DETAIL — ATTENDANCE CALENDAR ─────────────────────────────────────

@login_required
def subject_detail_view(request, subject_id):
    """
    Student views a full FullCalendar attendance calendar for a specific subject.
    Shows present/absent/late per day, month stats, timetable slot info.
    """
    import json
    from django.core.serializers.json import DjangoJSONEncoder

    try:
        student = Student.objects.select_related('department', 'user').get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Contact admin.')
        return redirect('home')

    subject = get_object_or_404(Subject, id=subject_id)

    # Faculty for this subject
    faculty_assignment = FacultySubject.objects.filter(subject=subject).select_related('faculty__user').first()
    faculty_name = None
    if faculty_assignment and faculty_assignment.faculty and faculty_assignment.faculty.user:
        faculty_name = faculty_assignment.faculty.user.get_full_name() or faculty_assignment.faculty.user.username

    # Attendance records for this student + subject
    records = Attendance.objects.filter(
        student=student,
        session__subject=subject
    ).select_related('session')

    attendance_by_date = {}
    for rec in records:
        if not rec.session or not rec.session.date:
            continue
        status = str(rec.status).upper()
        if status in ('PRESENT', 'TRUE', '1'):
            normalized = 'PRESENT'
        elif status == 'LATE':
            normalized = 'LATE'
        else:
            normalized = 'ABSENT'
        attendance_by_date[rec.session.date.strftime('%Y-%m-%d')] = normalized

    # Scheduled days from timetable
    scheduled_days = list(
        Timetable.objects.filter(subject=subject)
        .values_list('day_of_week', flat=True)
        .distinct()
    )

    # Timetable time slots per day
    timetable_map = {}
    for slot in Timetable.objects.filter(subject=subject).order_by('day_of_week', 'start_time'):
        label = f"{slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}"
        timetable_map.setdefault(slot.day_of_week, []).append(label)
    timetable_display = {k: ', '.join(v) for k, v in timetable_map.items()}

    today = timezone.localdate()

    # Sidebar badge helpers
    from datetime import timedelta as _td
    week_ago = timezone.now() - _td(days=7)
    new_assignments = Assignment.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
        deadline__gte=timezone.now(),
    ).exclude(assignmentsubmission__student=student).order_by('deadline')[:3]
    new_quizzes = Quiz.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
        is_active=True,
        created_at__gte=week_ago,
    ).select_related('subject').order_by('-created_at')[:3]

    # Last semester attendance for comparison
    last_semester = student.current_semester - 1 if student.current_semester > 1 else None
    last_sem_pct = None
    if last_semester:
        last_att = Attendance.objects.filter(
            student=student,
            session__subject__semester=last_semester,
        ).aggregate(total=Count('id'), present=Count('id', filter=Q(status='PRESENT')))
        if last_att['total']:
            last_sem_pct = round(last_att['present'] / last_att['total'] * 100, 1)

    context = {
        'subject': subject,
        'attendance_map_json': json.dumps(attendance_by_date, cls=DjangoJSONEncoder),
        'scheduled_days_json': json.dumps(scheduled_days, cls=DjangoJSONEncoder),
        'timetable_map_json': json.dumps(timetable_display, cls=DjangoJSONEncoder),
        'initial_month': today.month,
        'initial_year': today.year,
        'faculty_name': faculty_name,
        'student': student,
        'college': student.department.college,
        'last_semester': last_semester,
        'last_sem_pct': last_sem_pct,
        'notifications': Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:10],
        'new_assignments': new_assignments,
        'new_quizzes': new_quizzes,
        'branding': _get_college_branding(student.department.college),
    }
    return render(request, 'dashboards/subject_board.html', context)
