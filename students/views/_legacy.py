import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta, time as dt_time
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.db import DataError, IntegrityError, transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Q, Count, F, ExpressionWrapper, FloatField, Avg, OuterRef, Subquery, IntegerField, Value
from django.db.models.functions import TruncWeek, Cast, Coalesce
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse
from ..models import (
    UserRole, College, Student, Faculty, Department, HOD, Principal, Course,
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
    FacultyFeedbackCycle, FacultyFeedbackResponse,
    AttendanceRule, AttendanceExemption, AttendanceCorrection, EligibilityOverride,
    FeeBreakdown, SupplyExamRegistration, TimetableBreak,
    Regulation, CurriculumEntry, ElectivePool, ElectiveSelection,
    Section, SectionSubjectFacultyMap,
    AuditLog, FeeInstallmentPlan, FeeInstallment, LateFeeRule, FeeWaiver,
    GraceMarksRule, GraceMarksApplication,
    StudentRegulation, RegulationMigration, SubjectSchemeOverride, PromotionRule,
    ResultVersion, ResultFreeze, MarksModeration,
    ExamEligibilityConfig, StudentLifecycleEvent, DisciplinaryRecord,
    ElectiveWaitlist, CollegeFeatureConfig,
    SemesterResultBatch, SemesterResultStudent, SemesterResultSubject,
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


def _digits_only(value):
    return ''.join(ch for ch in str(value or '') if ch.isdigit())


def _safe_decimal(value, default=Decimal('0')):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _valid_academic_year(value):
    raw = (value or '').strip()
    if not raw:
        return True
    if len(raw) != 7 or raw[4] != '-':
        return False
    start, end = raw[:4], raw[5:]
    if not (start.isdigit() and end.isdigit()):
        return False
    return int(end) == (int(start) + 1) % 100


def _paginate_queryset(request, queryset, per_page=25, page_param='page'):
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get(page_param) or 1)
    return page_obj


def _validate_staff_admin_payload(request, departments, *, is_hod=False, existing_user=None, existing_staff=None):
    errors = []
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    employee_id = request.POST.get('employee_id', '').strip()
    dept_id = request.POST.get('department', '').strip()
    phone = request.POST.get('phone_number', '').strip()
    experience = _safe_int(request.POST.get('experience_years'))
    joined_date_str = request.POST.get('joined_date', '').strip()

    if not first_name:
        errors.append('First name is required.')
    if not last_name:
        errors.append('Last name is required.')
    if not username:
        errors.append('Username is required.')
    if not dept_id:
        errors.append('Department is required.')
    elif not departments.filter(pk=dept_id).exists():
        errors.append('Select a valid department.')

    if email:
        try:
            validate_email(email)
        except ValidationError:
            errors.append('Enter a valid email address.')
        else:
            dup_users = User.objects.exclude(pk=getattr(existing_user, 'pk', None)).filter(email__iexact=email)
            if dup_users.exists():
                errors.append('Email already exists for another user.')
    else:
        errors.append('Email is required.')

    dup_username = User.objects.exclude(pk=getattr(existing_user, 'pk', None)).filter(username=username)
    if dup_username.exists():
        errors.append('Username already taken.')

    if employee_id:
        model_cls = HOD if is_hod else Faculty
        dup_emp = model_cls.objects.exclude(pk=getattr(existing_staff, 'pk', None)).filter(employee_id=employee_id)
        if dup_emp.exists():
            errors.append('Employee ID already exists.')
    else:
        errors.append('Employee ID is required.')

    digits = _digits_only(phone)
    if len(digits) != 10:
        errors.append('Phone number must be exactly 10 digits.')

    if experience < 0 or experience > 60:
        errors.append('Experience years must be between 0 and 60.')

    if joined_date_str:
        try:
            joined_date = datetime.fromisoformat(joined_date_str).date()
            if joined_date > timezone.localdate():
                errors.append('Joined date cannot be in the future.')
        except (ValueError, TypeError):
            errors.append('Enter a valid joined date.')

    return errors


def _validate_fee_payload(total_amount, paid_amount, semester, academic_year):
    errors = []
    if total_amount <= 0:
        errors.append('Total fee must be greater than zero.')
    if paid_amount < 0:
        errors.append('Paid amount cannot be negative.')
    if paid_amount > total_amount:
        errors.append('Paid amount cannot exceed total amount.')
    if semester is not None and not (1 <= semester <= 8):
        errors.append('Semester must be between 1 and 8.')
    if academic_year and not _valid_academic_year(academic_year):
        errors.append('Academic year must be in the format YYYY-YY, for example 2026-27.')
    return errors


def _validate_exam_payload(name, semester, start_date_raw, end_date_raw, college=None, exam_pk=None):
    errors = []
    start_date = end_date = None
    if not name:
        errors.append('Exam name is required.')
    if semester < 1 or semester > 8:
        errors.append('Semester must be between 1 and 8.')
    try:
        start_date = datetime.fromisoformat(start_date_raw).date()
        end_date = datetime.fromisoformat(end_date_raw).date()
    except (ValueError, TypeError):
        errors.append('Enter valid exam start and end dates.')
    if start_date and end_date and end_date < start_date:
        errors.append('End date cannot be earlier than start date.')
    if college and name and start_date and end_date:
        dup = Exam.objects.filter(
            college=college,
            name__iexact=name,
            semester=semester,
            start_date=start_date,
            end_date=end_date,
        )
        if exam_pk:
            dup = dup.exclude(pk=exam_pk)
        if dup.exists():
            errors.append('An exam with the same name, semester, and date range already exists.')
    return errors, start_date, end_date


def _enterprise_summary(total_count, page_obj):
    return {
        'total': total_count,
        'page_size': page_obj.paginator.per_page,
        'current_page': page_obj.number,
        'total_pages': page_obj.paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    }


def _validate_student_admin_payload(request, student):
    errors = []
    current_year = timezone.localdate().year

    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    email = request.POST.get('email', '').strip()
    college_email = request.POST.get('college_email', '').strip()
    personal_email = request.POST.get('personal_email', '').strip()
    phone_number = request.POST.get('phone_number', '').strip()
    alternate_phone = request.POST.get('alternate_phone', '').strip()
    parent_phone = request.POST.get('parent_phone_number', '').strip()
    parent_email = request.POST.get('parent_email', '').strip()
    emergency_phone = request.POST.get('emergency_phone_number', '').strip()
    aadhaar_number = request.POST.get('aadhaar_number', '').strip()
    pincode = request.POST.get('pincode', '').strip()
    admission_year = _safe_int(request.POST.get('admission_year'))
    current_semester = _safe_int(request.POST.get('current_semester'))
    entry_semester = _safe_int(request.POST.get('entry_semester'))
    inter_passed_year_raw = request.POST.get('inter_passed_year', '').strip()
    school_passed_year_raw = request.POST.get('school_passed_year', '').strip()
    inter_passed_year = _safe_int(inter_passed_year_raw) if inter_passed_year_raw else None
    school_passed_year = _safe_int(school_passed_year_raw) if school_passed_year_raw else None
    inter_percentage_raw = request.POST.get('inter_percentage', '').strip()
    school_percentage_raw = request.POST.get('school_percentage', '').strip()
    inter_percentage = _safe_float(inter_percentage_raw) if inter_percentage_raw else None
    school_percentage = _safe_float(school_percentage_raw) if school_percentage_raw else None
    dob_raw = request.POST.get('date_of_birth', '').strip()
    department_id = request.POST.get('department', '').strip()

    if not first_name:
        errors.append('First name is required.')
    if not last_name:
        errors.append('Last name is required.')
    if not department_id:
        errors.append('Department is required.')

    if not email:
        errors.append('Primary email is required.')
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors.append('Enter a valid primary email address.')
        if User.objects.exclude(pk=student.user_id).filter(email__iexact=email).exists():
            errors.append('Primary email already exists for another user.')

    for label, value in (
        ('College email', college_email),
        ('Personal email', personal_email),
        ('Parent email', parent_email),
    ):
        if value:
            try:
                validate_email(value)
            except ValidationError:
                errors.append(f'Enter a valid {label.lower()}.')

    for label, value, required in (
        ('Phone number', phone_number, True),
        ('Alternate phone', alternate_phone, False),
        ('Parent phone', parent_phone, False),
        ('Emergency phone', emergency_phone, False),
    ):
        digits = _digits_only(value)
        if required and not digits:
            errors.append(f'{label} is required.')
        elif digits and len(digits) != 10:
            errors.append(f'{label} must be exactly 10 digits.')

    if aadhaar_number:
        aadhaar_digits = _digits_only(aadhaar_number)
        if len(aadhaar_digits) != 12:
            errors.append('Aadhaar number must be exactly 12 digits.')
        elif StudentProfile.objects.exclude(user=student.user).filter(aadhaar_number=aadhaar_digits).exists():
            errors.append('Aadhaar number already exists for another student.')

    if pincode:
        pincode_digits = _digits_only(pincode)
        if len(pincode_digits) != 6:
            errors.append('Pincode must be exactly 6 digits.')

    if admission_year < 2000 or admission_year > current_year + 1:
        errors.append('Admission year is out of range.')
    if current_semester < 1 or current_semester > 8:
        errors.append('Current semester must be between 1 and 8.')
    if entry_semester < 1 or entry_semester > 8:
        errors.append('Entry semester must be between 1 and 8.')
    if entry_semester > current_semester:
        errors.append('Entry semester cannot be greater than current semester.')

    if dob_raw:
        try:
            dob = datetime.strptime(dob_raw, '%Y-%m-%d').date()
            if dob > timezone.localdate():
                errors.append('Date of birth cannot be in the future.')
        except ValueError:
            errors.append('Enter a valid date of birth.')

    for label, year_value in (
        ('Intermediate passed year', inter_passed_year),
        ('School passed year', school_passed_year),
    ):
        if year_value is not None and (year_value < 1980 or year_value > current_year):
            errors.append(f'{label} is out of range.')

    for label, percentage in (
        ('Intermediate percentage', inter_percentage),
        ('School percentage', school_percentage),
    ):
        if percentage is not None and (percentage < 0 or percentage > 100):
            errors.append(f'{label} must be between 0 and 100.')

    return errors

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
    Two allowed windows:
      1. During class: slot.start_time → slot.end_time + 10 min grace
      2. Evening edit: 17:00 → 20:00 (5 pm – 8 pm) for any assigned subject
    """
    role = getattr(user, 'userrole', None)
    if not role: return False, "No role assigned."
    if user.is_superuser: return True, ""

    # HOD override
    if role.role == 2 and hasattr(user, 'hod') and user.hod.department == subject.department:
        return True, ""

    if role.role in (2, 3) and hasattr(user, 'faculty'):
        is_assigned = FacultySubject.objects.filter(faculty=user.faculty, subject=subject).exists()

        now = timezone.localtime(timezone.now())
        today_day = {0:'MON',1:'TUE',2:'WED',3:'THU',4:'FRI',5:'SAT',6:'SUN'}.get(now.weekday())
        if not slot:
            slot = Timetable.objects.filter(subject=subject, day_of_week=today_day).first()

        is_sub = False
        if slot:
            is_sub = Substitution.objects.filter(
                timetable_slot=slot, substitute_faculty=user.faculty,
                date=now.date(), status='ACCEPTED',
            ).exists()

        if not (is_assigned or is_sub):
            return False, "You are not assigned to this subject."

        import os
        if os.environ.get('ATTENDANCE_TIME_LOCK_DISABLED') == '1':
            return True, ""

        current_time = now.time()

        # Window 1: during class + 10 min grace
        if slot:
            end_dt = timezone.make_aware(datetime.combine(now.date(), slot.end_time))
            marking_end = (end_dt + timedelta(minutes=10)).time()
            if slot.start_time <= current_time <= marking_end:
                return True, ""

        # Window 2: evening edit — 5 pm to 8 pm
        from datetime import time as dt_time
        if dt_time(17, 0) <= current_time <= dt_time(20, 0):
            return True, "Evening window: editable 5 PM – 8 PM."

        # Build a helpful error message
        if slot:
            return False, f"Attendance locked. Allowed: during class ({slot.start_time}–{slot.end_time} +10 min) or 5 PM–8 PM."
        return False, "Attendance locked. Allowed: during class (+10 min grace) or 5 PM–8 PM."

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


ADMIN_DASHBOARD_STUDENT_LIMIT = 100
ADMIN_DASHBOARD_FACULTY_LIMIT = 80
ADMIN_DASHBOARD_FEE_LIMIT = 100
ADMIN_DASHBOARD_ANNOUNCEMENT_LIMIT = 30
ADMIN_DASHBOARD_INVITE_LIMIT = 30
ADMIN_DASHBOARD_REQUEST_LIMIT = 50
ADMIN_DASHBOARD_HELPDESK_LIMIT = 50
ADMIN_DASHBOARD_EXAM_LIMIT = 40
ADMIN_DASHBOARD_HOD_LIMIT = 50
SUPER_ADMIN_COLLEGE_LIMIT = 60
SUPER_ADMIN_COLLEGE_ADMIN_LIMIT = 80
SUPER_ADMIN_IMPERSONATION_LIMIT = 40


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


def _build_weekly_timetable_matrix(entries, breaks=None, days=None, merge_sections=False):
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

    if merge_sections:
        for cell in slot_map.values():
            cell['entries'] = _merge_timetable_section_rows(cell['entries'])

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


def _merge_timetable_section_rows(entries):
    """Collapse same faculty/subject/time rows for multiple sections into one display item."""
    grouped = {}
    for entry in entries:
        group_key = (
            entry.subject_id,
            entry.faculty_id,
            entry.day_of_week,
            entry.start_time,
            entry.end_time,
        )
        if group_key not in grouped:
            entry.display_sections = []
            entry.display_room_numbers = []
            grouped[group_key] = entry
        merged_entry = grouped[group_key]
        if entry.section and entry.section not in merged_entry.display_sections:
            merged_entry.display_sections.append(entry.section)
        if entry.classroom and entry.classroom.room_number not in merged_entry.display_room_numbers:
            merged_entry.display_room_numbers.append(entry.classroom.room_number)
    return list(grouped.values())


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


def _student_academic_year(student, semester=None):
    semester = semester or student.current_semester or 1
    year_offset = max((semester - 1) // 2, 0)
    start_year = (student.admission_year or timezone.now().year) + year_offset
    return f"{start_year}-{str(start_year + 1)[-2:]}"


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

    approved_transcripts = (
        SemesterResultStudent.objects.filter(
            student=student,
            status='APPROVED',
            batch__status='APPROVED',
        )
        .select_related('batch')
        .prefetch_related('subjects__subject')
        .order_by('-batch__semester', '-approved_at', '-id')
    )
    transcript_by_semester = {}
    for transcript in approved_transcripts:
        transcript_by_semester.setdefault(transcript.batch.semester, transcript)

    # Build breakdown: one entry per semester that has Result, Marks, or an approved transcript
    result_by_sem = {r.semester: r for r in results}
    all_semesters = sorted(set(
        list(result_by_sem.keys()) +
        list(marks_by_semester.keys()) +
        list(transcript_by_semester.keys())
    ))

    breakdown = []
    for semester in all_semesters:
        result = result_by_sem.get(semester)
        transcript = transcript_by_semester.get(semester)
        sem_marks = list(transcript.subjects.all()) if transcript else marks_by_semester.get(semester, [])
        breakdown.append({
            'result': result,
            'semester': semester,
            'marks': sem_marks,
            'transcript': transcript,
        })

    return breakdown, results


def _semester_result_redirect_url(academic_year, department_id, semester):
    return (
        reverse('admin_semester_results') +
        f'?academic_year={academic_year}&department={department_id}&semester={semester}'
    )


def _dedupe_semester_result_batches(batch_qs):
    seen = set()
    deduped = []
    for batch in batch_qs.order_by('-uploaded_at', '-id'):
        key = (batch.college_id, batch.department_id, batch.academic_year, batch.semester)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(batch)
    return deduped


def _build_active_backlog_groups(student):
    result_breakdown, _results = _student_result_breakdown(student)
    backlog_subjects = set()
    passed_subjects = set()
    best_failed_by_subject = {}

    for item in result_breakdown:
        semester = item.get('semester')
        for mark in item.get('marks', []):
            subject = getattr(mark, 'subject', None)
            subject_id = getattr(mark, 'subject_id', None) or getattr(subject, 'id', None)
            max_marks = getattr(mark, 'max_marks', 0) or 0
            if not subject_id or max_marks <= 0:
                continue

            passing = max_marks * 0.4
            is_failed = getattr(mark, 'grade', '') == 'F' or mark.marks_obtained < passing
            if is_failed:
                backlog_subjects.add(subject_id)
                existing = best_failed_by_subject.get(subject_id)
                if existing is None or mark.marks_obtained > existing['mark'].marks_obtained:
                    best_failed_by_subject[subject_id] = {'semester': semester, 'mark': mark}
            else:
                passed_subjects.add(subject_id)

    active_backlogs = backlog_subjects - passed_subjects
    failed_by_semester = {}
    for subject_id, row in best_failed_by_subject.items():
        if subject_id not in active_backlogs:
            continue
        failed_by_semester.setdefault(row['semester'], []).append(row['mark'])

    supply_backlog_grouped = [(sem, failed_by_semester[sem]) for sem in sorted(failed_by_semester.keys())]
    all_failed_marks = [mark for _sem, marks in supply_backlog_grouped for mark in marks]
    failed_subject_ids = {getattr(mark, 'subject_id', None) or mark.subject.id for mark in all_failed_marks}
    return {
        'result_breakdown': result_breakdown,
        'active_backlogs': active_backlogs,
        'backlog_count': len(active_backlogs),
        'supply_backlog_grouped': supply_backlog_grouped,
        'all_failed_marks': all_failed_marks,
        'failed_subject_ids': failed_subject_ids,
    }


def _scope_helpdesk_tickets(request):
    college = _get_admin_college(request)
    qs = HelpDeskTicket.objects.select_related('college', 'submitted_by').order_by('-created_at')
    if request.user.is_superuser or college is None:
        return qs
    return qs.filter(Q(college=college) | Q(college__isnull=True))


def _auto_generate_timetable(department, semester):
    """
    Real-college timetable generator — section-aware, L-T-P-C aware, conflict-free.

    Returns a dict: {'created': int, 'skipped_subjects': [Subject], 'no_availability': [Faculty]}
    """
    from datetime import time as dt_time

    subjects = list(Subject.objects.filter(department=department, semester=semester).order_by('name'))
    if not subjects:
        return {'created': 0, 'skipped_subjects': [], 'no_availability': []}

    mapping_qs = (
        SectionSubjectFacultyMap.objects
        .filter(section__department=department, section__semester=semester, subject__in=subjects)
        .select_related('section', 'subject', 'faculty__user', 'classroom')
        .order_by('subject__name', 'section__label')
    )
    rows_by_subject = defaultdict(list)
    for mapping in mapping_qs:
        rows_by_subject[mapping.subject_id].append({
            'faculty': mapping.faculty,
            'section': mapping.section.label,
            'classroom': mapping.classroom,
        })

    if not rows_by_subject:
        assignments_qs = (
            FacultySubject.objects
            .filter(subject__in=subjects)
            .select_related('faculty__user', 'subject')
            .order_by('subject__name', 'faculty__user__first_name')
        )
        fallback_counts = defaultdict(int)
        fallback_totals = defaultdict(int)
        for fa in assignments_qs:
            fallback_totals[fa.subject_id] += 1
        for fa in assignments_qs:
            idx = fallback_counts[fa.subject_id]
            fallback_counts[fa.subject_id] += 1
            rows_by_subject[fa.subject_id].append({
                'faculty': fa.faculty,
                'section': chr(65 + idx) if fallback_totals[fa.subject_id] > 1 else '',
                'classroom': None,
            })

    if not rows_by_subject:
        return {'created': 0, 'skipped_subjects': subjects, 'no_availability': []}

    # Separate lecture rooms and lab rooms for room-type matching (Fix 4)
    all_classrooms = list(Classroom.objects.filter(college=department.college).order_by('room_number'))
    if not all_classrooms:
        all_classrooms = [Classroom.objects.create(
            college=department.college, room_number=f"{department.code}-101", capacity=60
        )]
    lab_rooms = [r for r in all_classrooms if r.room_type == 'lab']
    lecture_rooms = [r for r in all_classrooms if r.room_type != 'lab'] or all_classrooms

    all_faculty_ids = list({row['faculty'].id for rows in rows_by_subject.values() for row in rows})
    avail_qs = FacultyAvailability.objects.filter(
        faculty_id__in=all_faculty_ids, is_available=True
    ).order_by('day_of_week', 'start_time')
    avail_map = {}
    for av in avail_qs:
        avail_map.setdefault(av.faculty_id, []).append((av.day_of_week, av.start_time, av.end_time))

    # Track faculty with no availability set (Fix 3)
    no_availability_faculty = []
    for fac_id in all_faculty_ids:
        if fac_id not in avail_map:
            try:
                fac = Faculty.objects.select_related('user').get(pk=fac_id)
                no_availability_faculty.append(fac)
            except Faculty.DoesNotExist:
                pass

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

    Timetable.objects.filter(subject__department=department, subject__semester=semester).delete()

    used_faculty: set = set()
    used_rooms: set   = set()

    existing = Timetable.objects.filter(
        subject__department__college=department.college
    ).exclude(
        subject__department=department, subject__semester=semester
    ).values_list('faculty_id', 'classroom_id', 'day_of_week', 'start_time')
    for fac_id, room_id, day, start in existing:
        used_faculty.add((fac_id, day, start))
        used_rooms.add((room_id, day, start))

    created_count = 0
    skipped_subjects = []

    for subj in subjects:
        subject_rows = rows_by_subject.get(subj.id, [])
        if not subject_rows:
            skipped_subjects.append(subj)  # Fix 6 — track skipped
            continue

        L = max(subj.lecture_hours, 1)
        T = subj.tutorial_hours
        P = subj.practical_hours

        # Fix 4 — pick room pool based on subject type
        is_lab_subject = P > 0 or subj.slot_type == 'lab'
        preferred_lab_rooms = lab_rooms if (is_lab_subject and lab_rooms) else all_classrooms
        preferred_lecture_rooms = lecture_rooms

        for sec_idx, row in enumerate(subject_rows):
            faculty = row['faculty']
            section = row['section']
            default_room = row['classroom']
            fac_avail = avail_map.get(faculty.id)
            lecture_candidates = fac_avail if fac_avail else LECTURE_GRID
            lectures_placed = 0
            room_idx = sec_idx
            lecture_room_pool = ([default_room] + [r for r in preferred_lecture_rooms if r.id != default_room.id]) if default_room else preferred_lecture_rooms
            lab_room_pool = ([default_room] + [r for r in preferred_lab_rooms if r.id != default_room.id]) if default_room else preferred_lab_rooms

            for day, start, end in lecture_candidates:
                if lectures_placed >= L:
                    break
                fkey = (faculty.id, day, start)
                if fkey in used_faculty:
                    continue
                room = None
                for ri in range(len(lecture_room_pool)):
                    candidate = lecture_room_pool[(room_idx + ri) % len(lecture_room_pool)]
                    if (candidate.id, day, start) not in used_rooms:
                        room = candidate
                        break
                if not room:
                    continue
                Timetable.objects.create(
                    subject=subj, faculty=faculty,
                    day_of_week=day, start_time=start, end_time=end,
                    classroom=room, section=section, generation_mode='balanced',
                )
                used_faculty.add(fkey)
                used_rooms.add((room.id, day, start))
                lectures_placed += 1
                created_count += 1

            if T > 0:
                for day, start, end in (fac_avail or LECTURE_GRID):
                    fkey = (faculty.id, day, start)
                    if fkey in used_faculty:
                        continue
                    room = None
                    for ri in range(len(lecture_room_pool)):
                        candidate = lecture_room_pool[(room_idx + ri) % len(lecture_room_pool)]
                        if (candidate.id, day, start) not in used_rooms:
                            room = candidate
                            break
                    if not room:
                        continue
                    Timetable.objects.create(
                        subject=subj, faculty=faculty,
                        day_of_week=day, start_time=start, end_time=end,
                        classroom=room, section=section, generation_mode='balanced',
                    )
                    used_faculty.add(fkey)
                    used_rooms.add((room.id, day, start))
                    created_count += 1
                    break

            if P > 0:
                for _day, _s1, _e1, _s2, _e2 in LAB_PAIRS:
                    fkey1 = (faculty.id, _day, _s1)
                    fkey2 = (faculty.id, _day, _s2)
                    if fkey1 in used_faculty or fkey2 in used_faculty:
                        continue
                    # Fix 4 — prefer lab rooms for practical slots
                    room = None
                    for ri in range(len(lab_room_pool)):
                        candidate = lab_room_pool[(room_idx + ri) % len(lab_room_pool)]
                        if (candidate.id, _day, _s1) not in used_rooms and (candidate.id, _day, _s2) not in used_rooms:
                            room = candidate
                            break
                    if not room:
                        continue
                    for _s, _e in [(_s1, _e1), (_s2, _e2)]:
                        Timetable.objects.create(
                            subject=subj, faculty=faculty,
                            day_of_week=_day, start_time=_s, end_time=_e,
                            classroom=room, section=section, generation_mode='balanced',
                        )
                        used_faculty.add((faculty.id, _day, _s))
                        used_rooms.add((room.id, _day, _s))
                        created_count += 1
                    break

    return {'created': created_count, 'skipped_subjects': skipped_subjects, 'no_availability': no_availability_faculty}


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


def _effective_dashboard_name(user):
    if user.is_superuser:
        return 'super_admin_dashboard'
    try:
        role = user.userrole.role
    except Exception:
        role = None
    role_map = {
        1: 'admin_dashboard',
        2: 'hod_dashboard',
        3: 'faculty_dashboard',
        4: 'student_dashboard',
        5: 'lab_staff_dashboard',
        6: 'principal_dashboard',
        7: 'exam_dashboard',
    }
    if role in role_map:
        return role_map[role]
    if hasattr(user, 'principal'):
        return 'principal_dashboard'
    if hasattr(user, 'hod'):
        return 'hod_dashboard'
    if hasattr(user, 'faculty'):
        return 'faculty_dashboard'
    if hasattr(user, 'student'):
        return 'student_dashboard'
    return 'dashboard'


def _set_session_role_cache_for_user(request, user):
    role_obj = UserRole.objects.select_related('college').filter(user=user).first()
    if role_obj:
        request.session['_user_role'] = role_obj.role
        request.session['_user_college_id'] = role_obj.college_id
        return
    request.session['_user_role'] = None
    if hasattr(user, 'principal'):
        request.session['_user_college_id'] = user.principal.college_id
    elif hasattr(user, 'hod'):
        request.session['_user_college_id'] = user.hod.department.college_id
    elif hasattr(user, 'faculty'):
        request.session['_user_college_id'] = user.faculty.department.college_id
    elif hasattr(user, 'student'):
        request.session['_user_college_id'] = user.student.department.college_id
    elif hasattr(user, 'examcontroller'):
        request.session['_user_college_id'] = user.examcontroller.college_id
    else:
        request.session['_user_college_id'] = None


def _clear_impersonation_session(request):
    for key in (
        '_impersonator_user_id',
        '_impersonator_name',
        '_impersonated_target_label',
        '_impersonated_role_label',
    ):
        request.session.pop(key, None)


def _scope_departments(request, queryset=None):
    queryset = queryset or Department.objects.all()
    college = _get_admin_college(request)
    queryset = queryset.filter(is_deleted=False)
    if request.user.is_superuser or college is None:
        return queryset
    return queryset.filter(college=college)


def _generate_unique_faculty_employee_id(target_department, preferred_id=''):
    employee_id = (preferred_id or '').strip()
    if employee_id and not Faculty.objects.filter(employee_id=employee_id).exists():
        return employee_id

    employee_id = _generate_faculty_id(target_department)
    if not Faculty.objects.filter(employee_id=employee_id).exists():
        return employee_id

    base_id = employee_id[:42]
    counter = 2
    while Faculty.objects.filter(employee_id=f'{base_id}-{counter}').exists():
        counter += 1
    return f'{base_id}-{counter}'


def _archive_department(dept):
    dept.is_deleted = True
    dept.code = f'DEL{dept.pk}'
    dept.name = f'{dept.name} (Deleted)'
    dept.save(update_fields=['is_deleted', 'code', 'name'])


def _transfer_department_records(request, source_dept, target_dept):
    subject_conflicts = list(
        Subject.objects.filter(department=source_dept, code__in=Subject.objects.filter(department=target_dept).values('code'))
        .values_list('code', flat=True)
    )
    if subject_conflicts:
        raise ValueError(
            'Cannot transfer because the target department already has subject code(s): ' +
            ', '.join(sorted(set(subject_conflicts))) + '.'
        )

    section_conflicts = [
        f'Sem {semester} Section {label}'
        for semester, label in Section.objects.filter(department=source_dept).values_list('semester', 'label')
        if Section.objects.filter(department=target_dept, semester=semester, label=label).exists()
    ]
    if section_conflicts:
        raise ValueError(
            'Cannot transfer because the target department already has section(s): ' +
            ', '.join(section_conflicts) + '.'
        )

    with transaction.atomic():
        Student.objects.filter(department=source_dept, is_deleted=False).update(department=target_dept)
        Faculty.objects.filter(department=source_dept, is_deleted=False).update(department=target_dept)

        for hod in HOD.objects.filter(department=source_dept).select_related('user'):
            faculty_defaults = {
                'employee_id': _generate_unique_faculty_employee_id(target_dept, hod.employee_id),
                'department': target_dept,
                'designation': 'Professor' if 'head' in (hod.designation or '').lower() else (hod.designation or 'Professor'),
                'qualification': hod.qualification,
                'experience_years': hod.experience_years,
                'phone_number': hod.phone_number,
                'joined_date': hod.joined_date or timezone.localdate(),
            }
            faculty, created = Faculty.objects.get_or_create(
                user=hod.user,
                defaults=faculty_defaults,
            )
            if not created:
                faculty.department = target_dept
                faculty.is_deleted = False
                faculty.designation = faculty.designation or faculty_defaults['designation']
                faculty.qualification = faculty.qualification or hod.qualification
                faculty.experience_years = max(faculty.experience_years or 0, hod.experience_years or 0)
                faculty.phone_number = faculty.phone_number or hod.phone_number
                faculty.save()
            UserRole.objects.filter(user=hod.user, role=2).update(role=3, college=target_dept.college)
            hod.delete()

        Subject.objects.filter(department=source_dept).update(department=target_dept)
        Course.objects.filter(department=source_dept).update(department=target_dept)
        Section.objects.filter(department=source_dept).update(department=target_dept)

        HODApproval.objects.filter(department=source_dept).update(department=target_dept)
        TimetableBreak.objects.filter(department=source_dept).update(department=target_dept)
        PromotionRule.objects.filter(department=source_dept).update(department=target_dept)
        FeeStructure.objects.filter(department=source_dept).update(department=target_dept)
        EvaluationScheme.objects.filter(department=source_dept).update(department=target_dept)
        AttendanceRule.objects.filter(department=source_dept).update(department=target_dept)
        FacultyFeedbackCycle.objects.filter(department=source_dept).update(department=target_dept)
        SemesterResultBatch.objects.filter(department=source_dept).update(department=target_dept)

        _archive_department(source_dept)

    return {
        'students': Student.objects.filter(department=target_dept, is_deleted=False).count(),
    }


def _scope_announcements_for_college(college, target=None):
    """Return announcements scoped to a college, optionally filtered by target audience.
    target: 'students', 'faculty', or None (returns all/everyone notices only)
    """
    qs = Announcement.objects.filter(Q(college=college) | Q(college__isnull=True)) if college else Announcement.objects.all()
    if target == 'students':
        qs = qs.filter(Q(target='all') | Q(target='students'))
    elif target == 'faculty':
        qs = qs.filter(Q(target='all') | Q(target='faculty'))
    return qs


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
    Results are cached in Django's cache for 5 minutes to avoid repeated DB hits.
    """
    from django.core.cache import cache
    cache_key = f'att_rule_{college.pk}_{getattr(department,"pk","x")}_{semester or "x"}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    qs = AttendanceRule.objects.filter(college=college, is_active=True)

    # Most specific: dept + semester
    if department and semester:
        rule = qs.filter(department=department, semester=semester).first()
        if rule:
            cache.set(cache_key, rule, 300)
            return rule

    # Dept-level (any semester)
    if department:
        rule = qs.filter(department=department, semester__isnull=True).first()
        if rule:
            cache.set(cache_key, rule, 300)
            return rule

    # College-wide fallback
    rule = qs.filter(department__isnull=True, semester__isnull=True).first()
    if rule:
        cache.set(cache_key, rule, 300)
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
    cache.set(cache_key, default, 300)
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
        response = redirect("dashboard")
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response

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
            response = redirect(next_url)
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            return response
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
    resp = render(request, "auth/login.html", {'captcha_q': captcha_q})
    resp['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp


def logout_view(request):
    if request.user.is_authenticated:
        ActivityLog.objects.create(user=request.user, action="User logged out", ip_address=get_client_ip(request))
    logout(request)
    return redirect("home")


import random
import time
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.contrib.auth import authenticate, login


def _generate_captcha(request):
    a, b = random.randint(1, 9), random.randint(1, 9)
    request.session['sa_captcha_answer'] = a + b
    request.session['sa_captcha_q'] = f"{a} + {b}"
    return request.session['sa_captcha_q']


def super_admin_login_view(request):
    """Dedicated login for super admins."""

    # Block authenticated non-superusers
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("super_admin_dashboard")
        return HttpResponseForbidden("Access denied.")

    # Ensure captcha exists
    captcha_q = request.session.get('sa_captcha_q') or _generate_captcha(request)

    if request.method == "POST":
        # Validate captcha
        try:
            captcha_valid = int(request.POST.get("captcha", "").strip()) == request.session.get('sa_captcha_answer')
        except (ValueError, TypeError):
            captcha_valid = False

        if not captcha_valid:
            messages.error(request, "Incorrect answer. Please try again.")
            captcha_q = _generate_captcha(request)
            return render(request, "auth/superadmin_login.html", {'captcha_q': captcha_q})

        # Authenticate user
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user and user.is_superuser:
            login(request, user)

            # Session tracking
            request.session['_last_activity'] = time.time()

            # Security updates
            security = _get_or_create_security(user)
            ip = get_client_ip(request)

            security.login_attempts = 0
            security.last_login_ip = ip
            security.save(update_fields=["login_attempts", "last_login_ip"])

            ActivityLog.objects.create(
                user=user,
                action="Super admin logged in",
                ip_address=ip
            )

            return redirect("super_admin_dashboard")

        # Invalid credentials
        messages.error(request, "Invalid credentials.")
        captcha_q = _generate_captcha(request)

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
    target_dashboard = _effective_dashboard_name(user)
    if target_dashboard == 'dashboard':
        messages.warning(request, "Your account has no role assigned. Contact admin.")
        logout(request)
        return redirect("login")
    return redirect(target_dashboard)


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
        'notifications': Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:20],
        'role_name': 'Lab Technician',
        'branding': _get_college_branding(college),
    }
    return render(request, 'dashboards/lab_staff.html', context)


@login_required
@super_admin_required
def super_admin_dashboard(request):
    colleges_base = College.objects.order_by('name')
    department_count_sq = Department.objects.filter(
        college=OuterRef('pk'),
        is_deleted=False,
    ).values('college').annotate(total=Count('pk')).values('total')[:1]
    admin_count_sq = UserRole.objects.filter(
        college=OuterRef('pk'),
        role=1,
    ).values('college').annotate(total=Count('pk')).values('total')[:1]
    student_count_sq = Student.objects.filter(
        department__college=OuterRef('pk'),
        is_deleted=False,
    ).values('department__college').annotate(total=Count('pk')).values('total')[:1]
    faculty_count_sq = Faculty.objects.filter(
        department__college=OuterRef('pk'),
        is_deleted=False,
    ).values('department__college').annotate(total=Count('pk')).values('total')[:1]

    colleges = colleges_base.annotate(
        department_count=Coalesce(Subquery(department_count_sq, output_field=IntegerField()), Value(0)),
        admin_count=Coalesce(Subquery(admin_count_sq, output_field=IntegerField()), Value(0)),
        student_count=Coalesce(Subquery(student_count_sq, output_field=IntegerField()), Value(0)),
        faculty_count=Coalesce(Subquery(faculty_count_sq, output_field=IntegerField()), Value(0)),
    ).only('id', 'name', 'code', 'city', 'is_active')[:SUPER_ADMIN_COLLEGE_LIMIT]

    college_admins = UserRole.objects.filter(role=1).select_related('user', 'college').only(
        'id',
        'user__id',
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'college__id',
        'college__name',
    ).order_by('college__name', 'user__username')[:SUPER_ADMIN_COLLEGE_ADMIN_LIMIT]
    platform_announcements = Announcement.objects.filter(college__isnull=True).select_related('created_by').order_by('-created_at')[:5]

    # Activity log: only super-admin actions, NOT college user activity
    recent_activity = ActivityLog.objects.filter(
        user__is_superuser=True
    ).select_related('user').order_by('-timestamp')[:15]

    total_colleges = colleges_base.count()
    total_college_admins = UserRole.objects.filter(role=1).count()
    total_principals = Principal.objects.count()
    total_exam_controllers = ExamController.objects.count()
    total_users = User.objects.count()
    total_students = Student.objects.filter(is_deleted=False).count()
    total_faculty = Faculty.objects.filter(is_deleted=False).count()
    total_departments = Department.objects.filter(is_deleted=False).count()

    impersonation_college_filter = request.GET.get('imp_college', '').strip()
    impersonation_department_filter = request.GET.get('imp_department', '').strip()
    impersonation_search = request.GET.get('imp_search', '').strip()
    impersonation_semester_filter = request.GET.get('imp_semester', '').strip()
    impersonation_show_all = request.GET.get('imp_show_all', '').strip() == '1'
    impersonation_colleges = colleges_base.only('id', 'name')
    impersonation_departments = Department.objects.filter(is_deleted=False).select_related('college').only(
        'id',
        'name',
        'code',
        'college__id',
        'college__name',
    ).order_by('college__name', 'name')

    college_admin_targets = UserRole.objects.filter(role=1).select_related('user', 'college').only(
        'id',
        'user__id',
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'college__id',
        'college__name',
    )
    principal_targets = Principal.objects.select_related('user', 'college').only(
        'id',
        'employee_id',
        'user__id',
        'user__username',
        'user__first_name',
        'user__last_name',
        'college__id',
        'college__name',
    )
    hod_targets = HOD.objects.select_related('user', 'department__college').only(
        'id',
        'employee_id',
        'user__id',
        'user__username',
        'user__first_name',
        'user__last_name',
        'department__id',
        'department__name',
        'department__code',
        'department__college__id',
        'department__college__name',
    )
    faculty_targets = Faculty.objects.filter(is_deleted=False).select_related('user', 'department__college').only(
        'id',
        'employee_id',
        'designation',
        'user__id',
        'user__username',
        'user__first_name',
        'user__last_name',
        'department__id',
        'department__name',
        'department__code',
        'department__college__id',
        'department__college__name',
    )
    student_targets = Student.objects.filter(is_deleted=False).select_related('user', 'department__college').only(
        'id',
        'roll_number',
        'current_semester',
        'section',
        'user__id',
        'user__username',
        'user__first_name',
        'user__last_name',
        'department__id',
        'department__name',
        'department__code',
        'department__college__id',
        'department__college__name',
    )
    exam_controller_targets = ExamController.objects.select_related('user', 'college').only(
        'id',
        'employee_id',
        'designation',
        'user__id',
        'user__username',
        'user__first_name',
        'user__last_name',
        'college__id',
        'college__name',
    )

    if impersonation_college_filter:
        college_admin_targets = college_admin_targets.filter(college_id=impersonation_college_filter)
        principal_targets = principal_targets.filter(college_id=impersonation_college_filter)
        hod_targets = hod_targets.filter(department__college_id=impersonation_college_filter)
        faculty_targets = faculty_targets.filter(department__college_id=impersonation_college_filter)
        student_targets = student_targets.filter(department__college_id=impersonation_college_filter)
        exam_controller_targets = exam_controller_targets.filter(college_id=impersonation_college_filter)
        impersonation_departments = impersonation_departments.filter(college_id=impersonation_college_filter)

    if impersonation_department_filter:
        hod_targets = hod_targets.filter(department_id=impersonation_department_filter)
        faculty_targets = faculty_targets.filter(department_id=impersonation_department_filter)
        student_targets = student_targets.filter(department_id=impersonation_department_filter)

    if impersonation_semester_filter:
        student_targets = student_targets.filter(current_semester=impersonation_semester_filter)

    if impersonation_search:
        college_admin_targets = college_admin_targets.filter(
            Q(user__username__icontains=impersonation_search) |
            Q(user__first_name__icontains=impersonation_search) |
            Q(user__last_name__icontains=impersonation_search) |
            Q(user__email__icontains=impersonation_search) |
            Q(college__name__icontains=impersonation_search) |
            Q(college__code__icontains=impersonation_search)
        )
        principal_targets = principal_targets.filter(
            Q(user__username__icontains=impersonation_search) |
            Q(user__first_name__icontains=impersonation_search) |
            Q(user__last_name__icontains=impersonation_search) |
            Q(employee_id__icontains=impersonation_search) |
            Q(college__name__icontains=impersonation_search) |
            Q(college__code__icontains=impersonation_search)
        )
        hod_targets = hod_targets.filter(
            Q(user__username__icontains=impersonation_search) |
            Q(user__first_name__icontains=impersonation_search) |
            Q(user__last_name__icontains=impersonation_search) |
            Q(employee_id__icontains=impersonation_search) |
            Q(department__name__icontains=impersonation_search) |
            Q(department__code__icontains=impersonation_search) |
            Q(department__college__name__icontains=impersonation_search)
        )
        faculty_targets = faculty_targets.filter(
            Q(user__username__icontains=impersonation_search) |
            Q(user__first_name__icontains=impersonation_search) |
            Q(user__last_name__icontains=impersonation_search) |
            Q(employee_id__icontains=impersonation_search) |
            Q(designation__icontains=impersonation_search) |
            Q(department__name__icontains=impersonation_search) |
            Q(department__code__icontains=impersonation_search) |
            Q(department__college__name__icontains=impersonation_search)
        )
        student_targets = student_targets.filter(
            Q(user__username__icontains=impersonation_search) |
            Q(user__first_name__icontains=impersonation_search) |
            Q(user__last_name__icontains=impersonation_search) |
            Q(roll_number__icontains=impersonation_search) |
            Q(section__icontains=impersonation_search) |
            Q(department__name__icontains=impersonation_search) |
            Q(department__code__icontains=impersonation_search) |
            Q(department__college__name__icontains=impersonation_search)
        )
        exam_controller_targets = exam_controller_targets.filter(
            Q(user__username__icontains=impersonation_search) |
            Q(user__first_name__icontains=impersonation_search) |
            Q(user__last_name__icontains=impersonation_search) |
            Q(employee_id__icontains=impersonation_search) |
            Q(designation__icontains=impersonation_search) |
            Q(college__name__icontains=impersonation_search) |
            Q(college__code__icontains=impersonation_search)
        )

    impersonation_admin_total = college_admin_targets.count()
    impersonation_principal_total = principal_targets.count()
    impersonation_hod_total = hod_targets.count()
    impersonation_faculty_total = faculty_targets.count()
    impersonation_student_total = student_targets.count()
    impersonation_exam_controller_total = exam_controller_targets.count()

    college_admin_targets = college_admin_targets.order_by('college__name', 'user__username')
    principal_targets = principal_targets.order_by('college__name', 'user__username')
    hod_targets = hod_targets.order_by('department__college__name', 'department__name', 'user__username')
    faculty_targets = faculty_targets.order_by('department__college__name', 'department__name', 'user__username')
    student_targets = student_targets.order_by('department__college__name', 'department__name', 'roll_number')
    exam_controller_targets = exam_controller_targets.order_by('college__name', 'user__username')

    if not impersonation_show_all:
        college_admin_targets = college_admin_targets[:SUPER_ADMIN_IMPERSONATION_LIMIT]
        principal_targets = principal_targets[:SUPER_ADMIN_IMPERSONATION_LIMIT]
        hod_targets = hod_targets[:SUPER_ADMIN_IMPERSONATION_LIMIT]
        faculty_targets = faculty_targets[:SUPER_ADMIN_IMPERSONATION_LIMIT]
        student_targets = student_targets[:SUPER_ADMIN_IMPERSONATION_LIMIT]
        exam_controller_targets = exam_controller_targets[:SUPER_ADMIN_IMPERSONATION_LIMIT]

    context = {
        'colleges': colleges,
        'college_admins': college_admins,
        'principals': Principal.objects.select_related('user', 'college').order_by('college__name', 'user__username')[:SUPER_ADMIN_COLLEGE_ADMIN_LIMIT],
        'exam_controllers': ExamController.objects.select_related('user', 'college').order_by('college__name', 'user__username')[:SUPER_ADMIN_COLLEGE_ADMIN_LIMIT],
        'recent_activity': recent_activity,
        'platform_announcements': platform_announcements,
        'total_colleges': total_colleges,
        'total_college_admins': total_college_admins,
        'total_principals': total_principals,
        'total_exam_controllers': total_exam_controllers,
        # Platform-level counts only — no breakdown by college
        'total_users': total_users,
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_departments': total_departments,
        'colleges_preview_limited': total_colleges > SUPER_ADMIN_COLLEGE_LIMIT,
        'college_admins_preview_limited': total_college_admins > SUPER_ADMIN_COLLEGE_ADMIN_LIMIT,
        'principals_preview_limited': total_principals > SUPER_ADMIN_COLLEGE_ADMIN_LIMIT,
        'exam_controllers_preview_limited': total_exam_controllers > SUPER_ADMIN_COLLEGE_ADMIN_LIMIT,
        'colleges_preview_limit': SUPER_ADMIN_COLLEGE_LIMIT,
        'college_admins_preview_limit': SUPER_ADMIN_COLLEGE_ADMIN_LIMIT,
        'impersonation_colleges': impersonation_colleges,
        'impersonation_departments': impersonation_departments,
        'impersonation_college_filter': impersonation_college_filter,
        'impersonation_department_filter': impersonation_department_filter,
        'impersonation_search': impersonation_search,
        'impersonation_semester_filter': impersonation_semester_filter,
        'impersonation_show_all': impersonation_show_all,
        'impersonation_limit': SUPER_ADMIN_IMPERSONATION_LIMIT,
        'impersonation_admin_total': impersonation_admin_total,
        'impersonation_principal_total': impersonation_principal_total,
        'impersonation_hod_total': impersonation_hod_total,
        'impersonation_faculty_total': impersonation_faculty_total,
        'impersonation_student_total': impersonation_student_total,
        'impersonation_exam_controller_total': impersonation_exam_controller_total,
        'impersonation_admin_targets': college_admin_targets,
        'impersonation_principal_targets': principal_targets,
        'impersonation_hod_targets': hod_targets,
        'impersonation_faculty_targets': faculty_targets,
        'impersonation_student_targets': student_targets,
        'impersonation_exam_controller_targets': exam_controller_targets,
    }
    return render(request, 'dashboards/super_admin.html', context)


@login_required
@super_admin_required
def super_admin_impersonate_start(request, target_type, target_id):
    if request.method != 'POST':
        return redirect('super_admin_dashboard')

    if request.session.get('_impersonator_user_id'):
        messages.warning(request, 'Stop the current impersonation before starting a new one.')
        return redirect('super_admin_dashboard')

    target_map = {
        'college-admin': (
            UserRole.objects.select_related('user', 'college').filter(role=1),
            lambda obj: obj.user,
            lambda obj: f'College Admin {obj.user.get_full_name() or obj.user.username} ({obj.college.name})',
            lambda obj: 'College Admin',
        ),
        'principal': (
            Principal.objects.select_related('user', 'college').all(),
            lambda obj: obj.user,
            lambda obj: f'Principal {obj.user.get_full_name() or obj.user.username} ({obj.college.name})',
            lambda obj: 'Principal',
        ),
        'hod': (
            HOD.objects.select_related('user', 'department__college').all(),
            lambda obj: obj.user,
            lambda obj: f'HOD {obj.user.get_full_name() or obj.user.username} ({obj.department.code})',
            lambda obj: 'HOD',
        ),
        'faculty': (
            Faculty.objects.select_related('user', 'department__college').filter(is_deleted=False),
            lambda obj: obj.user,
            lambda obj: f'Faculty {obj.user.get_full_name() or obj.user.username} ({obj.department.code})',
            lambda obj: 'Faculty',
        ),
        'student': (
            Student.objects.select_related('user', 'department__college').filter(is_deleted=False),
            lambda obj: obj.user,
            lambda obj: f'Student {obj.roll_number} ({obj.department.code})',
            lambda obj: 'Student',
        ),
        'exam-controller': (
            ExamController.objects.select_related('user', 'college').all(),
            lambda obj: obj.user,
            lambda obj: f'Exam Controller {obj.user.get_full_name() or obj.user.username} ({obj.college.name})',
            lambda obj: 'Exam Controller',
        ),
    }

    config = target_map.get(target_type)
    if not config:
        messages.error(request, 'Invalid impersonation target.')
        return redirect('super_admin_dashboard')

    queryset, user_getter, label_getter, role_label_getter = config
    target_obj = get_object_or_404(queryset, pk=target_id)
    target_user = user_getter(target_obj)
    if target_user.is_superuser:
        messages.error(request, 'Super admins cannot be impersonated.')
        return redirect('super_admin_dashboard')

    impersonator = request.user
    target_user.backend = settings.AUTHENTICATION_BACKENDS[0]
    login(request, target_user)
    request.session['_impersonator_user_id'] = impersonator.pk
    request.session['_impersonator_name'] = impersonator.get_full_name() or impersonator.username
    request.session['_impersonated_target_label'] = label_getter(target_obj)
    request.session['_impersonated_role_label'] = role_label_getter(target_obj)
    _set_session_role_cache_for_user(request, target_user)
    request.session['_last_activity'] = time.time()

    ActivityLog.objects.create(
        user=impersonator,
        action=f"Started impersonation as {request.session['_impersonated_target_label']}",
        ip_address=get_client_ip(request),
    )
    messages.success(request, f"Now impersonating {request.session['_impersonated_target_label']}.")
    return redirect(_effective_dashboard_name(target_user))


@login_required
def super_admin_impersonate_stop(request):
    impersonator_id = request.session.get('_impersonator_user_id')
    if not impersonator_id:
        return redirect('dashboard')

    impersonated_user = request.user
    impersonator = User.objects.filter(pk=impersonator_id, is_superuser=True).first()
    if not impersonator:
        _clear_impersonation_session(request)
        logout(request)
        messages.error(request, 'Original super admin session could not be restored. Please sign in again.')
        return redirect('super_admin_login')

    impersonator.backend = settings.AUTHENTICATION_BACKENDS[0]
    login(request, impersonator)
    _clear_impersonation_session(request)
    _set_session_role_cache_for_user(request, impersonator)
    request.session['_last_activity'] = time.time()

    ActivityLog.objects.create(
        user=impersonator,
        action=f"Stopped impersonation and returned from {impersonated_user.get_full_name() or impersonated_user.username}",
        ip_address=get_client_ip(request),
    )
    messages.info(request, 'Returned to your super admin account.')
    return redirect('super_admin_dashboard')


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
def super_admin_principal_add(request):
    selected_college_id = request.GET.get('college', '').strip() or request.POST.get('college', '').strip()
    colleges = College.objects.order_by('name')
    colleges_without_principal = colleges.exclude(principal__isnull=False)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        employee_id = request.POST.get('employee_id', '').strip().upper()
        phone_number = request.POST.get('phone_number', '').strip()
        qualification = request.POST.get('qualification', '').strip()
        experience_years = request.POST.get('experience_years', '').strip()
        college_id = request.POST.get('college', '').strip()

        if not college_id:
            messages.error(request, 'Select a college for the principal.')
        elif not employee_id or not phone_number or not qualification or not experience_years:
            messages.error(request, 'Employee ID, phone number, qualification, and experience are required.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif email and User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
        elif Principal.objects.filter(employee_id=employee_id).exists():
            messages.error(request, 'A principal with this employee ID already exists.')
        else:
            college = get_object_or_404(College, pk=college_id)
            if hasattr(college, 'principal'):
                messages.error(request, f'{college.name} already has a principal. Edit or remove that principal first.')
            else:
                password_value, password_generated = _resolve_password(password)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password_value,
                    first_name=first_name,
                    last_name=last_name,
                )
                UserRole.objects.create(user=user, role=6, college=college)
                Principal.objects.create(
                    user=user,
                    college=college,
                    employee_id=employee_id,
                    phone_number=phone_number,
                    qualification=qualification,
                    experience_years=int(experience_years or 0),
                )
                ActivityLog.objects.create(
                    user=request.user,
                    action=f'Created principal {user.username} for {college.name}',
                    ip_address=get_client_ip(request),
                )
                if password_generated:
                    messages.success(request, f'Principal created successfully. Temporary password: {password_value}')
                else:
                    messages.success(request, 'Principal created successfully.')
                return redirect('super_admin_dashboard')

    return render(request, 'super_admin/principal_form.html', {
        'colleges': colleges_without_principal if not selected_college_id else colleges,
        'selected_college_id': selected_college_id,
        'mode': 'add',
    })


@login_required
@super_admin_required
def super_admin_principal_edit(request, pk):
    principal = get_object_or_404(Principal.objects.select_related('user', 'college'), pk=pk)
    if request.method == 'POST':
        principal.user.first_name = request.POST.get('first_name', principal.user.first_name).strip()
        principal.user.last_name = request.POST.get('last_name', principal.user.last_name).strip()
        new_email = request.POST.get('email', principal.user.email).strip()
        new_username = request.POST.get('username', principal.user.username).strip()
        employee_id = request.POST.get('employee_id', principal.employee_id).strip().upper()
        phone_number = request.POST.get('phone_number', principal.phone_number).strip()
        qualification = request.POST.get('qualification', principal.qualification).strip()
        experience_years = request.POST.get('experience_years', principal.experience_years)
        new_password = request.POST.get('password', '').strip()

        if User.objects.exclude(pk=principal.user_id).filter(username=new_username).exists():
            messages.error(request, 'Username already exists.')
        elif new_email and User.objects.exclude(pk=principal.user_id).filter(email=new_email).exists():
            messages.error(request, 'A user with this email already exists.')
        elif Principal.objects.exclude(pk=principal.pk).filter(employee_id=employee_id).exists():
            messages.error(request, 'A principal with this employee ID already exists.')
        else:
            principal.user.username = new_username
            principal.user.email = new_email
            if new_password:
                principal.user.set_password(new_password)
            principal.user.save()
            principal.employee_id = employee_id
            principal.phone_number = phone_number
            principal.qualification = qualification
            principal.experience_years = int(experience_years or 0)
            principal.save()
            ActivityLog.objects.create(
                user=request.user,
                action=f'Updated principal {principal.user.username} for {principal.college.name}',
                ip_address=get_client_ip(request),
            )
            messages.success(request, 'Principal updated successfully.')
            return redirect('super_admin_dashboard')

    return render(request, 'super_admin/principal_form.html', {
        'principal': principal,
        'colleges': College.objects.filter(pk=principal.college_id),
        'selected_college_id': str(principal.college_id),
        'mode': 'edit',
    })


@login_required
@super_admin_required
def super_admin_principal_delete(request, pk):
    principal = get_object_or_404(Principal.objects.select_related('user', 'college'), pk=pk)
    if request.method == 'POST':
        username = principal.user.username
        college_name = principal.college.name
        user = principal.user
        UserRole.objects.filter(user=user, role=6).delete()
        principal.delete()
        user.delete()
        ActivityLog.objects.create(
            user=request.user,
            action=f'Removed principal {username} from {college_name}',
            ip_address=get_client_ip(request),
        )
        messages.success(request, 'Principal account removed.')
    return redirect('super_admin_dashboard')


@login_required
@super_admin_required
def super_admin_exam_controller_add(request):
    selected_college_id = request.GET.get('college', '').strip() or request.POST.get('college', '').strip()
    colleges = College.objects.order_by('name')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        employee_id = request.POST.get('employee_id', '').strip().upper()
        phone_number = request.POST.get('phone_number', '').strip()
        designation = request.POST.get('designation', 'Exam Controller').strip() or 'Exam Controller'
        college_id = request.POST.get('college', '').strip()

        if not college_id:
            messages.error(request, 'Select a college for the exam controller.')
        elif not first_name or not last_name or not username or not employee_id:
            messages.error(request, 'First name, last name, username, and employee ID are required.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif email and User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
        elif ExamController.objects.filter(employee_id=employee_id).exists():
            messages.error(request, 'An exam controller with this employee ID already exists.')
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
            UserRole.objects.create(user=user, role=7, college=college)
            ExamController.objects.create(
                user=user,
                college=college,
                employee_id=employee_id,
                phone_number=phone_number,
                designation=designation,
            )
            ActivityLog.objects.create(
                user=request.user,
                action=f'Created exam controller {user.username} for {college.name}',
                ip_address=get_client_ip(request),
            )
            if password_generated:
                messages.success(request, f'Exam controller created successfully. Temporary password: {password_value}')
            else:
                messages.success(request, 'Exam controller created successfully.')
            return redirect('super_admin_dashboard')

    return render(request, 'super_admin/exam_controller_form.html', {
        'colleges': colleges,
        'selected_college_id': selected_college_id,
        'mode': 'add',
    })


@login_required
@super_admin_required
def super_admin_exam_controller_edit(request, pk):
    exam_controller = get_object_or_404(ExamController.objects.select_related('user', 'college'), pk=pk)
    if request.method == 'POST':
        exam_controller.user.first_name = request.POST.get('first_name', exam_controller.user.first_name).strip()
        exam_controller.user.last_name = request.POST.get('last_name', exam_controller.user.last_name).strip()
        new_email = request.POST.get('email', exam_controller.user.email).strip()
        new_username = request.POST.get('username', exam_controller.user.username).strip()
        employee_id = request.POST.get('employee_id', exam_controller.employee_id).strip().upper()
        phone_number = request.POST.get('phone_number', exam_controller.phone_number).strip()
        designation = request.POST.get('designation', exam_controller.designation).strip() or 'Exam Controller'
        new_password = request.POST.get('password', '').strip()

        if User.objects.exclude(pk=exam_controller.user_id).filter(username=new_username).exists():
            messages.error(request, 'Username already exists.')
        elif new_email and User.objects.exclude(pk=exam_controller.user_id).filter(email=new_email).exists():
            messages.error(request, 'A user with this email already exists.')
        elif ExamController.objects.exclude(pk=exam_controller.pk).filter(employee_id=employee_id).exists():
            messages.error(request, 'An exam controller with this employee ID already exists.')
        else:
            exam_controller.user.username = new_username
            exam_controller.user.email = new_email
            if new_password:
                exam_controller.user.set_password(new_password)
            exam_controller.user.save()
            exam_controller.employee_id = employee_id
            exam_controller.phone_number = phone_number
            exam_controller.designation = designation
            exam_controller.save()
            ActivityLog.objects.create(
                user=request.user,
                action=f'Updated exam controller {exam_controller.user.username} for {exam_controller.college.name}',
                ip_address=get_client_ip(request),
            )
            messages.success(request, 'Exam controller updated successfully.')
            return redirect('super_admin_dashboard')

    return render(request, 'super_admin/exam_controller_form.html', {
        'exam_controller': exam_controller,
        'colleges': College.objects.filter(pk=exam_controller.college_id),
        'selected_college_id': str(exam_controller.college_id),
        'mode': 'edit',
    })


@login_required
@super_admin_required
def super_admin_exam_controller_delete(request, pk):
    exam_controller = get_object_or_404(ExamController.objects.select_related('user', 'college'), pk=pk)
    if request.method == 'POST':
        username = exam_controller.user.username
        college_name = exam_controller.college.name
        user = exam_controller.user
        UserRole.objects.filter(user=user, role=7).delete()
        exam_controller.delete()
        user.delete()
        ActivityLog.objects.create(
            user=request.user,
            action=f'Removed exam controller {username} from {college_name}',
            ip_address=get_client_ip(request),
        )
        messages.success(request, 'Exam controller account removed.')
    return redirect('super_admin_dashboard')


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
    principal = Principal.objects.select_related('user').filter(college=college).first()
    exam_controllers = ExamController.objects.select_related('user').filter(college=college).order_by('user__username')
    return render(request, 'super_admin/college_detail.html', {
        'college': college,
        'departments': departments,
        'admins': admins,
        'principal': principal,
        'exam_controllers': exam_controllers,
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
    student_qs = Student.objects.filter(department__in=department_qs)
    faculty_qs = Faculty.objects.filter(department__in=department_qs)
    hod_qs = HOD.objects.filter(department__in=department_qs)
    fee_qs = Fee.objects.filter(student__department__in=department_qs)
    announcement_qs = _scope_announcements_for_college(college).select_related("created_by")
    request_qs = RegistrationRequest.objects.filter(college=college).select_related('desired_department').order_by('-created_at')
    invite_qs = RegistrationInvite.objects.filter(college=college).order_by('-created_at')
    helpdesk_qs = HelpDeskTicket.objects.filter(Q(college=college) | Q(college__isnull=True)).order_by('-created_at')
    exams_qs = _scope_exams(request).select_related('created_by').order_by('-start_date', '-id')

    # System Health Dashboard Metrics
    metrics_cache_key = f"admin_dashboard_metrics:{college.pk if college else 'global'}"
    metrics = cache.get(metrics_cache_key)
    now_local = timezone.localtime(timezone.now())

    if metrics is None:
        active_users_count = User.objects.filter(
            last_login__gte=now_local - timedelta(hours=24),
            userrole__college=college
        ).count()

        total_students = student_qs.count()
        total_faculty = faculty_qs.count()
        total_departments = department_qs.count()
        total_hods = hod_qs.count()
        total_fees = fee_qs.count()
        pending_fees = fee_qs.filter(Q(status="PENDING") | Q(status="PARTIAL")).count()
        total_collected = fee_qs.aggregate(s=Sum("paid_amount"))["s"] or 0
        total_pending_agg = fee_qs.exclude(status="PAID").aggregate(
            pending=Sum(F('total_amount') - F('paid_amount'))
        )
        total_pending = total_pending_agg['pending'] or 0
        fee_paid_count = fee_qs.filter(status="PAID").count()
        fee_partial_count = fee_qs.filter(status="PARTIAL").count()
        pending_requests = request_qs.filter(
            status__in=['SUBMITTED', 'UNDER_REVIEW', 'NEEDS_CORRECTION', 'APPROVED']
        ).count()
        active_invites = invite_qs.filter(used_at__isnull=True).count()
        open_helpdesk_tickets = helpdesk_qs.exclude(status='RESOLVED').count()
        exams_without_schedule = exams_qs.exclude(
            pk__in=ExamSchedule.objects.values_list('exam_id', flat=True)
        ).count()
        today = now_local.date()
        upcoming_count = exams_qs.filter(start_date__gt=today).count()
        ongoing_count = exams_qs.filter(start_date__lte=today, end_date__gte=today).count()
        completed_count = exams_qs.filter(end_date__lt=today).count()

        metrics = {
            "active_users_count": active_users_count,
            "total_students": total_students,
            "total_faculty": total_faculty,
            "total_departments": total_departments,
            "total_hods": total_hods,
            "total_fees": total_fees,
            "pending_fees": pending_fees,
            "total_collected": total_collected,
            "total_pending": total_pending,
            "fee_paid_count": fee_paid_count,
            "fee_partial_count": fee_partial_count,
            "pending_requests": pending_requests,
            "active_invites": active_invites,
            "open_helpdesk_tickets": open_helpdesk_tickets,
            "exams_without_schedule": exams_without_schedule,
            "upcoming_count": upcoming_count,
            "ongoing_count": ongoing_count,
            "completed_count": completed_count,
        }
        cache.set(metrics_cache_key, metrics, 60)

    # Attendance Completion Rate: (Marked Sessions Today / Scheduled Slots Today)
    today_day = {0:'MON',1:'TUE',2:'WED',3:'THU',4:'FRI',5:'SAT',6:'SUN'}.get(now_local.weekday())
    scheduled_today = Timetable.objects.filter(subject__department__college=college, day_of_week=today_day).count()
    marked_today = AttendanceSession.objects.filter(subject__department__college=college, date=now_local.date()).count()
    attendance_rate = round((marked_today / scheduled_today * 100), 1) if scheduled_today > 0 else 100.0

    total_students = metrics["total_students"]
    total_faculty = metrics["total_faculty"]
    total_departments = metrics["total_departments"]
    total_hods = metrics["total_hods"]
    total_fees = metrics["total_fees"]
    pending_fees = metrics["pending_fees"]
    total_collected = metrics["total_collected"]
    total_pending = metrics["total_pending"]
    fee_paid_count = metrics["fee_paid_count"]
    fee_partial_count = metrics["fee_partial_count"]
    recent_students = student_qs.select_related("user", "department").order_by("-created_at")[:5]
    recent_announcements = announcement_qs.order_by("-created_at")[:5]
    recent_requests = request_qs[:5]
    recent_helpdesk_tickets = helpdesk_qs[:10]
    departments = department_qs

    student_year_filter = request.GET.get("year", "").strip()
    student_dept_filter = request.GET.get("dept", "").strip()
    student_sem_filter = request.GET.get("sem", "").strip()
    student_filter_qs = student_qs
    if student_year_filter:
        student_filter_qs = student_filter_qs.filter(admission_year=student_year_filter)
    if student_dept_filter:
        student_filter_qs = student_filter_qs.filter(department_id=student_dept_filter)
    if student_sem_filter:
        student_filter_qs = student_filter_qs.filter(current_semester=student_sem_filter)

    student_year_options = list(
        student_qs.order_by("-admission_year").values_list("admission_year", flat=True).distinct()
    )
    filtered_students = student_filter_qs.order_by("department__code", "admission_year", "current_semester", "roll_number")
    filtered_students_total = filtered_students.count()
    filtered_students = filtered_students.select_related("user", "department")[:ADMIN_DASHBOARD_STUDENT_LIMIT]

    fee_academic_year_filter = request.GET.get("fee_year", "").strip()
    fee_dept_filter = request.GET.get("fee_dept", "").strip()
    fee_sem_filter = request.GET.get("fee_sem", "").strip()
    fee_status_filter = request.GET.get("fee_status", "").strip()
    fee_filter_qs = fee_qs
    if fee_academic_year_filter:
        fee_filter_qs = fee_filter_qs.filter(academic_year=fee_academic_year_filter)
    if fee_dept_filter:
        fee_filter_qs = fee_filter_qs.filter(student__department_id=fee_dept_filter)
    if fee_sem_filter:
        fee_filter_qs = fee_filter_qs.filter(semester=fee_sem_filter)
    if fee_status_filter:
        fee_filter_qs = fee_filter_qs.filter(status=fee_status_filter)
    fee_year_options = list(
        fee_qs.exclude(academic_year='').order_by('-academic_year').values_list('academic_year', flat=True).distinct()
    )
    filtered_fees = fee_filter_qs.annotate(
        balance=ExpressionWrapper(F('total_amount') - F('paid_amount'), output_field=FloatField())
    ).order_by('status', 'student__roll_number')
    filtered_fees_total = filtered_fees.count()
    filtered_fees = filtered_fees.select_related('student__user', 'student__department')[:ADMIN_DASHBOARD_FEE_LIMIT]

    faculty_preview = faculty_qs.select_related('user', 'department').order_by('department__name', 'user__first_name')[:ADMIN_DASHBOARD_FACULTY_LIMIT]
    hod_preview = hod_qs.filter(is_active=True).select_related('user', 'department').order_by('department__name')[:ADMIN_DASHBOARD_HOD_LIMIT]
    helpdesk_preview = helpdesk_qs[:ADMIN_DASHBOARD_HELPDESK_LIMIT]
    announcement_preview = announcement_qs.order_by('-created_at')[:ADMIN_DASHBOARD_ANNOUNCEMENT_LIMIT]
    invite_preview = invite_qs.order_by('-created_at')[:ADMIN_DASHBOARD_INVITE_LIMIT]
    request_preview = request_qs.select_related('desired_department').order_by('-created_at')[:ADMIN_DASHBOARD_REQUEST_LIMIT]
    exams_total = exams_qs.count()
    exams_preview = exams_qs[:ADMIN_DASHBOARD_EXAM_LIMIT]
    all_departments = department_qs.annotate(
        student_count=Count('student', distinct=True),
        faculty_count=Count('faculty', distinct=True),
        subject_count=Count('subject', distinct=True),
    ).order_by('name')

    context = {
        "total_students": total_students, "total_faculty": total_faculty,
        "total_departments": total_departments, "total_hods": total_hods,
        "pending_fees": pending_fees, "recent_students": recent_students,
        "recent_announcements": recent_announcements, "departments": departments,
        "fee_summary": {"total_collected": total_collected, "total_pending": total_pending},
        "pending_requests": metrics["pending_requests"],
        "recent_requests": recent_requests,
        "recent_helpdesk_tickets": recent_helpdesk_tickets,
        "active_invites": metrics["active_invites"],
        "open_helpdesk_tickets": metrics["open_helpdesk_tickets"],
        "active_users_24h": metrics["active_users_count"],
        "attendance_completion_rate": attendance_rate,
        "college": college,
        "branding": _get_college_branding(college),
        "exams_without_schedule": metrics["exams_without_schedule"],
        "all_helpdesk_tickets": helpdesk_preview,
        "exams": exams_preview,
        "exam_total_count": exams_total,
        "exam_preview_limited": exams_total > ADMIN_DASHBOARD_EXAM_LIMIT,
        "upcoming_count": metrics["upcoming_count"],
        "ongoing_count": metrics["ongoing_count"],
        "completed_count": metrics["completed_count"],
        "all_departments": all_departments,
        "all_students_full": filtered_students,
        "all_students_total": total_students,
        "all_students_filtered_total": filtered_students_total,
        "student_year_filter": student_year_filter,
        "student_dept_filter": student_dept_filter,
        "student_sem_filter": student_sem_filter,
        "student_year_options": student_year_options,
        "all_faculty_full": faculty_preview,
        "all_faculty_total": total_faculty,
        "all_hods_full": hod_preview,
        "all_fees": filtered_fees,
        "all_fees_total": total_fees,
        "all_fees_filtered_total": filtered_fees_total,
        "fee_paid_count": fee_paid_count,
        "fee_partial_count": fee_partial_count,
        "fee_academic_year_filter": fee_academic_year_filter,
        "fee_dept_filter": fee_dept_filter,
        "fee_sem_filter": fee_sem_filter,
        "fee_status_filter": fee_status_filter,
        "fee_year_options": fee_year_options,
        "all_announcements": announcement_preview,
        "all_invites": invite_preview,
        "all_requests": request_preview,
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
    faculty_qs = Faculty.objects.filter(department__college=college).select_related("user", "department")
    students_qs = Student.objects.filter(department__college=college).select_related("user", "department")
    hod_qs = HOD.objects.filter(department__college=college).select_related("user", "department")
    faculty_list = faculty_qs[:100]
    students_list = students_qs[:100]
    hod_list = hod_qs[:50]
    total_faculty_count = faculty_qs.count()
    total_students_count = students_qs.count()
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
    sem_distribution = students_qs.values('current_semester').annotate(
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
        "notifications": Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:20],
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

    # Build semester → section → students grouped structure for HOD students pane
    all_active_students = Student.objects.filter(
        department=dept, status='ACTIVE', is_deleted=False
    ).select_related('user').order_by('current_semester', 'section', 'roll_number')

    from collections import OrderedDict
    _sem_sec_map = OrderedDict()
    for s in all_active_students:
        sem = s.current_semester
        sec = s.section.strip() if s.section and s.section.strip() else None
        _sem_sec_map.setdefault(sem, OrderedDict()).setdefault(sec, []).append(s)

    students_by_sem_section = []
    for sem, sec_map in _sem_sec_map.items():
        # If only one key and it's None → no sections assigned, flat list
        has_sections = not (len(sec_map) == 1 and None in sec_map)
        sections = []
        for sec_label, stu_list in sec_map.items():
            sections.append({
                'label': sec_label or '',
                'students': stu_list,
                'count': len(stu_list),
            })
        students_by_sem_section.append({
            'semester': sem,
            'sections': sections,
            'has_sections': has_sections,
            'total': sum(len(v) for v in sec_map.values()),
        })
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
    announcements  = _scope_announcements_for_college(dept.college, target='faculty').order_by('-created_at')[:20]

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

    # ── Smart Alerts ─────────────────────────────────────────────────────────
    today_local = timezone.localdate()
    smart_alerts = []

    # Alert: pending approvals
    pending_total = pending_approvals.count() + pending_leaves.count()
    if pending_total > 0:
        smart_alerts.append({
            'type': 'warning',
            'icon': 'fa-check-circle',
            'msg': f'{pending_total} approval{"s" if pending_total > 1 else ""} waiting for your review',
            'link': '#approvals',
            'link_label': 'Review',
        })

    # Alert: faculty who have timetable today but haven't marked attendance
    today_slots = Timetable.objects.filter(
        subject__department=dept, day_of_week=today_day
    ).select_related('faculty__user', 'subject').distinct()
    marked_today = set(AttendanceSession.objects.filter(
        subject__department=dept, date=today_local
    ).values_list('faculty_id', flat=True))
    absent_faculty = []
    for slot in today_slots:
        if slot.faculty_id not in marked_today:
            absent_faculty.append(slot.faculty.user.get_full_name() or slot.faculty.user.username)
    absent_faculty = list(dict.fromkeys(absent_faculty))  # dedupe
    if absent_faculty:
        names = ', '.join(absent_faculty[:3]) + (f' +{len(absent_faculty)-3} more' if len(absent_faculty) > 3 else '')
        smart_alerts.append({
            'type': 'danger',
            'icon': 'fa-user-slash',
            'msg': f'Classes not marked today: {names}',
            'link': '#timetable',
            'link_label': 'View',
        })

    # Alert: subjects with high defaulter count
    high_defaulter_subjects = [sa for sa in subject_attendance if sa['defaulters'] > 0]
    if high_defaulter_subjects:
        total_def = sum(sa['defaulters'] for sa in high_defaulter_subjects)
        smart_alerts.append({
            'type': 'warning',
            'icon': 'fa-user-graduate',
            'msg': f'{total_def} student{"s" if total_def > 1 else ""} below attendance threshold across {len(high_defaulter_subjects)} subject{"s" if len(high_defaulter_subjects) > 1 else ""}',
            'link': '#attendance',
            'link_label': 'View',
        })

    # ── Faculty Performance ───────────────────────────────────────────────────
    # Sessions assigned (timetable slots this week) vs sessions taken (AttendanceSession this month)
    from django.db.models import Avg as _Avg
    month_start = today_local.replace(day=1)
    sessions_taken_map = {row['faculty_id']: row['count'] for row in sessions_month}

    # Timetable slots per faculty (total weekly slots = proxy for "assigned")
    slots_assigned = Timetable.objects.filter(
        subject__department=dept
    ).values('faculty_id').annotate(count=Count('id'))
    slots_assigned_map = {row['faculty_id']: row['count'] for row in slots_assigned}

    # Feedback avg per faculty
    feedback_agg = FacultyFeedbackResponse.objects.filter(
        cycle__department=dept
    ).values('cycle__faculty_id').annotate(responses=Count('id'))
    feedback_map = {}
    for row in feedback_agg:
        fid = row['cycle__faculty_id']
        # Compute avg rating from all responses for this faculty
        responses = FacultyFeedbackResponse.objects.filter(cycle__faculty_id=fid)
        ratings = []
        for r in responses:
            for v in r.ratings.values():
                try: ratings.append(float(v))
                except: pass
        feedback_map[fid] = round(sum(ratings)/len(ratings), 1) if ratings else None

    # Leave days this month per faculty
    leave_days_map = {}
    for f in faculty_list:
        days = 0
        for lv in LeaveApplication.objects.filter(
            faculty=f, status='APPROVED',
            from_date__gte=month_start, from_date__lte=today_local
        ):
            days += max((lv.to_date - lv.from_date).days + 1, 1)
        leave_days_map[f.id] = days

    faculty_performance = []
    for f in faculty_list:
        faculty_performance.append({
            'faculty': f,
            'subj_count': subj_count_map.get(f.id, 0),
            'sessions_taken': sessions_taken_map.get(f.id, 0),
            'slots_assigned': slots_assigned_map.get(f.id, 0),
            'pending_reviews': pending_reviews_map.get(f.user_id, 0),
            'feedback_avg': feedback_map.get(f.id),
            'leave_days': leave_days_map.get(f.id, 0),
        })

    context = {
        'hod': hod, 'dept': dept,
        'college': dept.college,
        'total_faculty': total_faculty_count,
        'total_students': total_students_count,
        'total_subjects': subjects_list.count(),
        'pending_approvals_count': pending_approvals.count() + pending_leaves.count(),
        'faculty_list': faculty_list,
        'students_list': students_list,
        'students_by_sem_section': students_by_sem_section,
        'pending_approvals': pending_approvals,
        'recent_approvals': recent_approvals,
        'pending_leaves': pending_leaves,
        'recent_leaves': recent_leaves,
        'subject_attendance': subject_attendance,
        'today_timetable': today_timetable,
        'today_day': today_day,
        'announcements': announcements,
        'faculty_workload': faculty_workload,
        'faculty_performance': faculty_performance,
        'sem_breakdown': sem_breakdown,
        'approval_stats': approval_stats,
        'smart_alerts': smart_alerts,
        'branding': _get_college_branding(dept.college),
    }

    # Teaching context — only when HOD also takes classes
    hod_faculty = Faculty.objects.filter(user=user).first()
    hod_teaching_subjects = []
    hod_today_timetable = []
    hod_marked_subject_ids = set()
    hod_sub_quota = None

    if hod.can_take_classes and hod_faculty:
        hod_teaching_subjects = list(
            FacultySubject.objects.filter(faculty=hod_faculty)
            .select_related('subject').order_by('subject__semester', 'subject__name')
        )
        hod_marked_subject_ids = set(AttendanceSession.objects.filter(
            faculty=hod_faculty, date=timezone.localdate()
        ).values_list('subject_id', flat=True))

        hod_raw_tt = Timetable.objects.filter(
            Q(faculty=hod_faculty, day_of_week=today_day) |
            Q(substitutions__substitute_faculty=hod_faculty,
              substitutions__date=timezone.localdate(),
              substitutions__status='ACCEPTED'),
        ).select_related('subject', 'classroom').order_by('start_time').distinct()
        hod_today_timetable = _merge_timetable_section_rows(list(hod_raw_tt))

        from datetime import date as _date_hod
        _today = timezone.localdate()
        _sem_start_month = 7 if _today.month >= 7 else 1
        _sem_start = _date_hod(_today.year, _sem_start_month, 1)
        _feature_cfg = CollegeFeatureConfig.objects.filter(college=dept.college).first()
        _sub_max = _feature_cfg.max_substitutions if _feature_cfg else 10
        _subs_used = Substitution.objects.filter(
            original_faculty=hod_faculty, date__gte=_sem_start, status='ACCEPTED'
        ).count()
        hod_sub_quota = {'used': _subs_used, 'max': _sub_max, 'remaining': max(_sub_max - _subs_used, 0)}

    context.update({
        'hod_faculty': hod_faculty,
        'hod_teaching_subjects': hod_teaching_subjects,
        'hod_today_timetable': hod_today_timetable,
        'hod_marked_subject_ids': hod_marked_subject_ids,
        'hod_sub_quota': hod_sub_quota,
        'notifications': Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:20],
    })
    return render(request, 'dashboards/hod.html', context)


@login_required
def hod_post_notice(request):
    """HOD creates an announcement for their department."""
    if request.method != 'POST':
        return redirect('hod_dashboard')
    try:
        hod = HOD.objects.select_related('department').get(user=request.user)
    except HOD.DoesNotExist:
        return redirect('dashboard')

    title = request.POST.get('title', '').strip()
    message = request.POST.get('message', '').strip()
    target = request.POST.get('target', 'all')
    attachment = request.FILES.get('attachment')

    if not title or not message:
        messages.error(request, 'Title and message are required.')
        return redirect(f"{reverse('hod_dashboard')}#notices")

    Announcement.objects.create(
        college=hod.department.college,
        department=hod.department,
        title=title,
        message=message,
        target=target,
        attachment=attachment,
        created_by=request.user,
    )
    messages.success(request, 'Notice posted successfully.')
    return redirect(f"{reverse('hod_dashboard')}#notices")


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
def faculty_assign_substitution(request):
    """
    Faculty requests a substitution for one of their own timetable slots.
    Only faculty who are FREE at that time on that date are shown.
    Creates a PENDING substitution and notifies the substitute.
    """
    faculty = get_object_or_404(Faculty, user=request.user)
    if request.method != 'POST':
        return redirect(f"{reverse('faculty_dashboard')}#substitution")

    # Check substitution quota
    college = faculty.department.college
    feature_cfg = CollegeFeatureConfig.objects.filter(college=college).first()
    sub_max = feature_cfg.max_substitutions if feature_cfg else 10
    from datetime import date as _date2
    today2 = timezone.localdate()
    sem_start_month = 7 if today2.month >= 7 else 1
    sem_start2 = _date2(today2.year, sem_start_month, 1)
    subs_used = Substitution.objects.filter(
        original_faculty=faculty,
        date__gte=sem_start2,
        status='ACCEPTED',
    ).count()
    if subs_used >= sub_max:
        messages.error(request, f'You have reached your substitution limit ({sub_max}) for this semester.')
        return redirect(f"{reverse('faculty_dashboard')}#substitution")

    slot_id        = request.POST.get('timetable_slot')
    sub_faculty_id = request.POST.get('substitute_faculty')
    date_str       = request.POST.get('date', '').strip()
    note           = request.POST.get('note', '').strip()

    slot = get_object_or_404(Timetable, pk=slot_id, faculty=faculty)

    try:
        sub_date = datetime.fromisoformat(date_str).date()
    except (ValueError, TypeError):
        sub_date = timezone.now().date()

    if sub_date < timezone.now().date():
        messages.error(request, 'Cannot assign substitution for a past date.')
        return redirect(f"{reverse('faculty_dashboard')}#substitution")

    # Enforce semester date range
    from datetime import date as _date3
    _today3 = timezone.localdate()
    _sem_start_month3 = 7 if _today3.month >= 7 else 1
    _sem_start3 = _date3(_today3.year, _sem_start_month3, 1)
    _sem_end_month3 = _sem_start_month3 + 5
    _sem_end_year3 = _today3.year + (_sem_end_month3 - 1) // 12
    _sem_end_month3 = ((_sem_end_month3 - 1) % 12) + 1
    _sem_end3 = _date3(_sem_end_year3, _sem_end_month3, 1)
    if not (_sem_start3 <= sub_date <= _sem_end3):
        messages.error(request, 'Substitution date must be within the current semester.')
        return redirect(f"{reverse('faculty_dashboard')}#substitution")

    # Enforce date falls on the slot's day of week
    day_code = {0:'MON',1:'TUE',2:'WED',3:'THU',4:'FRI',5:'SAT'}.get(sub_date.weekday(), '')
    if day_code != slot.day_of_week:
        day_names = {'MON':'Monday','TUE':'Tuesday','WED':'Wednesday','THU':'Thursday','FRI':'Friday','SAT':'Saturday'}
        messages.error(request, f'This slot is on {day_names.get(slot.day_of_week, slot.day_of_week)}s. Please pick a {day_names.get(slot.day_of_week, slot.day_of_week)} date.')
        return redirect(f"{reverse('faculty_dashboard')}#substitution")

    sub_faculty = get_object_or_404(Faculty, pk=sub_faculty_id, department=faculty.department)

    if sub_faculty.id == faculty.id:
        messages.error(request, 'You cannot assign yourself as a substitute.')
        return redirect(f"{reverse('faculty_dashboard')}#substitution")

    # Verify the chosen faculty is actually free at that time on that date
    clash = Timetable.objects.filter(
        faculty=sub_faculty,
        day_of_week=day_code,
    ).filter(
        start_time__lt=slot.end_time,
        end_time__gt=slot.start_time,
    ).exists()
    if clash:
        messages.error(
            request,
            f'{sub_faculty.user.get_full_name()} has a timetable clash at that time. '
            'Please choose a faculty who is free.'
        )
        return redirect(f"{reverse('faculty_dashboard')}#substitution")

    # Create or update substitution (PENDING)
    sub, created = Substitution.objects.update_or_create(
        timetable_slot=slot,
        date=sub_date,
        defaults={
            'original_faculty': faculty,
            'substitute_faculty': sub_faculty,
            'status': 'PENDING',
            'rejection_reason': '',
            'responded_at': None,
            'topic_covered': '',
            'note': note,
        }
    )

    note_snippet = f' Note: "{note}"' if note else ''

    # Notify the substitute faculty
    Notification.objects.create(
        user=sub_faculty.user,
        message=(
            f'Substitution Request: {request.user.get_full_name() or request.user.username} '
            f'has requested you to cover {slot.subject.name} ({slot.subject.code}) '
            f'on {sub_date.strftime("%d %b %Y")} '
            f'({slot.start_time.strftime("%I:%M %p")}–{slot.end_time.strftime("%I:%M %p")}).'
            f'{note_snippet} Please accept or reject from your dashboard.'
        )
    )

    # Notify the HOD of the department
    hod = HOD.objects.filter(department=faculty.department, is_active=True).first()
    if hod:
        Notification.objects.create(
            user=hod.user,
            message=(
                f'Substitution: {request.user.get_full_name() or request.user.username} '
                f'has requested {sub_faculty.user.get_full_name()} to cover '
                f'{slot.subject.name} ({slot.subject.code}) '
                f'on {sub_date.strftime("%d %b %Y")} '
                f'({slot.start_time.strftime("%I:%M %p")}–{slot.end_time.strftime("%I:%M %p")}).'
                f'{note_snippet}'
            )
        )

    messages.success(
        request,
        f'Substitution request sent to {sub_faculty.user.get_full_name() or sub_faculty.user.username}. '
        f'Waiting for their acceptance.'
    )
    return redirect(f"{reverse('faculty_dashboard')}#substitution")


@login_required
def faculty_substitution_respond(request, pk):
    """
    Substitute faculty accepts or rejects a pending substitution request.
    Only the designated substitute can respond.
    """
    faculty = get_object_or_404(Faculty, user=request.user)
    sub = get_object_or_404(Substitution, pk=pk, substitute_faculty=faculty)

    if sub.status != 'PENDING':
        messages.warning(request, 'This substitution request has already been responded to.')
        return redirect(f"{reverse('faculty_dashboard')}#substitution")

    if request.method != 'POST':
        return redirect(f"{reverse('faculty_dashboard')}#substitution")

    action = request.POST.get('action')  # 'accept' or 'reject'
    reason = request.POST.get('rejection_reason', '').strip()

    if action == 'accept':
        sub.status = 'ACCEPTED'
        sub.responded_at = timezone.now()
        sub.save(update_fields=['status', 'responded_at'])

        # Notify the original faculty
        Notification.objects.create(
            user=sub.original_faculty.user,
            message=(
                f'{request.user.get_full_name() or request.user.username} has ACCEPTED your substitution request '
                f'for {sub.timetable_slot.subject.name} on {sub.date.strftime("%d %b %Y")}. '
                f'They will cover the class and mark attendance.'
            )
        )
        messages.success(request, f'You have accepted the substitution for {sub.timetable_slot.subject.name} on {sub.date.strftime("%d %b %Y")}.')

    elif action == 'reject':
        sub.status = 'REJECTED'
        sub.rejection_reason = reason or 'No reason provided.'
        sub.responded_at = timezone.now()
        sub.save(update_fields=['status', 'rejection_reason', 'responded_at'])

        # Notify the original faculty
        Notification.objects.create(
            user=sub.original_faculty.user,
            message=(
                f'{request.user.get_full_name() or request.user.username} has REJECTED your substitution request '
                f'for {sub.timetable_slot.subject.name} on {sub.date.strftime("%d %b %Y")}. '
                f'Reason: {sub.rejection_reason}. Please arrange another substitute.'
            )
        )
        messages.warning(request, f'You have rejected the substitution for {sub.timetable_slot.subject.name}.')

    return redirect(f"{reverse('faculty_dashboard')}#substitution")


@login_required
def faculty_substitution_free_faculty(request):
    """
    AJAX — returns faculty FREE at the given slot's time on the given date.
    Also returns the slot's day_of_week and semester date bounds for the JS
    date-picker constraint.

    GET params: slot_id, date (YYYY-MM-DD)
    Returns JSON:
      {
        faculty: [{id, name, employee_id}, ...],
        day: 'MON',
        slot_day_index: 0,          # JS weekday index (0=Sun … 6=Sat)
        sem_start: 'YYYY-MM-DD',
        sem_end:   'YYYY-MM-DD',
      }
    """
    faculty = get_object_or_404(Faculty, user=request.user)
    slot_id  = request.GET.get('slot_id')
    date_str = request.GET.get('date', '')

    if not slot_id:
        return JsonResponse({'faculty': [], 'error': 'slot_id required'})

    try:
        slot = Timetable.objects.select_related('version').get(pk=slot_id, faculty=faculty)
    except Timetable.DoesNotExist:
        return JsonResponse({'faculty': [], 'error': 'slot not found'})

    # ── Semester date bounds ──────────────────────────────────────────────────
    # Use timetable version dates if available, else ±3 months from today
    today = timezone.localdate()
    if slot.version and slot.version.valid_from and slot.version.valid_to:
        sem_start = slot.version.valid_from
        sem_end   = slot.version.valid_to
    else:
        # Fallback: current month start → 5 months ahead (covers a semester)
        from datetime import date as _date
        sem_start = today.replace(day=1)
        # 5 months ahead
        month = today.month + 5
        year  = today.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        sem_end = _date(year, month, 1)

    # ── Day mapping ───────────────────────────────────────────────────────────
    DAY_TO_JS = {'MON': 1, 'TUE': 2, 'WED': 3, 'THU': 4, 'FRI': 5, 'SAT': 6}
    day_code      = slot.day_of_week
    slot_day_index = DAY_TO_JS.get(day_code, 1)

    # ── If no date provided, just return bounds (slot just selected) ──────────
    if not date_str:
        return JsonResponse({
            'faculty': [],
            'day': day_code,
            'slot_day_index': slot_day_index,
            'sem_start': sem_start.isoformat(),
            'sem_end': sem_end.isoformat(),
        })

    try:
        check_date = datetime.fromisoformat(date_str).date()
    except ValueError:
        return JsonResponse({'faculty': [], 'error': 'invalid date'})

    # Verify the chosen date actually falls on the slot's day
    actual_day = {0:'MON',1:'TUE',2:'WED',3:'THU',4:'FRI',5:'SAT'}.get(check_date.weekday(), '')
    if actual_day != day_code:
        return JsonResponse({
            'faculty': [],
            'day': day_code,
            'slot_day_index': slot_day_index,
            'sem_start': sem_start.isoformat(),
            'sem_end': sem_end.isoformat(),
            'error': f'Selected date is a {actual_day}, but this slot is on {day_code}.',
        })

    # ── All dept faculty except requester ─────────────────────────────────────
    dept_faculty = list(
        Faculty.objects.filter(department=faculty.department)
        .exclude(pk=faculty.pk)
        .select_related('user')
    )

    if not dept_faculty:
        return JsonResponse({
            'faculty': [],
            'day': day_code,
            'slot_day_index': slot_day_index,
            'sem_start': sem_start.isoformat(),
            'sem_end': sem_end.isoformat(),
        })

    dept_faculty_ids = [f.pk for f in dept_faculty]

    # ── Who has a timetable CLASS at this exact time on this day ──────────────
    busy_ids = set(
        Timetable.objects.filter(
            faculty_id__in=dept_faculty_ids,
            day_of_week=day_code,
            start_time__lt=slot.end_time,
            end_time__gt=slot.start_time,
        ).values_list('faculty_id', flat=True)
    )

    # ── Who already has an ACCEPTED substitution at this time on this date ────
    busy_sub_ids = set(
        Substitution.objects.filter(
            timetable_slot__day_of_week=day_code,
            timetable_slot__start_time__lt=slot.end_time,
            timetable_slot__end_time__gt=slot.start_time,
            date=check_date,
            status='ACCEPTED',
            substitute_faculty_id__in=dept_faculty_ids,
        ).values_list('substitute_faculty_id', flat=True)
    )

    busy_ids |= busy_sub_ids

    # Everyone NOT busy is free
    # ── Load balancing: count sessions each free faculty has on check_date ────
    free_faculty_ids = [f.pk for f in dept_faculty if f.pk not in busy_ids]
    sessions_today_map = {}
    if free_faculty_ids:
        sess_counts = AttendanceSession.objects.filter(
            faculty_id__in=free_faculty_ids,
            date=check_date,
        ).values('faculty_id').annotate(cnt=Count('id'))
        sessions_today_map = {r['faculty_id']: r['cnt'] for r in sess_counts}
        # Also count substitution duties on that date
        sub_counts = Substitution.objects.filter(
            substitute_faculty_id__in=free_faculty_ids,
            date=check_date,
            status='ACCEPTED',
        ).values('substitute_faculty_id').annotate(cnt=Count('id'))
        for r in sub_counts:
            sessions_today_map[r['substitute_faculty_id']] = sessions_today_map.get(r['substitute_faculty_id'], 0) + r['cnt']

    free_faculty = [
        {
            'id': f.pk,
            'name': f.user.get_full_name() or f.user.username,
            'employee_id': f.employee_id or '',
            'sessions_today': sessions_today_map.get(f.pk, 0),
        }
        for f in dept_faculty
        if f.pk not in busy_ids
    ]

    # ── Conflict check for a specific faculty (check_id param) ───────────────
    check_id = request.GET.get('check_id')
    conflict_msg = None
    if check_id:
        try:
            check_fac = Faculty.objects.get(pk=check_id, department=faculty.department)
            # Check if they already have a pending/accepted substitution that day
            existing_sub = Substitution.objects.filter(
                substitute_faculty=check_fac,
                date=check_date,
                status__in=['PENDING', 'ACCEPTED'],
            ).select_related('timetable_slot__subject').first()
            if existing_sub:
                conflict_msg = (
                    f'{check_fac.user.get_full_name()} already has a substitution duty '
                    f'for {existing_sub.timetable_slot.subject.name} on this date.'
                )
        except Faculty.DoesNotExist:
            pass

    response_data = {
        'faculty': free_faculty,
        'day': day_code,
        'slot_day_index': slot_day_index,
        'sem_start': sem_start.isoformat(),
        'sem_end': sem_end.isoformat(),
    }
    if conflict_msg:
        response_data['conflict'] = conflict_msg

    return JsonResponse(response_data)


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
        else:
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
        # Reload substitutions after POST
        substitutions = Substitution.objects.filter(timetable_slot__subject__department=dept, date__gte=today).order_by('date')

    # For the form: slots in this department and available faculty
    slots = Timetable.objects.filter(subject__department=dept).select_related('subject', 'faculty__user')
    faculty_list = Faculty.objects.filter(department=dept).select_related('user')
    slot_faculty_map = {slot.pk: slot.faculty_id for slot in slots}

    import json
    slot_faculty_json = json.dumps(slot_faculty_map)

    ctx = {
        'substitutions': substitutions, 'slots': slots, 'faculty_list': faculty_list,
        'slot_faculty_map': slot_faculty_map,
        'slot_faculty_json': slot_faculty_json,
        'today': today,
        'college': dept.college,
        'branding': _get_college_branding(dept.college),
    }
    if request.GET.get('partial') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'hod/substitutions_partial.html', ctx)
    return render(request, 'hod/substitutions.html', ctx)


@login_required
def hod_student_quick_json(request, pk):
    """Return lightweight student stats as JSON for the HOD popup dialog."""
    from django.http import JsonResponse
    try:
        hod = HOD.objects.select_related('department').get(user=request.user)
    except HOD.DoesNotExist:
        return JsonResponse({'error': 'forbidden'}, status=403)

    dept = hod.department
    student = get_object_or_404(Student, pk=pk, department=dept)

    # Basic profile
    try:
        profile = student.user.studentprofile
        dob = str(profile.date_of_birth) if profile.date_of_birth else None
        gender = profile.gender
        phone = profile.phone_number
    except Exception:
        dob = gender = phone = None

    # Attendance this semester
    subjects = Subject.objects.filter(department=dept, semester=student.current_semester)
    att_agg = Attendance.objects.filter(
        student=student, session__subject__in=subjects
    ).values('session__subject_id', 'session__subject__name').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    att_list = []
    total_p = total_t = 0
    for r in att_agg:
        pct = round(r['present'] / r['total'] * 100, 1) if r['total'] else None
        att_list.append({'subject': r['session__subject__name'], 'present': r['present'], 'total': r['total'], 'pct': pct})
        total_p += r['present']
        total_t += r['total']
    overall_pct = round(total_p / total_t * 100, 1) if total_t else None

    # Results summary
    results = list(Result.objects.filter(student=student).order_by('semester').values('semester', 'sgpa', 'percentage'))
    cgpa = round(sum(r['sgpa'] for r in results) / len(results), 2) if results else None

    return JsonResponse({
        'id': student.pk,
        'name': student.user.get_full_name() or student.user.username,
        'roll_number': student.roll_number,
        'email': student.user.email,
        'semester': student.current_semester,
        'section': student.section or '—',
        'status': student.status,
        'admission_year': student.admission_year,
        'admission_type': student.get_admission_type_display(),
        'dob': dob,
        'gender': gender,
        'phone': phone,
        'overall_attendance': overall_pct,
        'attendance': att_list,
        'results': [{'semester': r['semester'], 'sgpa': round(r['sgpa'], 2), 'pct': round(r['percentage'], 1)} for r in results],
        'cgpa': cgpa,
        'profile_url': f'/dashboard/hod/student/{student.pk}/',
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

    ctx = {
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
    }
    if request.GET.get('modal'):
        return render(request, 'hod/student_profile_fragment.html', ctx)
    return render(request, 'hod/student_profile.html', ctx)


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
    leave_history = LeaveApplication.objects.filter(faculty=faculty).order_by('-from_date')[:10]

    # Feedback average from student feedback cycles
    feedback_avg = None
    try:
        responses = FacultyFeedbackResponse.objects.filter(cycle__faculty=faculty)
        ratings = []
        for r in responses:
            for v in r.ratings.values():
                try:
                    ratings.append(float(v))
                except (TypeError, ValueError):
                    pass
        if ratings:
            feedback_avg = round(sum(ratings) / len(ratings), 1)
    except Exception:
        pass

    # Leave summary counts
    leave_summary = {
        'approved': LeaveApplication.objects.filter(faculty=faculty, status='APPROVED').count(),
        'pending': LeaveApplication.objects.filter(faculty=faculty, status='PENDING').count(),
        'rejected': LeaveApplication.objects.filter(faculty=faculty, status='REJECTED').count(),
    }

    ctx = {
        'hod': hod, 'dept': dept, 'college': dept.college,
        'faculty': faculty,
        'assigned_subjects': assigned_subjects,
        'subject_stats': subject_stats,
        'sessions_this_month': sessions_this_month,
        'sessions_total': sessions_total,
        'pending_reviews': pending_reviews,
        'leave_history': leave_history,
        'feedback_avg': feedback_avg,
        'leave_summary': leave_summary,
        'branding': _get_college_branding(dept.college),
    }
    if request.GET.get('modal'):
        return render(request, 'hod/faculty_profile_fragment.html', ctx)
    return render(request, 'hod/faculty_profile.html', ctx)


# ── FACULTY DASHBOARD ────────────────────────────────────

def _non_teaching_faculty_dashboard(request, faculty):
    """Dashboard for faculty with no subject assignments (admin/lab/support roles)."""
    college = faculty.department.college
    announcements = _scope_announcements_for_college(college).order_by('-created_at')[:8]
    leave_history = LeaveApplication.objects.filter(faculty=faculty).order_by('-from_date')[:8]
    my_requests_qs = HODApproval.objects.filter(requested_by=request.user).order_by('-created_at')
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:10]

    return render(request, 'dashboards/faculty_non_teaching.html', {
        'faculty': faculty,
        'college': college,
        'announcements': announcements,
        'leave_history': leave_history,
        'my_requests': my_requests_qs[:5],
        'my_requests_count': my_requests_qs.filter(status='PENDING').count(),
        'notifications': notifications,
        'branding': _get_college_branding(college),
    })


@login_required
def faculty_student_profile_fragment(request, pk):
    """Faculty views a student's full profile in a modal — attendance, marks, quizzes, assignments."""
    try:
        faculty = Faculty.objects.select_related('department').get(user=request.user)
    except Faculty.DoesNotExist:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    student = get_object_or_404(Student, pk=pk, department=faculty.department)
    subject_ids = list(FacultySubject.objects.filter(faculty=faculty).values_list('subject_id', flat=True))
    subjects = Subject.objects.filter(id__in=subject_ids, semester=student.current_semester)

    # Attendance per subject this semester
    att_agg = Attendance.objects.filter(
        student=student, session__subject__in=subjects
    ).values('session__subject_id', 'session__subject__name').annotate(
        total=Count('id'), present=Count('id', filter=Q(status='PRESENT'))
    )
    att_data = []
    total_p = total_t = 0
    for r in att_agg:
        pct = round(r['present'] / r['total'] * 100, 1) if r['total'] else None
        att_data.append({'name': r['session__subject__name'], 'present': r['present'], 'total': r['total'], 'pct': pct})
        total_p += r['present']; total_t += r['total']
    overall_att = round(total_p / total_t * 100, 1) if total_t else None

    # Internal marks per subject
    im_qs = InternalMark.objects.filter(student=student, subject__in=subjects).select_related('subject')
    im_data = [{'subject': im.subject.name, 'ia1': im.ia1, 'ia2': im.ia2,
                'assignment': im.assignment_marks, 'attendance': im.attendance_marks,
                'total': im.total} for im in im_qs]

    # Quiz attempts for faculty's quizzes
    quiz_qs = QuizAttempt.objects.filter(
        student=student, quiz__subject_id__in=subject_ids, is_submitted=True
    ).select_related('quiz__subject').order_by('-submitted_at')
    quiz_data = [{'quiz': qa.quiz.title, 'subject': qa.quiz.subject.name,
                  'score': qa.score, 'max': qa.quiz.total_marks,
                  'pct': round(qa.score / qa.quiz.total_marks * 100, 1) if qa.score and qa.quiz.total_marks else None}
                 for qa in quiz_qs]

    # Assignment submissions for faculty's assignments
    asn_qs = AssignmentSubmission.objects.filter(
        student=student, assignment__created_by=request.user,
        assignment__subject_id__in=subject_ids
    ).select_related('assignment__subject').order_by('-submitted_at')
    asn_data = [{'title': s.assignment.title, 'subject': s.assignment.subject.name,
                 'marks': s.marks, 'max': s.assignment.max_marks,
                 'submitted': True,
                 'pct': round(s.marks / s.assignment.max_marks * 100, 1) if s.marks and s.assignment.max_marks else None}
                for s in asn_qs]
    # Also find assignments not submitted
    all_asn = Assignment.objects.filter(created_by=request.user, subject_id__in=subject_ids, is_published=True)
    submitted_ids = set(asn_qs.values_list('assignment_id', flat=True))
    for a in all_asn:
        if a.id not in submitted_ids:
            asn_data.append({'title': a.title, 'subject': a.subject.name,
                             'marks': None, 'max': a.max_marks, 'submitted': False, 'pct': None})

    return render(request, 'faculty/student_profile_fragment.html', {
        'student': student,
        'overall_att': overall_att,
        'att_data': att_data,
        'im_data': im_data,
        'quiz_data': quiz_data,
        'asn_data': asn_data,
    })


@login_required
def faculty_dashboard(request):
    user = request.user
    try:
        faculty = Faculty.objects.select_related('department').get(user=user)
    except Faculty.DoesNotExist:
        messages.error(request, 'Faculty profile not found. Contact admin.')
        return redirect('home')

    # Non-teaching faculty: has Faculty record but no subject assignments
    is_teaching = FacultySubject.objects.filter(faculty=faculty).exists()
    if not is_teaching:
        return _non_teaching_faculty_dashboard(request, faculty)

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
        Q(faculty=faculty, day_of_week=today_day) |
        Q(substitutions__substitute_faculty=faculty, substitutions__date=today, substitutions__status='ACCEPTED'),
    ).select_related('subject', 'classroom').order_by('start_time').distinct()
    today_timetable = _merge_timetable_section_rows(list(raw_timetable))
    today_sessions = today_timetable
    has_unmarked_today = any(t.subject_id not in marked_subject_ids for t in today_timetable)

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
        breaks=TimetableBreak.objects.filter(college=faculty.department.college, applies_to_all=True).order_by('day_of_week','start_time'),
        merge_sections=True
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

    announcements = _scope_announcements_for_college(faculty.department.college, target='faculty').order_by('-created_at').select_related('created_by')[:20]

    # Today's breaks for faculty's college
    faculty_today_breaks = list(TimetableBreak.objects.filter(
        college=faculty.department.college, day_of_week=today_day, applies_to_all=True
    ).order_by('start_time'))

    # Per-subject enriched data for My Subjects panel
    all_subject_ids = [s.id for s in subjects]
    fac_assignments_qs = Assignment.objects.filter(
        created_by=user, subject_id__in=all_subject_ids
    ).select_related('subject').order_by('subject_id', '-deadline')
    fac_assignments_by_subj = {}
    for a in fac_assignments_qs:
        fac_assignments_by_subj.setdefault(a.subject_id, []).append(a)

    fac_quizzes_qs = Quiz.objects.filter(
        created_by=user, subject_id__in=all_subject_ids
    ).select_related('subject').order_by('subject_id', '-created_at')
    fac_quizzes_by_subj = {}
    for q in fac_quizzes_qs:
        fac_quizzes_by_subj.setdefault(q.subject_id, []).append(q)

    ce_submissions = HODApproval.objects.filter(
        requested_by=user, approval_type='CE_MARKS',
        subject_id__in=all_subject_ids,
    ).select_related('subject').order_by('subject_id', '-created_at')
    ce_submission_by_subj = {}
    for ce in ce_submissions:
        if ce.subject_id not in ce_submission_by_subj:
            ce_submission_by_subj[ce.subject_id] = ce

    fac_lesson_plans_qs = LessonPlan.objects.filter(
        faculty=faculty, subject_id__in=all_subject_ids
    ).select_related('subject').order_by('subject_id', 'planned_date')
    fac_lesson_plans_by_subj = {}
    for lp in fac_lesson_plans_qs:
        fac_lesson_plans_by_subj.setdefault(lp.subject_id, []).append(lp)

    im_filled_by_subj = {}
    for subj in subjects:
        # Use section-scoped student count
        sec_students = _get_section_students(faculty, subj)
        enrolled = sec_students.count()
        filled = InternalMark.objects.filter(subject=subj, student__in=sec_students).count()
        im_filled_by_subj[subj.id] = {'filled': filled, 'total': enrolled}

    from django.db.models import Avg as _Avg
    my_subjects = []
    for item in subject_cards:
        subj = item['subject']
        sec_students = _get_section_students(faculty, subj)
        sec_enrolled = sec_students.count()

        assignments = fac_assignments_by_subj.get(subj.id, [])
        for a in assignments:
            a.sub_count = AssignmentSubmission.objects.filter(assignment=a).count()
            a.graded_count = AssignmentSubmission.objects.filter(assignment=a, marks__isnull=False).count()
            a.pending_review = a.sub_count - a.graded_count
            a.not_submitted = max(0, sec_enrolled - a.sub_count)
            a.first_ungraded = AssignmentSubmission.objects.filter(assignment=a, marks__isnull=True).first()

        quizzes = fac_quizzes_by_subj.get(subj.id, [])
        for q in quizzes:
            q.attempted = QuizAttempt.objects.filter(quiz=q, is_submitted=True).count()
            q.not_attempted = max(0, sec_enrolled - q.attempted)
            q.avg_score = QuizAttempt.objects.filter(quiz=q, is_submitted=True).aggregate(a=_Avg('score'))['a']

        sec_filled = InternalMark.objects.filter(subject=subj, student__in=sec_students).count()
        ce_existing = {im.student_id: im for im in InternalMark.objects.filter(subject=subj, student__in=sec_students)}

        my_subjects.append({
            **item,
            'enrolled': sec_enrolled,
            'assignments': assignments,
            'quizzes': quizzes,
            'ce_submission': ce_submission_by_subj.get(subj.id),
            'lesson_plans': fac_lesson_plans_by_subj.get(subj.id, []),
            'im_status': {'filled': sec_filled, 'total': sec_enrolled},
            'ce_students': list(sec_students),
            'ce_existing': ce_existing,
        })

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
        'has_unmarked_today': has_unmarked_today,
        'recent_sessions': recent_sessions,
        'pending_submissions': pending_submissions_qs[:10],
        'pending_submissions_count': pending_submissions_qs.count(),
        'my_requests': my_requests_qs[:5],
        'my_requests_count': my_requests_qs.filter(status='PENDING').count(),
        'my_assignments': my_assignments,
        'leave_history': leave_history,
        'announcements': announcements,
        'branding': _get_college_branding(faculty.department.college),
        'my_subjects': my_subjects,
        'now': timezone.now(),
        'dept_faculty_list': Faculty.objects.filter(
            department=faculty.department, is_deleted=False
        ).exclude(pk=faculty.pk).select_related('user').order_by('user__first_name'),
        'all_week_slots': list(all_week_slots),
    }

    # ── Leave & Substitution quotas ───────────────────────────────────────────
    feature_cfg = CollegeFeatureConfig.objects.filter(college=college).first()
    current_year = today.year
    # Count approved/pending leaves this year by type
    leaves_this_year = LeaveApplication.objects.filter(
        faculty=faculty,
        from_date__year=current_year,
        status__in=['APPROVED', 'PENDING'],
    )
    def _leave_days(qs, leave_type):
        total = 0
        for l in qs.filter(leave_type=leave_type):
            total += max((l.to_date - l.from_date).days + 1, 1)
        return total

    leave_quota = {
        'CL':  {'used': _leave_days(leaves_this_year, 'CL'),  'max': feature_cfg.max_casual_leaves  if feature_cfg else 12},
        'ML':  {'used': _leave_days(leaves_this_year, 'ML'),  'max': feature_cfg.max_medical_leaves if feature_cfg else 10},
        'EL':  {'used': _leave_days(leaves_this_year, 'EL'),  'max': feature_cfg.max_earned_leaves  if feature_cfg else 15},
        'OD':  {'used': _leave_days(leaves_this_year, 'OD'),  'max': feature_cfg.max_od_leaves      if feature_cfg else 20},
    }
    for k, v in leave_quota.items():
        v['remaining'] = max(v['max'] - v['used'], 0)

    # Substitutions this semester — only count ACCEPTED (approved) ones
    from datetime import date as _date
    sem_start_month = 7 if today.month >= 7 else 1
    sem_start = _date(today.year, sem_start_month, 1)
    subs_used = Substitution.objects.filter(
        original_faculty=faculty,
        date__gte=sem_start,
        status='ACCEPTED',
    ).count()
    sub_max = feature_cfg.max_substitutions if feature_cfg else 10
    sub_quota = {'used': subs_used, 'max': sub_max, 'remaining': max(sub_max - subs_used, 0)}

    context['leave_quota'] = leave_quota
    context['sub_quota'] = sub_quota

    # ── Pre-compute substitution data: for each slot, who is free ────────────
    import json as _json
    dept_faculty_qs = Faculty.objects.filter(
        department=faculty.department, is_deleted=False
    ).exclude(pk=faculty.pk).select_related('user').order_by('user__first_name')
    dept_faculty_all = list(dept_faculty_qs)
    dept_faculty_ids = [f.pk for f in dept_faculty_all]

    # For each slot, find faculty who have a conflicting timetable slot
    slot_busy_map = {}  # slot_pk -> set of busy faculty_ids
    if dept_faculty_ids and all_week_slots:
        for slot in all_week_slots:
            busy = set(
                Timetable.objects.filter(
                    faculty_id__in=dept_faculty_ids,
                    day_of_week=slot.day_of_week,
                    start_time__lt=slot.end_time,
                    end_time__gt=slot.start_time,
                ).values_list('faculty_id', flat=True)
            )
            slot_busy_map[slot.pk] = busy

    # Build JSON: {slot_pk: {faculty: [...], day: 'MON', sem_start: 'YYYY-MM-DD', sem_end: 'YYYY-MM-DD'}}
    from datetime import date as _date_sub
    _sub_today = timezone.localdate()
    _sub_sem_start_month = 7 if _sub_today.month >= 7 else 1
    _sub_sem_start = _date_sub(_sub_today.year, _sub_sem_start_month, 1)
    _sub_sem_end_month = _sub_sem_start_month + 5
    _sub_sem_end_year = _sub_today.year + (_sub_sem_end_month - 1) // 12
    _sub_sem_end_month = ((_sub_sem_end_month - 1) % 12) + 1
    _sub_sem_end = _date_sub(_sub_sem_end_year, _sub_sem_end_month, 1)

    sub_faculty_data = {}
    for slot in all_week_slots:
        busy = slot_busy_map.get(slot.pk, set())
        free = [
            {
                'id': f.pk,
                'name': f.user.get_full_name() or f.user.username,
                'employee_id': f.employee_id or '',
            }
            for f in dept_faculty_all
            if f.pk not in busy
        ]
        # Use timetable version dates if available
        if hasattr(slot, 'version') and slot.version and getattr(slot.version, 'valid_from', None) and getattr(slot.version, 'valid_to', None):
            sem_start_str = slot.version.valid_from.isoformat()
            sem_end_str   = slot.version.valid_to.isoformat()
        else:
            sem_start_str = _sub_sem_start.isoformat()
            sem_end_str   = _sub_sem_end.isoformat()
        sub_faculty_data[str(slot.pk)] = {
            'faculty': free,
            'day': slot.day_of_week,
            'sem_start': sem_start_str,
            'sem_end': sem_end_str,
        }

    context['sub_faculty_json'] = _json.dumps(sub_faculty_data)

    # ── Analytics: student-level visibility ──────────────────────────────────
    # Per-student attendance across all faculty's subjects
    student_att_detail = Attendance.objects.filter(
        session__subject_id__in=subject_ids
    ).values('student_id', 'session__subject_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    # Build per-student summary: {student_id: {subject_id: {total, present, pct}}}
    stu_subj_map = {}
    for row in student_att_detail:
        sid = row['student_id']
        subj = row['session__subject_id']
        pct = round(row['present'] / row['total'] * 100, 1) if row['total'] > 0 else 0
        stu_subj_map.setdefault(sid, {})[subj] = {'total': row['total'], 'present': row['present'], 'pct': pct}

    # Get all students across faculty's subjects
    all_students_qs = Student.objects.filter(
        department=faculty.department,
        current_semester__in=list({s.semester for s in subjects}),
        status='ACTIVE', is_deleted=False,
    ).select_related('user').order_by('roll_number')

    # Marks for performance analysis
    marks_qs = Marks.objects.filter(
        subject_id__in=subject_ids
    ).values('student_id', 'subject_id', 'marks_obtained', 'max_marks')
    stu_marks_map = {}
    for m in marks_qs:
        sid = m['student_id']
        pct = round(m['marks_obtained'] / m['max_marks'] * 100, 1) if m['max_marks'] > 0 else 0
        stu_marks_map.setdefault(sid, []).append({'subject_id': m['subject_id'], 'pct': pct, 'marks': m['marks_obtained'], 'max': m['max_marks']})

    # Recently absent (last 7 days)
    week_ago = today - timedelta(days=7)
    recent_absent_qs = Attendance.objects.filter(
        session__subject_id__in=subject_ids,
        session__date__gte=week_ago,
        status='ABSENT',
    ).select_related('student__user', 'session__subject').order_by('-session__date')[:50]

    # Build student analytics rows
    analytics_students = []
    for student in all_students_qs[:100]:
        subj_data = stu_subj_map.get(student.id, {})
        if not subj_data:
            continue
        # Overall attendance across faculty's subjects
        total_p = sum(v['present'] for v in subj_data.values())
        total_t = sum(v['total'] for v in subj_data.values())
        overall_pct = round(total_p / total_t * 100, 1) if total_t > 0 else 0
        # Marks average
        marks_data = stu_marks_map.get(student.id, [])
        avg_marks_pct = round(sum(m['pct'] for m in marks_data) / len(marks_data), 1) if marks_data else None
        # At-risk: attendance < 75 OR marks avg < 40
        is_at_risk = overall_pct < 75 or (avg_marks_pct is not None and avg_marks_pct < 40)
        analytics_students.append({
            'student': student,
            'overall_pct': overall_pct,
            'avg_marks_pct': avg_marks_pct,
            'is_at_risk': is_at_risk,
            'subj_count': len(subj_data),
        })

    # Top performers: sort by marks desc, then attendance
    top_performers = sorted(
        [s for s in analytics_students if s['avg_marks_pct'] is not None],
        key=lambda x: (x['avg_marks_pct'], x['overall_pct']), reverse=True
    )[:10]
    # At-risk students
    at_risk_students = sorted(
        [s for s in analytics_students if s['is_at_risk']],
        key=lambda x: x['overall_pct']
    )[:20]

    # Subject comparison: avg marks % per subject
    subj_marks_agg = Marks.objects.filter(subject_id__in=subject_ids).values('subject_id').annotate(
        avg_pct=Avg(Cast('marks_obtained', FloatField()) * 100.0 / Cast('max_marks', FloatField())),
        count=Count('id')
    )
    subj_marks_map = {r['subject_id']: {'avg_pct': round(r['avg_pct'] or 0, 1), 'count': r['count']} for r in subj_marks_agg}

    # Attendance trend: last 8 weeks per subject
    eight_weeks_ago = today - timedelta(weeks=8)
    weekly_att = Attendance.objects.filter(
        session__subject_id__in=subject_ids,
        session__date__gte=eight_weeks_ago,
    ).annotate(
        week=TruncWeek('session__date')
    ).values('week', 'session__subject_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    ).order_by('week')

    # Build weekly trend per subject
    att_trend_by_subj = {}
    for row in weekly_att:
        subj_id = row['session__subject_id']
        pct = round(row['present'] / row['total'] * 100, 1) if row['total'] > 0 else 0
        att_trend_by_subj.setdefault(subj_id, []).append({
            'week': row['week'].strftime('%d %b') if row['week'] else '',
            'pct': pct,
        })

    # Build analytics subject list
    analytics_subjects = []
    for subj in subjects:
        marks_info = subj_marks_map.get(subj.id, {'avg_pct': 0, 'count': 0})
        agg = att_map.get(subj.id, {'total': 0, 'present': 0})
        att_pct = round(agg['present'] / agg['total'] * 100, 1) if agg['total'] > 0 else 0
        analytics_subjects.append({
            'subject': subj,
            'att_pct': att_pct,
            'avg_marks_pct': marks_info['avg_pct'],
            'marks_count': marks_info['count'],
            'defaulters': defaulters_map.get(subj.id, 0),
            'enrolled': enrolled_counts.get((subj.department_id, subj.semester), 0),
            'trend': att_trend_by_subj.get(subj.id, []),
        })

    context['top_performers'] = top_performers
    context['at_risk_students'] = at_risk_students
    context['recent_absent'] = list(recent_absent_qs)
    context['analytics_subjects'] = analytics_subjects

    # Pass full student list + per-student subject breakdown for the new students pane
    # Build internal marks map: {student_id: {subject_id: InternalMark}}
    im_qs = InternalMark.objects.filter(subject_id__in=subject_ids).values(
        'student_id', 'subject_id', 'ia1', 'ia2', 'assignment_marks', 'attendance_marks'
    )
    stu_im_map = {}
    for im in im_qs:
        stu_im_map.setdefault(im['student_id'], {})[im['subject_id']] = im

    context['analytics_students'] = sorted(analytics_students, key=lambda x: (x['student'].current_semester, x['student'].section or '', x['student'].roll_number))
    context['stu_subj_att_map'] = stu_subj_map
    context['stu_marks_map'] = stu_marks_map
    context['stu_im_map'] = stu_im_map
    context['fac_subjects'] = subjects
    context['notifications'] = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:20]

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
def _get_section_students(faculty, subject):
    """
    Returns the queryset of students this faculty should see for a subject.
    If a SectionSubjectFacultyMap exists for this faculty+subject, scope to that section.
    Otherwise fall back to all active students in the department+semester.
    """
    ssf = SectionSubjectFacultyMap.objects.filter(faculty=faculty, subject=subject).select_related('section').first()
    base_qs = Student.objects.filter(
        department=subject.department,
        current_semester=subject.semester,
        status='ACTIVE',
        is_deleted=False,
    ).select_related('user').order_by('roll_number')
    if ssf:
        return base_qs.filter(section=ssf.section.label)
    return base_qs


def faculty_mark_attendance(request, subject_id):
    """
    Mark attendance for a subject session.
    - Topic covered is REQUIRED for every session (not just substitutions).
    - Lesson plan topics are passed as quick-select chips.
    - Substitution sessions show a banner and also save topic to Substitution record.
    - Existing attendance pre-filled when re-opening a session.
    """
    subject = get_object_or_404(Subject, pk=subject_id)

    try:
        faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        faculty = None

    allowed, msg = _check_attendance_permission(request.user, subject)
    if not allowed:
        messages.error(request, msg)
        return redirect('faculty_dashboard')
    if msg:
        messages.info(request, msg)

    students = _get_section_students(faculty, subject)
    today = timezone.localdate()

    # Check for accepted substitution today — look up by subject+faculty+date directly
    # (do NOT filter by day_of_week; the sub slot may be from a different weekday)
    active_sub = None
    if faculty:
        active_sub = Substitution.objects.filter(
            timetable_slot__subject=subject,
            substitute_faculty=faculty,
            date=today,
            status='ACCEPTED',
        ).select_related('timetable_slot').first()

    # Existing session for today (pre-fill topic + attendance)
    existing_session = AttendanceSession.objects.filter(subject=subject, date=today).first()

    # Lesson plan topics → quick-select chips
    topic_suggestions = []
    if faculty:
        for lp in LessonPlan.objects.filter(subject=subject, faculty=faculty).order_by('unit_number', 'planned_date'):
            if lp.topics:
                for t in lp.topics.split(','):
                    t = t.strip()
                    if t:
                        topic_suggestions.append(f"Unit {lp.unit_number} — {t}")
            else:
                topic_suggestions.append(f"Unit {lp.unit_number} — {lp.unit_title}")

    # Pre-fill existing attendance statuses
    existing_att = {}
    if existing_session:
        existing_att = {
            a.student_id: a.status
            for a in Attendance.objects.filter(session=existing_session)
        }

    if request.method == 'POST':
        date_str = request.POST.get('date', str(today))
        try:
            session_date = datetime.fromisoformat(date_str).date()
        except (ValueError, TypeError):
            session_date = today

        if session_date > today:
            messages.error(request, 'Cannot mark attendance for a future date.')
            return redirect('faculty_dashboard')

        topic_covered = request.POST.get('topic_covered', '').strip()
        if not topic_covered:
            prior_session = AttendanceSession.objects.filter(subject=subject, date=session_date).first()
            topic_covered = (
                (prior_session.topic_covered if prior_session else '')
                or (active_sub.topic_covered if active_sub else '')
                or (topic_suggestions[0] if topic_suggestions else '')
                or f'Attendance session for {subject.code}'
            )

        # Always store topic on the session
        session, created = AttendanceSession.objects.update_or_create(
            subject=subject,
            date=session_date,
            defaults={'faculty': faculty, 'topic_covered': topic_covered},
        )

        # Mirror topic on substitution record
        if active_sub:
            active_sub.topic_covered = topic_covered
            active_sub.save(update_fields=['topic_covered'])

        saved_count = 0
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'ABSENT')
            if status not in {'PRESENT', 'ABSENT', 'LATE'}:
                status = 'ABSENT'
            Attendance.objects.update_or_create(
                session=session, student=student,
                defaults={'status': status, 'marked_by': request.user},
            )
            saved_count += 1

        verb = 'marked' if created else 'updated'
        messages.success(
            request,
            f'Attendance {verb} for {subject.name} on {session_date} '
            f'({saved_count} students). Topic: {topic_covered}'
        )
        return redirect('faculty_dashboard')

    context = {
        'subject': subject,
        'students': students,
        'today': today,
        'active_sub': active_sub,
        'topic_suggestions': topic_suggestions,
        'existing_session': existing_session,
        'existing_att': existing_att,
    }
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
    students = _get_section_students(faculty, subject)
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


# ── SEMESTER RESULT HELPERS ──────────────────────────────────────────────────

def _format_academic_year(value):
    year = _safe_int(value, default=0)
    if year <= 0:
        return ''
    return f"{year}-{str(year + 1)[-2:]}"


def _parse_academic_year_start(value):
    if not value:
        return None
    raw = str(value).strip()
    head = raw.split('-', 1)[0].strip()
    return _safe_int(head, default=None)


def _get_semester_result_academic_year_options(college):
    years = set()
    for year in Student.objects.filter(department__college=college, is_deleted=False).values_list('admission_year', flat=True).distinct():
        formatted = _format_academic_year(year)
        if formatted:
            years.add(formatted)
    for year in SemesterResultBatch.objects.filter(college=college).values_list('academic_year', flat=True).distinct():
        formatted = str(year or '').strip()
        if formatted:
            years.add(formatted)
    return sorted(years, reverse=True)


def _get_semester_result_students(college, department, semester, academic_year):
    start_year = _parse_academic_year_start(academic_year)
    qs = Student.objects.select_related('user', 'department').filter(
        department=department,
        department__college=college,
        current_semester=semester,
        status='ACTIVE',
    ).order_by('roll_number')
    if start_year:
        qs = qs.filter(admission_year=start_year)
    return qs


def _get_semester_result_subjects(department, semester, academic_year):
    base_qs = Subject.objects.filter(department=department, semester=semester).order_by('code', 'name', 'id')
    subject_field_names = {field.name for field in Subject._meta.get_fields()}
    if 'academic_year' in subject_field_names:
        scoped_qs = base_qs.filter(Q(academic_year=academic_year) | Q(academic_year=''))
        return scoped_qs if scoped_qs.exists() else base_qs
    return base_qs


def _semester_result_fixed_headers():
    return ['roll_number', 'username', 'first_name', 'last_name', 'academic_year', 'department_code', 'semester']


def _semester_result_subject_headers(subjects):
    return [f"{subject.code} - {subject.name}" for subject in subjects]


def _build_semester_result_preview_pdf(batch):
    from io import BytesIO
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors

    styles, PRIMARY, DARK, MUTED = _get_pdf_styles()
    batch = SemesterResultBatch.objects.select_related('college', 'department').prefetch_related(
        'student_results__student__user',
        'student_results__student__department',
        'student_results__subjects__subject',
    ).get(pk=batch.pk)

    student_results = list(batch.student_results.all().order_by('student__roll_number'))
    combined_buf = BytesIO()
    combined_doc = SimpleDocTemplate(combined_buf, pagesize=A4,
                                     leftMargin=12*mm, rightMargin=12*mm,
                                     topMargin=10*mm, bottomMargin=10*mm)
    combined_elements = []
    pdf_map = {}

    for index, transcript in enumerate(student_results):
        student = transcript.student
        subjects = list(transcript.subjects.all().order_by('display_order', 'subject_code_snapshot'))
        student_name = student.user.get_full_name() or transcript.full_name_snapshot or transcript.username_snapshot

        elements = []
        _build_pdf_header(elements, batch.college, 'SEMESTER TRANSCRIPT',
                          f'{batch.academic_year} | {batch.department.code} | Semester {batch.semester}',
                          styles=styles, PRIMARY=PRIMARY)
        elements.append(Spacer(1, 8))

        info_table = Table([
            [Paragraph('Name', styles['FieldLabel']), Paragraph(student_name, styles['FieldValue']),
             Paragraph('Roll No.', styles['FieldLabel']), Paragraph(transcript.roll_number_snapshot, styles['FieldValue'])],
            [Paragraph('Department', styles['FieldLabel']), Paragraph(student.department.name, styles['FieldValue']),
             Paragraph('Branch', styles['FieldLabel']), Paragraph(batch.department.code, styles['FieldValue'])],
            [Paragraph('Semester', styles['FieldLabel']), Paragraph(str(batch.semester), styles['FieldValue']),
             Paragraph('Academic Year', styles['FieldLabel']), Paragraph(batch.academic_year, styles['FieldValue'])],
        ], colWidths=['20%', '30%', '20%', '30%'])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#dbe4ea')),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#dbe4ea')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 10))

        subject_rows = [[
            Paragraph('<b>Subject</b>', styles['TableHeader']),
            Paragraph('<b>Marks</b>', styles['TableHeader']),
            Paragraph('<b>Grade</b>', styles['TableHeader']),
            Paragraph('<b>Status</b>', styles['TableHeader']),
            Paragraph('<b>Credits</b>', styles['TableHeader']),
        ]]
        for sr in subjects:
            subject_rows.append([
                Paragraph(f"{sr.subject_code_snapshot} - {sr.subject_name_snapshot}", styles['TableCell']),
                Paragraph(f"{sr.marks_obtained:.0f}/{sr.max_marks:.0f}", styles['TableCell']),
                Paragraph(sr.grade or 'NA', styles['TableCell']),
                Paragraph(sr.status, styles['TableCell']),
                Paragraph(str(sr.credits), styles['TableCell']),
            ])
        subject_table = Table(subject_rows, colWidths=['44%', '14%', '12%', '16%', '14%'])
        subject_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d7377')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#dbe4ea')),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e5edf2')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
            ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(subject_table)
        elements.append(Spacer(1, 10))

        summary_table = Table([
            [Paragraph('Semester SGPA', styles['FieldLabel']), Paragraph(f"{transcript.sgpa:.2f}", styles['FieldValue']),
             Paragraph('Overall CGPA', styles['FieldLabel']), Paragraph(f"{transcript.cgpa:.2f}", styles['FieldValue'])],
            [Paragraph('Semester Credits', styles['FieldLabel']), Paragraph(str(transcript.semester_credits), styles['FieldValue']),
             Paragraph('Overall Credits', styles['FieldLabel']), Paragraph(str(transcript.overall_credits), styles['FieldValue'])],
            [Paragraph('Status', styles['FieldLabel']), Paragraph(transcript.result_status, styles['FieldValue']),
             Paragraph('Percentage', styles['FieldLabel']), Paragraph(f"{transcript.percentage:.2f}%", styles['FieldValue'])],
        ], colWidths=['22%', '28%', '22%', '28%'])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#dbe4ea')),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#dbe4ea')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(summary_table)

        student_buf = BytesIO()
        student_doc = SimpleDocTemplate(student_buf, pagesize=A4,
                                        leftMargin=12*mm, rightMargin=12*mm,
                                        topMargin=10*mm, bottomMargin=10*mm)
        student_doc.build(list(elements))
        pdf_map[transcript.pk] = student_buf.getvalue()

        combined_elements.extend(elements)
        if index != len(student_results) - 1:
            combined_elements.append(PageBreak())

    combined_doc.build(combined_elements)
    return combined_buf.getvalue(), pdf_map


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
def faculty_quiz_toggle(request, pk):
    """Toggle quiz active/inactive from the dashboard modal."""
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    if request.method == 'POST':
        quiz.is_active = not quiz.is_active
        quiz.save(update_fields=['is_active'])
        state = 'activated' if quiz.is_active else 'deactivated'
        messages.success(request, f'Quiz "{quiz.title}" {state}.')
    return redirect(f"{reverse('faculty_dashboard')}#subjects")


@login_required
def faculty_quiz_add_question_inline(request, pk):
    """Add a question to an existing quiz from the dashboard modal."""
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    if request.method != 'POST':
        return redirect(f"{reverse('faculty_dashboard')}#subjects")
    q_text = request.POST.get('question_text', '').strip()
    if not q_text:
        messages.error(request, 'Question text is required.')
        return redirect(f"{reverse('faculty_dashboard')}#subjects")
    question = QuizQuestion.objects.create(
        quiz=quiz,
        question_text=q_text,
        question_type='MCQ',
        marks=_safe_float(request.POST.get('marks'), 1),
    )
    correct = _safe_int(request.POST.get('correct_option'), 1)
    for i in range(1, 5):
        opt_text = request.POST.get(f'opt{i}', '').strip()
        if opt_text:
            QuizOption.objects.create(
                question=question,
                option_text=opt_text,
                is_correct=(i == correct),
            )
    messages.success(request, f'Question added to "{quiz.title}".')
    return redirect(f"{reverse('faculty_dashboard')}#subjects")


@login_required
def faculty_quiz_delete_question(request, pk):
    """Delete a quiz question from the dashboard modal."""
    question = get_object_or_404(QuizQuestion, pk=pk, quiz__created_by=request.user)
    if request.method == 'POST':
        quiz_title = question.quiz.title
        question.delete()
        messages.success(request, f'Question deleted from "{quiz_title}".')
    return redirect(f"{reverse('faculty_dashboard')}#subjects")


def _import_quiz_questions_from_csv(quiz, file_obj):
    """
    Import questions from a CSV template into a quiz.
    Expected columns: question_text, option1, option2, option3, option4, correct_option (1-4), marks
    """
    try:
        import io
        decoded = file_obj.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))
        for row in reader:
            q_text = (row.get('question_text') or row.get('Question') or '').strip()
            if not q_text:
                continue
            correct_raw = (row.get('correct_option') or row.get('Correct') or '1').strip()
            try:
                correct_num = int(correct_raw)
            except ValueError:
                correct_num = 1
            marks = _safe_float(row.get('marks') or row.get('Marks'), 1)
            question = QuizQuestion.objects.create(
                quiz=quiz, question_text=q_text, question_type='MCQ', marks=marks,
            )
            for i in range(1, 5):
                opt = (row.get(f'option{i}') or row.get(f'Option{i}') or '').strip()
                if opt:
                    QuizOption.objects.create(
                        question=question, option_text=opt, is_correct=(i == correct_num),
                    )
    except Exception:
        pass  # Silently skip bad rows — user can add manually


@login_required
def faculty_quiz_create_inline(request, subject_id):
    faculty = get_object_or_404(Faculty, user=request.user)
    get_object_or_404(FacultySubject, faculty=faculty, subject_id=subject_id)
    if request.method != 'POST':
        return redirect(f"{reverse('faculty_dashboard')}#subjects")
    title = request.POST.get('title', '').strip()
    if not title:
        messages.error(request, 'Quiz title is required.')
        return redirect(f"{reverse('faculty_dashboard')}#subjects")

    start_raw = request.POST.get('start_time', '').strip()
    end_raw = request.POST.get('end_time', '').strip()
    start_dt = _assignment_deadline_from_input(start_raw) if start_raw else None
    end_dt = _assignment_deadline_from_input(end_raw) if end_raw else None

    quiz = Quiz.objects.create(
        subject_id=subject_id,
        created_by=request.user,
        title=title,
        description=request.POST.get('description', '').strip(),
        duration_minutes=_safe_int(request.POST.get('duration_minutes'), 30),
        total_marks=_safe_float(request.POST.get('total_marks'), 10),
        start_time=start_dt,
        end_time=end_dt,
        access_password=request.POST.get('access_password', '').strip(),
        questions_per_student=_safe_int(request.POST.get('questions_per_student'), 0) or None,
        is_active=False,
    )

    # Handle template file upload (CSV with questions)
    template_file = request.FILES.get('template_file')
    if template_file:
        quiz.template_file = template_file
        quiz.save(update_fields=['template_file'])
        _import_quiz_questions_from_csv(quiz, template_file)

    # Inline questions
    questions_added = 0
    for i in range(1, 51):
        q_text = request.POST.get(f'q{i}_text', '').strip()
        if not q_text:
            continue
        question = QuizQuestion.objects.create(
            quiz=quiz, question_text=q_text, question_type='MCQ',
            marks=_safe_float(request.POST.get(f'q{i}_marks'), 1),
        )
        for opt_num in range(1, 5):
            opt_text = request.POST.get(f'q{i}_opt{opt_num}', '').strip()
            if opt_text:
                QuizOption.objects.create(
                    question=question, option_text=opt_text,
                    is_correct=(request.POST.get(f'q{i}_correct') == str(opt_num)),
                )
        questions_added += 1

    if questions_added > 0 or quiz.questions.exists():
        quiz.is_active = True
        quiz.save(update_fields=['is_active'])
        messages.success(request, f'Quiz "{quiz.title}" created with {quiz.questions.count()} questions.')
    else:
        messages.success(request, f'Quiz "{quiz.title}" created — add questions via Edit to activate.')

    return redirect(f"{reverse('faculty_dashboard')}#subjects")


@login_required
def faculty_assignment_create_inline(request, subject_id):
    """Create an assignment inline from the My Subjects dashboard tab."""
    faculty = get_object_or_404(Faculty, user=request.user)
    get_object_or_404(FacultySubject, faculty=faculty, subject_id=subject_id)
    if request.method != 'POST':
        return redirect(f"{reverse('faculty_dashboard')}#subjects")
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()
    deadline_value = request.POST.get('deadline', '').strip()
    if not title or not deadline_value:
        messages.error(request, 'Title and deadline are required.')
        return redirect(f"{reverse('faculty_dashboard')}#subjects")
    Assignment.objects.create(
        subject_id=subject_id,
        title=title,
        description=description,
        deadline=_assignment_deadline_from_input(deadline_value),
        created_by=request.user,
        submission_type=request.POST.get('submission_type', 'ONLINE'),
        max_marks=_safe_float(request.POST.get('max_marks'), 10),
    )
    messages.success(request, f'Assignment "{title}" created.')
    return redirect(f"{reverse('faculty_dashboard')}#subjects")


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

        elif action == 'upload_csv':
            csv_file = request.FILES.get('csv_file')
            if csv_file:
                _import_quiz_questions_from_csv(quiz, csv_file)
                messages.success(request, f'Questions imported from CSV into "{quiz.title}".')
            else:
                messages.error(request, 'Please select a CSV file.')

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

    students = _get_section_students(faculty, subject)
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


@login_required
def faculty_ce_marks_inline(request, subject_id):
    """Save CE marks inline from the My Subjects dashboard — no page navigation."""
    faculty = get_object_or_404(Faculty, user=request.user)
    get_object_or_404(FacultySubject, faculty=faculty, subject_id=subject_id)
    subject = get_object_or_404(Subject, pk=subject_id)
    if request.method != 'POST':
        return redirect(f"{reverse('faculty_dashboard')}#subjects")

    students = _get_section_students(faculty, subject)
    with transaction.atomic():
        for student in students:
            def _fv(key, max_val):
                v = request.POST.get(f'{key}_{student.id}', '').strip()
                if not v: return None
                try: val = float(v)
                except ValueError: return None
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
    messages.success(request, f'CE marks saved for {subject.name}.')
    return redirect(f"{reverse('faculty_dashboard')}#subjects")


@login_required
def faculty_submit_ce_marks(request, subject_id):
    """Faculty submits CE marks for a subject to the HOD for review."""
    faculty = get_object_or_404(Faculty, user=request.user)
    get_object_or_404(FacultySubject, faculty=faculty, subject_id=subject_id)
    subject = get_object_or_404(Subject, pk=subject_id)

    if request.method != 'POST':
        return redirect('faculty_dashboard')

    # Check if already submitted and pending
    existing = HODApproval.objects.filter(
        requested_by=request.user,
        approval_type='CE_MARKS',
        subject=subject,
        status='PENDING',
    ).first()
    if existing:
        messages.warning(request, f'CE marks for {subject.name} are already submitted and pending HOD review.')
        return redirect(f"{reverse('faculty_dashboard')}#subjects")

    # Count how many students have marks entered (scoped to faculty's section)
    students = _get_section_students(faculty, subject)
    filled = InternalMark.objects.filter(subject=subject, student__in=students).count()
    total = students.count()

    if filled == 0:
        messages.error(request, f'No CE marks entered for {subject.name} yet. Enter marks before submitting.')
        return redirect(f"{reverse('faculty_dashboard')}#subjects")

    HODApproval.objects.create(
        requested_by=request.user,
        department=subject.department,
        subject=subject,
        approval_type='CE_MARKS',
        description=(
            f'CE marks submission for {subject.name} ({subject.code}) — '
            f'Semester {subject.semester}. '
            f'{filled}/{total} students have marks entered.'
        ),
    )

    # Notify HOD
    try:
        hod = HOD.objects.filter(department=subject.department, is_active=True).first()
        if hod:
            Notification.objects.create(
                user=hod.user,
                message=(
                    f'{request.user.get_full_name() or request.user.username} has submitted '
                    f'CE marks for {subject.name} (Sem {subject.semester}) for your review.'
                ),
            )
    except Exception:
        pass

    messages.success(request, f'CE marks for {subject.name} submitted to HOD for review.')
    return redirect(f"{reverse('faculty_dashboard')}#subjects")


# ── FACULTY: ATTENDANCE DEFAULTERS ───────────────────────────────────────────

@login_required
def faculty_attendance_defaulters(request, subject_id):
    """Show students below the configured attendance threshold for a subject."""
    faculty = get_object_or_404(Faculty, user=request.user)
    subject = get_object_or_404(Subject, pk=subject_id)

    att_rule = _get_attendance_rule(subject.department.college, subject.department, subject.semester)
    threshold = att_rule.effective_min_subject

    students = _get_section_students(faculty, subject)

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
        return redirect(f'/dashboard/faculty/#subjects')

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
                days_requested = max((td - fd).days + 1, 1)
                # Check quota
                college_l = faculty.department.college
                fcfg = CollegeFeatureConfig.objects.filter(college=college_l).first()
                quota_map = {
                    'CL': fcfg.max_casual_leaves  if fcfg else 12,
                    'ML': fcfg.max_medical_leaves if fcfg else 10,
                    'EL': fcfg.max_earned_leaves  if fcfg else 15,
                    'OD': fcfg.max_od_leaves      if fcfg else 20,
                }
                max_days = quota_map.get(leave_type, 12)
                used_days = sum(
                    max((l.to_date - l.from_date).days + 1, 1)
                    for l in LeaveApplication.objects.filter(
                        faculty=faculty, leave_type=leave_type,
                        from_date__year=fd.year, status__in=['APPROVED', 'PENDING']
                    )
                )
                if used_days + days_requested > max_days:
                    messages.error(request, f'Leave quota exceeded. You have {max(max_days - used_days, 0)} {leave_type} days remaining.')
                elif fd < timezone.now().date():
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
                    # Notify HOD
                    hod = HOD.objects.filter(department=faculty.department, is_active=True).first()
                    if hod:
                        Notification.objects.create(
                            user=hod.user,
                            message=(
                                f'{request.user.get_full_name() or request.user.username} has submitted a '
                                f'{dict(LeaveApplication.LEAVE_TYPES).get(leave_type, leave_type)} '
                                f'from {from_date} to {to_date}. Please review in your dashboard.'
                            )
                        )
                    messages.success(request, 'Leave application submitted to HOD.')
                    return redirect(f"{reverse('faculty_dashboard')}#leave")
        elif action == 'cancel':
            LeaveApplication.objects.filter(
                pk=request.POST.get('leave_id'), faculty=faculty, status='PENDING'
            ).delete()
            messages.success(request, 'Application withdrawn.')
            return redirect(f"{reverse('faculty_dashboard')}#leave")

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
    # Count only subjects that have at least one session recorded
    tracked_subjects_count = sum(1 for a in attendance_data if a['total'] > 0)

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

    backlog_data = _build_active_backlog_groups(student)
    active_backlogs = backlog_data['active_backlogs']
    backlog_count = backlog_data['backlog_count']

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

    # Academic concern here is based on academic records only. Attendance has its own tab.
    on_probation = backlog_count > 2 or (cgpa is not None and cgpa < 5.0)

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
    announcements = _scope_announcements_for_college(student.department.college, target='students').order_by('-created_at')[:20]

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

    # Past semesters summary — padded list for attendance stat boxes (most recent first)
    db_stats = {row['semester']: row['pct'] for row in att_by_semester}
    past_semesters_summary = []
    if student.current_semester > 1:
        for sem in range(student.current_semester - 1, 0, -1):
            past_semesters_summary.append({
                'semester': sem,
                'pct': db_stats.get(sem, None),
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

    current_semester_credits = sum(s.credits or 0 for s in course_subjects)
    passed_marks = Marks.objects.filter(student=student).exclude(grade='F').select_related('subject')
    earned_subject_ids = set()
    earned_credits = 0
    for mark in passed_marks:
        if mark.subject_id not in earned_subject_ids:
            earned_subject_ids.add(mark.subject_id)
            earned_credits += mark.subject.credits or 0
    academic_credit_summary = {
        'current_semester_credits': current_semester_credits,
        'earned_credits': earned_credits,
        'passed_subjects': len(earned_subject_ids),
        'current_subjects': course_subjects.count(),
    }

    current_subject_ids = list(course_subjects.values_list('id', flat=True))
    current_faculty_ids = list(FacultySubject.objects.filter(subject_id__in=current_subject_ids).values_list('faculty_id', flat=True))
    submitted_feedback_ids = set(FacultyFeedbackResponse.objects.filter(student=student).values_list('cycle_id', flat=True))
    pending_feedback = FacultyFeedbackCycle.objects.filter(
        college=college,
        is_active=True,
        start_date__lte=today,
        end_date__gte=today,
    ).filter(
        Q(department__isnull=True) | Q(department=student.department),
        Q(semester__isnull=True) | Q(semester=student.current_semester),
        Q(subject__isnull=True) | Q(subject_id__in=current_subject_ids),
        Q(faculty__isnull=True) | Q(faculty_id__in=current_faculty_ids),
    ).exclude(id__in=submitted_feedback_ids).select_related('subject', 'faculty__user').order_by('end_date')
    submitted_feedback = FacultyFeedbackResponse.objects.filter(student=student).select_related(
        'cycle__subject', 'cycle__faculty__user'
    ).order_by('-submitted_at')[:5]

    # Full student payment history: semester fees + supply/revaluation payments
    all_payments = Payment.objects.filter(
        user=user,
        status='SUCCESS',
    ).select_related('fee').order_by('paid_at', 'created_at')
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

    # Fee components for inline payment panel in dashboard
    from django.conf import settings as _ds
    _razorpay_enabled = bool(getattr(_ds, 'RAZORPAY_KEY_ID', '') and getattr(_ds, 'RAZORPAY_KEY_SECRET', ''))
    _razorpay_key_id  = getattr(_ds, 'RAZORPAY_KEY_ID', '')
    _fee_structure = FeeStructure.objects.filter(
        department=student.department,
        semester=fee.semester or student.current_semester
    ).first() if fee else None
    _fee_breakdown_map = {}
    if _fee_structure:
        for bd in _fee_structure.breakdowns.all():
            _fee_breakdown_map[bd.category] = bd.amount
    _DEFAULT_AMOUNTS = {'TUITION': fee.total_amount if fee else 0, 'EXAM': 1500.0, 'LIBRARY': 500.0, 'SPORTS': 500.0, 'MISC': 0.0}
    _merged = {**_DEFAULT_AMOUNTS, **_fee_breakdown_map}
    _LABELS = {'TUITION': 'Tuition Fee', 'EXAM': 'Exam Fee', 'LIBRARY': 'Library Fee', 'SPORTS': 'Sports & Cultural Fee', 'MISC': 'Miscellaneous'}
    fee_components_display = [
        (k, _LABELS[k], _merged.get(k, 0))
        for k in _LABELS
        if k != 'TUITION' and _merged.get(k, 0) > 0
    ]

    # Academic track — CGPA per semester
    semester_results = results.order_by('semester')
    approved_transcripts_qs = (
        SemesterResultStudent.objects.filter(
            student=student,
            status='APPROVED',
            batch__status='APPROVED',
        )
        .select_related('batch')
        .order_by('-batch__semester', '-approved_at', '-id')
    )
    approved_transcripts = []
    seen_transcript_semesters = set()
    for transcript in approved_transcripts_qs:
        if transcript.batch.semester in seen_transcript_semesters:
            continue
        seen_transcript_semesters.add(transcript.batch.semester)
        approved_transcripts.append(transcript)

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

    # ── My Courses: per-subject data for current semester ────────────────────
    all_sem_assignments = (
        Assignment.objects.filter(
            subject__department=student.department,
            subject__semester=student.current_semester,
            is_published=True,
        ).select_related('subject').order_by('subject_id', 'deadline')
    )
    my_submissions_map = {
        sub.assignment_id: sub
        for sub in AssignmentSubmission.objects.filter(
            student=student,
            assignment__subject__semester=student.current_semester,
        ).select_related('assignment')
    }
    all_sem_quizzes = (
        Quiz.objects.filter(
            subject__department=student.department,
            subject__semester=student.current_semester,
            is_active=True,
        ).select_related('subject').order_by('subject_id', '-created_at')
    )
    my_quiz_attempts_map = {
        att.quiz_id: att
        for att in QuizAttempt.objects.filter(
            student=student,
            quiz__subject__semester=student.current_semester,
            is_submitted=True,
        ).select_related('quiz')
    }
    lesson_plans_qs = LessonPlan.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
    ).select_related('subject').order_by('subject_id', 'planned_date')
    lesson_plans_map = {}
    for lp in lesson_plans_qs:
        lesson_plans_map.setdefault(lp.subject_id, []).append(lp)

    my_courses = []
    for subj in course_subjects:
        faculty_names = [
            fs.faculty.user.get_full_name() or fs.faculty.user.username
            for fs in subj.facultysubject_set.all()
        ]
        my_courses.append({
            'subject': subj,
            'faculty': faculty_names,
            'assignments': [a for a in all_sem_assignments if a.subject_id == subj.id],
            'quizzes': [q for q in all_sem_quizzes if q.subject_id == subj.id],
            'internal_mark': internal_map.get(subj.id),
            'lesson_plans': lesson_plans_map.get(subj.id, []),
            'submissions_map': my_submissions_map,
            'quiz_attempts_map': my_quiz_attempts_map,
        })

    context = {
        'student': student,
        'college': student.department.college,
        'profile': profile,
        'address': address,
        'parent': parent,
        'emergency_contact': emergency_contact,
        'attendance_data': attendance_data,
        'overall_attendance': overall_attendance,
        'tracked_subjects_count': tracked_subjects_count,
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
        'approved_transcripts': approved_transcripts,
        'subjects': subjects,
        'branding': _get_college_branding(student.department.college),
        'now': timezone.now(),
        'all_internal_by_sem': all_internal_by_sem,
        'all_internal_semesters': all_internal_semesters,
        'all_internal_list': all_internal_list,
        'att_by_semester': att_by_semester,
        'past_semesters_summary': past_semesters_summary,
        'all_att_records': all_att_records,
        'eligibility': eligibility,
        'att_rule': att_rule,
        'assignment_score_trend': assignment_score_trend,
        'academic_credit_summary': academic_credit_summary,
        'pending_feedback': pending_feedback,
        'submitted_feedback': submitted_feedback,
        'fee_timeline': fee_timeline,
        'backlog_count': backlog_count,
        'year_of_study': year_of_study,
        'academic_standing': academic_standing,
        'on_probation': on_probation,
        'all_fees': all_fees,
        'total_fees_due': total_fees_due,
        'paid_fee_types': paid_fee_types,
        'fee_components_display': fee_components_display,
        'razorpay_enabled': _razorpay_enabled,
        'razorpay_key_id': _razorpay_key_id,
        'my_courses': my_courses,
    }

    # ── Course Registration (Electives) ──────────────────────────────────────
    feature_cfg = CollegeFeatureConfig.objects.filter(college=college).first()
    feature_disabled = feature_cfg and not feature_cfg.enable_electives

    # Course registration window — admin-controlled
    course_reg_open = bool(feature_cfg and feature_cfg.course_registration_open)
    course_reg_semester = feature_cfg.course_registration_semester if feature_cfg else None

    if not feature_disabled:
        open_pools = ElectivePool.objects.filter(
            department=student.department,
            semester=student.current_semester,
            status='OPEN',
        ).prefetch_related('subjects')
        my_sel_qs = ElectiveSelection.objects.filter(
            student=student, pool__in=open_pools
        ).select_related('subject', 'pool')
        sel_by_pool = {s.pool_id: s for s in my_sel_qs}
        pool_data = [{'pool': p, 'selection': sel_by_pool.get(p.pk)} for p in open_pools]
        my_selections = list(my_sel_qs)
    else:
        pool_data = []
        my_selections = []

    # All subjects for the registration semester (for the full course list view)
    reg_sem = course_reg_semester or student.current_semester
    all_reg_subjects = Subject.objects.filter(
        department=student.department,
        semester=reg_sem,
    ).order_by('category', 'name') if course_reg_open else []

    context['pool_data'] = pool_data
    context['my_selections'] = my_selections
    context['feature_disabled'] = feature_disabled
    context['course_reg_open'] = course_reg_open
    context['course_reg_semester'] = reg_sem
    context['all_reg_subjects'] = all_reg_subjects

    # ── Supply Exam ───────────────────────────────────────────────────────────
    # Only show supply/backlog exams — exclude the student's current semester end exam
    # A supply exam is one whose semester < student's current semester (backlog semesters)
    supply_latest_exam = Exam.objects.filter(
        college=college,
        semester__lt=student.current_semester,  # only past semesters = supply/backlog
    ).order_by('-end_date').first()
    supply_fee_per_subject = _get_supply_fee_per_subject(college, student.department, student.current_semester)

    supply_backlog_grouped = backlog_data['supply_backlog_grouped']

    supply_existing_reg = None
    supply_existing_reg_matches_current = False
    if supply_latest_exam:
        supply_existing_reg = SupplyExamRegistration.objects.filter(
            student=student, exam=supply_latest_exam
        ).first()
        supply_existing_reg_matches_current = _paid_supply_registration_matches(
            supply_existing_reg,
            backlog_data['failed_subject_ids'],
        )

    context['supply_latest_exam'] = supply_latest_exam
    context['supply_fee_per_subject'] = supply_fee_per_subject
    context['supply_backlog_grouped'] = supply_backlog_grouped
    context['supply_existing_reg'] = supply_existing_reg
    context['supply_existing_reg_matches_current'] = supply_existing_reg_matches_current

    # ── Hall Tickets ──────────────────────────────────────────────────────────
    student_hall_tickets = HallTicket.objects.filter(
        student=student
    ).select_related('exam').order_by('-exam__start_date')
    context['student_hall_tickets'] = student_hall_tickets
    context['total_semester_credits'] = sum(s.credits or 0 for s in course_subjects)

    resp = render(request, 'dashboards/student.html', context)
    resp['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp


@login_required
def student_profile_edit(request):
    """
    Student profile edit — inline form posted from the dashboard #profile section.
    Rules:
      - Editable: first_name, last_name, email, phone_number (max 10 digits),
                  date_of_birth, gender, blood_group, nationality, profile_photo,
                  address fields, emergency contact
      - Read-only (admin only): aadhaar_number, parent phone, parent name, parent type
    """
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
                # ── User fields — first_name/last_name are read-only for student ─
                # Only phone is editable from user-facing fields
                request.user.save()

                # ── Phone validation (max 10 digits) ──────────────────────────
                phone = request.POST.get('phone_number', '').strip()
                digits_only = ''.join(c for c in phone if c.isdigit())
                if len(digits_only) > 10:
                    messages.error(request, 'Phone number must be at most 10 digits.')
                    return redirect(f"{reverse('student_dashboard')}#profile")

                alt_phone = request.POST.get('alternate_phone', '').strip()
                alt_digits = ''.join(c for c in alt_phone if c.isdigit())
                if len(alt_digits) > 10:
                    messages.error(request, 'Alternate phone must be at most 10 digits.')
                    return redirect(f"{reverse('student_dashboard')}#profile")

                # ── Profile — keep all admin-managed fields from existing record ─
                existing_aadhaar = profile.aadhaar_number if profile else ''
                profile_data = {
                    'date_of_birth': profile.date_of_birth if profile else None,  # read-only
                    'gender':        profile.gender if profile else '',            # read-only
                    'phone_number':  phone,
                    'alternate_phone': alt_phone,
                    'aadhaar_number': existing_aadhaar,
                    'blood_group':   profile.blood_group if profile else None,     # read-only
                    'nationality':   request.POST.get('nationality', '').strip() or 'Indian',
                    # keep education history unchanged
                    'inter_college_name':  profile.inter_college_name  if profile else '',
                    'inter_passed_year':   profile.inter_passed_year   if profile else 0,
                    'inter_percentage':    profile.inter_percentage     if profile else 0,
                    'school_name':         profile.school_name          if profile else '',
                    'school_passed_year':  profile.school_passed_year   if profile else 0,
                    'school_percentage':   profile.school_percentage     if profile else 0,
                    'category':            profile.category             if profile else None,
                    'college_email':       profile.college_email        if profile else None,  # read-only
                    'personal_email':      profile.personal_email       if profile else None,  # read-only
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

                # ── Address ───────────────────────────────────────────────────
                address_data = {
                    'street':  request.POST.get('street', '').strip(),
                    'city':    request.POST.get('city', '').strip(),
                    'state':   request.POST.get('state', '').strip(),
                    'pincode': request.POST.get('pincode', '').strip(),
                    'country': request.POST.get('country', '').strip() or 'India',
                }
                if address is None:
                    Address.objects.create(user=request.user, **address_data)
                else:
                    for field, value in address_data.items():
                        setattr(address, field, value)
                    address.save()

                # ── Parent details are managed only by college admin ───────────

                # ── Emergency contact ─────────────────────────────────────────
                emergency_data = {
                    'name':         request.POST.get('emergency_name', '').strip(),
                    'relation':     request.POST.get('emergency_relation', '').strip(),
                    'phone_number': request.POST.get('emergency_phone_number', '').strip(),
                }
                if emergency_contact is None:
                    EmergencyContact.objects.create(user=request.user, **emergency_data)
                else:
                    for field, value in emergency_data.items():
                        setattr(emergency_contact, field, value)
                    emergency_contact.save()

            messages.success(request, 'Profile updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')

        return redirect(f"{reverse('student_dashboard')}#profile")

    context = {
        'student': student,
        'profile': profile,
        'address': address,
        'parent': parent,
        'emergency_contact': emergency_contact,
    }
    return render(request, 'student/profile_form.html', context)


@login_required
def student_faculty_feedback_submit(request, cycle_id):
    try:
        student = Student.objects.select_related('department__college').get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Contact admin.')
        return redirect('home')

    today = timezone.localdate()
    course_subject_ids = list(Subject.objects.filter(
        department=student.department,
        semester=student.current_semester,
    ).values_list('id', flat=True))
    faculty_ids = list(FacultySubject.objects.filter(subject_id__in=course_subject_ids).values_list('faculty_id', flat=True))
    cycle = get_object_or_404(
        FacultyFeedbackCycle.objects.filter(
            college=student.department.college,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today,
        ).filter(
            Q(department__isnull=True) | Q(department=student.department),
            Q(semester__isnull=True) | Q(semester=student.current_semester),
            Q(subject__isnull=True) | Q(subject_id__in=course_subject_ids),
            Q(faculty__isnull=True) | Q(faculty_id__in=faculty_ids),
        ),
        pk=cycle_id,
    )

    if FacultyFeedbackResponse.objects.filter(cycle=cycle, student=student).exists():
        messages.info(request, 'You have already submitted this feedback.')
        return redirect(f"{reverse('student_dashboard')}#academic-track")

    if request.method == 'POST':
        ratings = {}
        for idx, question in enumerate(cycle.question_list, start=1):
            value = _safe_int(request.POST.get(f'question_{idx}'), default=0)
            if value < 1 or value > 5:
                messages.error(request, 'Please rate every question from 1 to 5.')
                return redirect('student_faculty_feedback_submit', cycle_id=cycle.pk)
            ratings[question] = value
        FacultyFeedbackResponse.objects.create(
            cycle=cycle,
            student=student,
            ratings=ratings,
            comments=request.POST.get('comments', '').strip(),
        )
        messages.success(request, 'Faculty feedback submitted. Thank you.')
        return redirect(f"{reverse('student_dashboard')}#academic-track")

    return render(request, 'student/faculty_feedback_form.html', {
        'student': student,
        'cycle': cycle,
        'questions': cycle.question_list,
        'college': student.department.college,
        'branding': _get_college_branding(student.department.college),
    })


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
    exam_fee_block_reason = _exam_fee_block_reason(student, fee)
    exam_fee_subjects = _current_semester_exam_subjects(student, fee)

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
        elif fee_type == 'EXAM' and exam_fee_block_reason:
            messages.error(request, exam_fee_block_reason)
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
        'exam_fee_block_reason': exam_fee_block_reason,
        'exam_fee_subjects': exam_fee_subjects,
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
    exam_fee_block_reason = _exam_fee_block_reason(student, fee)

    if amount <= 0:
        return JsonResponse({'error': 'Amount must be greater than zero'}, status=400)
    if fee_type == 'EXAM' and exam_fee_block_reason:
        return JsonResponse({'error': exam_fee_block_reason}, status=400)
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


def _current_semester_exam_subjects(student, fee=None):
    target_semester = getattr(fee, 'semester', None) or student.current_semester
    return list(
        Subject.objects.filter(
            department=student.department,
            semester=target_semester,
        ).order_by('code', 'name')
    )


def _exam_fee_block_reason(student, fee):
    if not student or not fee:
        return 'Exam fee record not found.'

    balance_due = max(Decimal(str(fee.total_amount)) - Decimal(str(fee.paid_amount)), Decimal('0'))
    if balance_due > 0:
        return f'Please clear the tuition balance of Rs {balance_due:.0f} before paying the exam fee.'

    semester = fee.semester or student.current_semester
    eligibility = _compute_eligibility(student, semester, student.department.college)
    subject_breakdown = eligibility.get('subject_breakdown') or []
    evaluated_subjects = [item for item in subject_breakdown if not item.get('skipped')]
    if not evaluated_subjects:
        return 'Exam fee payment is blocked until attendance is recorded for the current semester subjects.'
    if sum((item.get('total') or 0) for item in evaluated_subjects) <= 0:
        return 'Exam fee payment is blocked until attendance is recorded for the current semester subjects.'
    if not eligibility.get('eligible'):
        reasons = eligibility.get('reasons') or []
        reason_text = reasons[0] if reasons else 'Attendance eligibility is not yet satisfied for this semester.'
        return f'Exam fee payment is blocked until attendance is eligible. {reason_text}'

    return None


def _supply_registration_subject_ids(reg):
    if not reg:
        return set()
    return set(reg.subjects.values_list('id', flat=True))


def _paid_supply_registration_matches(reg, failed_subject_ids):
    """
    Treat a paid supply registration as complete only when it still matches the
    student's current active backlog subjects exactly.
    """
    if not reg or reg.status != 'PAID':
        return False
    return _supply_registration_subject_ids(reg) == set(failed_subject_ids)


def _paid_supply_registration_matches_selection(reg, selected_subject_ids):
    """
    Treat a paid supply registration as complete for a POST only when the
    student's submitted subject selection exactly matches the already-paid
    registration. This prevents stale paid registrations from blocking a new
    payment flow after the active backlog list changes.
    """
    if not reg or reg.status != 'PAID':
        return False
    return _supply_registration_subject_ids(reg) == set(selected_subject_ids)


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

    # Find the latest backlog/supply exam only for past semesters.
    latest_exam = Exam.objects.filter(
        college=college,
        semester__lt=student.current_semester,
    ).order_by('-end_date').first()

    backlog_data = _build_active_backlog_groups(student)
    failed_grouped = backlog_data['supply_backlog_grouped']
    all_failed_marks = backlog_data['all_failed_marks']
    failed_subject_ids = backlog_data['failed_subject_ids']

    fee_per_subject = _get_supply_fee_per_subject(college, student.department, student.current_semester)

    # Check existing registration
    existing_reg = None
    existing_reg_matches_current = False
    if latest_exam:
        existing_reg = SupplyExamRegistration.objects.filter(
            student=student, exam=latest_exam
        ).first()
        existing_reg_matches_current = _paid_supply_registration_matches(
            existing_reg,
            failed_subject_ids,
        )

    if request.method == 'POST' and latest_exam:
        subject_ids = request.POST.getlist('subjects')
        if not subject_ids:
            messages.error(request, 'Select at least one subject to register.')
        else:
            try:
                selected_subject_ids = {int(subject_id) for subject_id in subject_ids}
            except (TypeError, ValueError):
                messages.error(request, 'Invalid subject selection for supply registration.')
                return redirect('student_supply_exam_register')
            if _paid_supply_registration_matches_selection(existing_reg, selected_subject_ids):
                messages.info(request, 'You have already completed payment for this supply registration.')
                return redirect('student_dashboard')
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
        'existing_reg_matches_current': existing_reg_matches_current,
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
    return redirect('student_payment_receipt', pk=payment.pk)


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

    # Guard: result must be published before revaluation is allowed
    er = ExamResult.objects.filter(student=student, exam=marks.exam, status='PUBLISHED').first()
    if not er:
        messages.error(request, 'Results are not published yet. Revaluation is only available after results are published.')
        return redirect(f"{reverse('student_dashboard')}#results")

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
            'supply_registration__student__user',
            'supply_registration__student__department__college',
            'supply_registration__exam',
        ),
        pk=pk, user=request.user
    )
    fee = payment.fee
    supply_registration = getattr(payment, 'supply_registration', None)
    student = fee.student if fee else (supply_registration.student if supply_registration else Student.objects.filter(user=request.user).first())
    college = student.department.college if student else None
    branding = _get_college_branding(college)
    profile = getattr(student.user, 'studentprofile', None) if student else None
    balance_due = max(fee.total_amount - fee.paid_amount, 0) if fee else 0
    receipt_title = 'Payment Receipt'
    payment_context = None
    supply_subjects = []
    exam_subjects = []

    if payment.payment_type == 'SUPPLY_EXAM':
        receipt_title = 'Supply Exam Receipt'
        if supply_registration:
            supply_subjects = list(supply_registration.subjects.order_by('semester', 'code'))
            payment_context = {
                'label': 'Supply Exam',
                'value': supply_registration.exam.name,
            }
    elif payment.payment_type == 'REVALUATION':
        receipt_title = 'Revaluation Receipt'
        payment_context = {
            'label': 'Payment For',
            'value': 'Revaluation Request',
        }
    else:
        receipt_title = 'Fee Receipt'
        if payment.payment_type == 'EXAM' and fee and fee.semester:
            payment_context = {
                'label': 'Payment For',
                'value': f'Semester {fee.semester} Exam Fee',
            }
        elif fee and fee.semester:
            payment_context = {
                'label': 'Payment For',
                'value': f'Semester {fee.semester} Fee',
            }
        if payment.payment_type == 'EXAM' and student:
            exam_subjects = _current_semester_exam_subjects(student, fee)

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
        'receipt_title': receipt_title,
        'payment_context': payment_context,
        'supply_subjects': supply_subjects,
        'exam_subjects': exam_subjects,
    })


@login_required
def student_payment_receipt_pdf(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related(
            'fee__student__user',
            'fee__student__department__college',
            'supply_registration__student__user',
            'supply_registration__student__department__college',
            'supply_registration__exam',
        ),
        pk=pk, user=request.user
    )
    fee     = payment.fee
    supply_registration = getattr(payment, 'supply_registration', None)
    student = fee.student if fee else (supply_registration.student if supply_registration else Student.objects.filter(user=request.user).first())
    college = student.department.college if student else None
    profile = getattr(student.user, 'studentprofile', None) if student else None
    supply_subjects = list(supply_registration.subjects.order_by('semester', 'code')) if supply_registration else []
    exam_subjects = _current_semester_exam_subjects(student, fee) if payment.payment_type == 'EXAM' and student else []

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

    receipt_title = 'PAYMENT RECEIPT'
    if payment.payment_type == 'SUPPLY_EXAM':
        receipt_title = 'SUPPLY EXAM RECEIPT'
    elif payment.payment_type == 'REVALUATION':
        receipt_title = 'REVALUATION RECEIPT'
    elif payment.payment_type in {'TUITION', 'SEM_FEE', 'EXAM', 'LIBRARY', 'SPORTS', 'MISC'}:
        receipt_title = 'FEE RECEIPT'

    # Right cell: receipt label, txn id, status badge
    badge_para = Paragraph(f'  {status_text}  ', ps('badge', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE, backColor=status_color, borderPadding=3))
    right_cell = [
        Paragraph(receipt_title, whtR),
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
    if payment.payment_type == 'SUPPLY_EXAM' and supply_subjects:
        subject_rows = [[
            Paragraph('SUBJECT CODE', hdr),
            Paragraph('SUBJECT NAME', hdr),
            Paragraph('SEM', hdr),
        ]]
        for subject in supply_subjects:
            subject_rows.append([
                Paragraph(subject.code, val),
                Paragraph(subject.name, val),
                Paragraph(str(subject.semester), val),
            ])

        subject_table = Table(subject_rows, colWidths=['22%', '58%', '20%'])
        subject_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(section_head('APPLIED SUPPLY SUBJECTS'))
        elements.append(Spacer(1, 6))
        elements.append(subject_table)
        elements.append(Spacer(1, 14))

    if payment.payment_type == 'EXAM' and exam_subjects:
        subject_rows = [[
            Paragraph('SUBJECT CODE', hdr),
            Paragraph('SUBJECT NAME', hdr),
            Paragraph('SEM', hdr),
        ]]
        for subject in exam_subjects:
            subject_rows.append([
                Paragraph(subject.code, val),
                Paragraph(subject.name, val),
                Paragraph(str(subject.semester), val),
            ])

        subject_table = Table(subject_rows, colWidths=['22%', '58%', '20%'])
        subject_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(section_head('CURRENT SEMESTER EXAM SUBJECTS'))
        elements.append(Spacer(1, 6))
        elements.append(subject_table)
        elements.append(Spacer(1, 14))

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
    college = _get_admin_college(request)
    department_qs = _scope_departments(request).annotate(
        student_count=Count('student', distinct=True),
        faculty_count=Count('faculty', distinct=True),
        subject_count=Count('subject', distinct=True),
    ).order_by('name')
    total_students = Student.objects.filter(department__in=department_qs).count()
    total_faculty  = Faculty.objects.filter(department__in=department_qs).count()
    total_subjects = Subject.objects.filter(department__in=department_qs).count()
    return render(request, 'admin_panel/departments.html', {
        'departments': department_qs,
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_subjects': total_subjects,
        'college': college,
        'branding': _get_college_branding(college),
    })


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
    return render(request, 'admin_panel/department_form.html', {
        'action': 'Add',
        'college': college,
        'branding': _get_college_branding(college),
    })


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
            return render(request, 'admin_panel/department_form.html', {
                'action': 'Edit',
                'dept': dept,
                'college': dept.college,
                'branding': _get_college_branding(dept.college),
            })
        if Department.objects.filter(college=dept.college, code=new_code).exclude(pk=dept.pk).exists():
            messages.error(request, f'Department code "{new_code}" already exists in this college.')
            return render(request, 'admin_panel/department_form.html', {
                'action': 'Edit',
                'dept': dept,
                'college': dept.college,
                'branding': _get_college_branding(dept.college),
            })
        if Department.objects.filter(college=dept.college, name__iexact=new_name).exclude(pk=dept.pk).exists():
            messages.error(request, f'Department "{new_name}" already exists in this college.')
            return render(request, 'admin_panel/department_form.html', {
                'action': 'Edit',
                'dept': dept,
                'college': dept.college,
                'branding': _get_college_branding(dept.college),
            })
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
    return render(request, 'admin_panel/department_form.html', {
        'action': 'Edit',
        'dept': dept,
        'college': dept.college,
        'branding': _get_college_branding(dept.college),
    })


@login_required
def admin_department_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    dept = get_object_or_404(_scope_departments(request), pk=pk)
    if request.method == 'POST':
        original_name = dept.name
        target_department_id = (request.POST.get('target_department') or '').strip()
        target_department = _scope_departments(request).exclude(pk=dept.pk).filter(pk=target_department_id).first()
        if not target_department:
            messages.error(request, 'Select a valid target department before deleting.')
            return redirect('/dashboard/admin/#departments')

        try:
            _transfer_department_records(request, dept, target_department)
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                f'Department "{original_name}" deleted. HOD users were converted to faculty and active records were moved to {target_department.name}.'
            )
    return redirect('/dashboard/admin/#departments')


# ── STUDENTS ────────────────────────────────────────────

@login_required
def admin_student_profile(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')

    departments = _scope_departments(request).order_by('name')
    student = get_object_or_404(
        Student.objects.select_related('user', 'department__college').filter(department__in=departments),
        pk=pk,
    )
    dept = student.department
    college = dept.college

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

    elig = _compute_eligibility(student, student.current_semester, college)
    results = Result.objects.filter(student=student).order_by('semester')
    cgpa = round(sum(r.gpa for r in results) / len(results), 2) if results else None
    fee = Fee.objects.filter(student=student).first()
    pending_assignments = AssignmentSubmission.objects.filter(
        student=student, marks__isnull=True
    ).select_related('assignment__subject').count()
    recent_absences = Attendance.objects.filter(
        student=student, status='ABSENT',
        session__subject__in=subjects
    ).select_related('session__subject').order_by('-session__date')[:10]

    context = {
        'dept': dept,
        'college': college,
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
        'profile_view_mode': 'admin',
    }
    
    # If AJAX request, return just the profile content
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'admin_panel/student_profile_modal.html', context)
    
    return render(request, 'hod/student_profile.html', context)


@login_required
def admin_students(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    year_filter = request.GET.get('year', '').strip()
    dept_filter = request.GET.get('dept', '').strip()
    sem_filter = request.GET.get('sem', '').strip()
    search_query = request.GET.get('q', '').strip()

    departments = _scope_departments(request).order_by('name')
    students = Student.objects.select_related('user', 'department__college').filter(
        department__in=departments,
        is_deleted=False,
    )
    if year_filter:
        students = students.filter(admission_year=year_filter)
    if dept_filter:
        students = students.filter(department_id=dept_filter)
    if sem_filter:
        students = students.filter(current_semester=sem_filter)
    if search_query:
        students = students.filter(
            Q(roll_number__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
            | Q(user__username__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(department__name__icontains=search_query)
            | Q(department__code__icontains=search_query)
        )

    students = students.order_by('department__code', 'current_semester', 'roll_number')
    total_students = students.count()
    page_obj = _paginate_queryset(request, students, per_page=30)
    year_options = list(
        Student.objects.filter(department__in=departments, is_deleted=False)
        .order_by('-admission_year')
        .values_list('admission_year', flat=True)
        .distinct()
    )

    return render(request, 'admin_panel/students.html', {
        'students': page_obj.object_list,
        'students_page': page_obj,
        'student_summary': _enterprise_summary(total_students, page_obj),
        'departments': departments,
        'year_options': year_options,
        'year_filter': year_filter,
        'dept_filter': dept_filter,
        'sem_filter': sem_filter,
        'search_query': search_query,
        'college': _get_admin_college(request),
        'branding': _get_college_branding(_get_admin_college(request)),
    })


@login_required
def admin_students_export_csv(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    year_filter = request.GET.get('year', '')
    dept_filter = request.GET.get('dept', '')
    sem_filter  = request.GET.get('sem', '')
    departments = _scope_departments(request).order_by('name')
    students = Student.objects.select_related('user', 'department__college').filter(
        department__in=departments
    ).order_by('department__code', 'current_semester', 'roll_number')
    if year_filter:
        students = students.filter(admission_year=year_filter)
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
    search_query = request.GET.get('q', '').strip()
    college = _get_admin_college(request) or _default_college()

    base_requests = _scope_registration_requests(request).select_related(
        'desired_department', 'college', 'reviewed_by'
    ).order_by('-created_at')
    requests_list = base_requests
    if status_filter:
        requests_list = requests_list.filter(status=status_filter)
    if dept_filter:
        requests_list = requests_list.filter(desired_department_id=dept_filter)
    if search_query:
        requests_list = requests_list.filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(phone_number__icontains=search_query)
        )

    invites = RegistrationInvite.objects.filter(college=college).select_related(
        'department', 'created_by'
    ).order_by('-created_at')
    departments = _scope_departments(request).order_by('name')
    now = timezone.now()
    request_page = _paginate_queryset(request, requests_list, per_page=25, page_param='requests_page')
    invite_page = _paginate_queryset(request, invites, per_page=20, page_param='invites_page')

    return render(request, 'admin_panel/student_invites.html', {
        'college': college,
        'branding': _get_college_branding(college),
        'departments': departments,
        'status_filter': status_filter,
        'dept_filter': dept_filter,
        'search_query': search_query,
        'status_choices': RegistrationRequest.STATUS_CHOICES,
        'invites': invite_page.object_list,
        'invites_page': invite_page,
        'requests_list': request_page.object_list,
        'requests_page': request_page,
        'active_invites_count': invites.filter(used_at__isnull=True).filter(Q(expires_at__isnull=True) | Q(expires_at__gte=now)).count(),
        'used_invites_count': invites.filter(used_at__isnull=False).count(),
        'expired_invites_count': invites.filter(used_at__isnull=True, expires_at__lt=now).count(),
        'pending_request_count': base_requests.filter(status__in=['SUBMITTED', 'UNDER_REVIEW', 'NEEDS_CORRECTION']).count(),
        'approved_request_count': base_requests.filter(status='APPROVED').count(),
        'converted_request_count': base_requests.filter(status='CONVERTED').count(),
        'rejected_request_count': base_requests.filter(status='REJECTED').count(),
        'initial_tab': request.GET.get('tab', 'requests') if request.GET.get('tab') in {'requests', 'invites'} else 'requests',
        'now': now,
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
            RegistrationInvite.objects.create(
                college=college,
                department=department,
                invited_email=email,
                admission_year=int(admission_year) if admission_year else None,
                current_semester=int(current_semester) if current_semester else None,
                created_by=request.user,
                expires_at=timezone.now() + timedelta(days=7),
            )
            messages.success(request, 'Invite link created successfully.')
        return redirect(f"{reverse('admin_registration_requests')}?tab=invites")

    return redirect(f"{reverse('admin_registration_requests')}?tab=invites")


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
                    status=status,
                    admission_type=request.POST.get('admission_type', 'regular'),
                    entry_semester=_safe_int(request.POST.get('entry_semester', semester), default=_safe_int(semester)),
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
    profile = StudentProfile.objects.filter(user=student.user).first()
    address = Address.objects.filter(user=student.user).order_by('id').first()
    parent = Parent.objects.filter(user=student.user).order_by('id').first()
    emergency_contact = EmergencyContact.objects.filter(user=student.user).order_by('id').first()
    if request.method == 'POST':
        errors = _validate_student_admin_payload(request, student)
        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': errors[0]})
            for error in errors:
                messages.error(request, error)
        else:
            with transaction.atomic():
                student.user.first_name = request.POST.get('first_name', '').strip()
                student.user.last_name  = request.POST.get('last_name', '').strip()
                student.user.email      = request.POST.get('email', '').strip()
                student.user.save()

                student.department_id    = request.POST.get('department', student.department_id)
                student.admission_year   = _safe_int(request.POST.get('admission_year', student.admission_year))
                student.current_semester = _safe_int(request.POST.get('current_semester', student.current_semester))
                student.status           = request.POST.get('status', student.status)
                student.admission_type   = request.POST.get('admission_type', student.admission_type)
                student.entry_semester   = _safe_int(request.POST.get('entry_semester', student.entry_semester), default=student.entry_semester)
                student.save()

                profile_defaults = {
                    'date_of_birth': request.POST.get('date_of_birth') or timezone.now().date(),
                    'gender': request.POST.get('gender', '').strip() or 'Not Specified',
                    'phone_number': _digits_only(request.POST.get('phone_number', '').strip()),
                    'alternate_phone': _digits_only(request.POST.get('alternate_phone', '').strip()),
                    'aadhaar_number': _digits_only(request.POST.get('aadhaar_number', '').strip()),
                    'inter_college_name': request.POST.get('inter_college_name', '').strip(),
                    'inter_passed_year': _safe_int(request.POST.get('inter_passed_year')),
                    'inter_percentage': _safe_float(request.POST.get('inter_percentage')),
                    'school_name': request.POST.get('school_name', '').strip(),
                    'school_passed_year': _safe_int(request.POST.get('school_passed_year')),
                    'school_percentage': _safe_float(request.POST.get('school_percentage')),
                    'blood_group': request.POST.get('blood_group', '').strip() or None,
                    'nationality': request.POST.get('nationality', '').strip() or 'Indian',
                    'category': request.POST.get('category', '').strip() or None,
                    'college_email': request.POST.get('college_email', '').strip() or None,
                    'personal_email': request.POST.get('personal_email', '').strip() or None,
                }
                profile, _ = StudentProfile.objects.update_or_create(user=student.user, defaults=profile_defaults)
                if request.FILES.get('profile_photo'):
                    profile.profile_photo = request.FILES['profile_photo']
                    profile.save(update_fields=['profile_photo'])

                address_data = {
                    'street': request.POST.get('street', '').strip(),
                    'city': request.POST.get('city', '').strip(),
                    'state': request.POST.get('state', '').strip(),
                    'pincode': _digits_only(request.POST.get('pincode', '').strip()),
                    'country': request.POST.get('country', '').strip() or 'India',
                }
                if any(address_data.values()):
                    if address is None:
                        address = Address.objects.create(user=student.user, **address_data)
                    else:
                        for field, value in address_data.items():
                            setattr(address, field, value)
                        address.save()

                parent_type = request.POST.get('parent_type', '').strip()
                parent_name = request.POST.get('parent_name', '').strip()
                parent_phone = request.POST.get('parent_phone_number', '').strip()
                parent_email = request.POST.get('parent_email', '').strip() or None
                parent_occupation = request.POST.get('parent_occupation', '').strip() or None
                if parent_type or parent_name or parent_phone or parent_email or parent_occupation:
                    parent_defaults = {
                        'parent_type': parent_type or 'FATHER',
                        'name': parent_name,
                        'phone_number': _digits_only(parent_phone),
                        'email': parent_email,
                        'occupation': parent_occupation,
                    }
                    if parent is None:
                        parent = Parent.objects.create(user=student.user, **parent_defaults)
                    else:
                        for field, value in parent_defaults.items():
                            setattr(parent, field, value)
                        parent.save()

                emergency_data = {
                    'name': request.POST.get('emergency_name', '').strip(),
                    'relation': request.POST.get('emergency_relation', '').strip(),
                    'phone_number': _digits_only(request.POST.get('emergency_phone_number', '').strip()),
                }
                if any(emergency_data.values()):
                    if emergency_contact is None:
                        emergency_contact = EmergencyContact.objects.create(user=student.user, **emergency_data)
                    else:
                        for field, value in emergency_data.items():
                            setattr(emergency_contact, field, value)
                        emergency_contact.save()

                UserRole.objects.filter(user=student.user).update(college=student.department.college)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': True})
            
            messages.success(request, 'Student updated.')
            return redirect('/dashboard/admin/#students')
    return render(request, 'admin_panel/student_form.html', {
        'student': student,
        'departments': departments,
        'action': 'Edit',
        'profile': profile,
        'address': address,
        'parent': parent,
        'emergency_contact': emergency_contact,
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
                    # ── Semester reset: clear per-semester data ──────────────
                    # Clear SectionSubjectFacultyMap for old semester (sections will be rebuilt)
                    from students.models import SectionSubjectFacultyMap as _SSF, Section as _Sec
                    old_sections = _Sec.objects.filter(department_id=dept_id, semester=from_sem)
                    _SSF.objects.filter(section__in=old_sections).delete()
                    old_sections.delete()

                    # Deactivate quizzes for old semester subjects
                    old_subject_ids = list(Subject.objects.filter(
                        department_id=dept_id, semester=from_sem
                    ).values_list('id', flat=True))
                    Quiz.objects.filter(subject_id__in=old_subject_ids, is_active=True).update(is_active=False)

                    # Clear pending HOD CE approvals for old semester
                    HODApproval.objects.filter(
                        department_id=dept_id,
                        approval_type='CE_MARKS',
                        subject_id__in=old_subject_ids,
                        status='PENDING',
                    ).update(status='REJECTED')

                    _audit('USER_PROMOTED', request.user,
                           f"Batch promotion: {affected} students from {dept_id} Sem {from_sem} → {from_sem + 1}",
                           college=_get_admin_college(request), request=request)
                    messages.success(request, f'{affected} student(s) promoted to Semester {from_sem + 1}. Semester data reset.')
            return redirect('/dashboard/admin/#students')

    return render(request, 'admin_panel/bulk_promote.html', {
        'departments': departments,
        'college': _get_admin_college(request),
        'branding': _get_college_branding(_get_admin_college(request)),
    })


@login_required
def admin_students_bulk_promote(request):
    if not _admin_guard(request):
        return redirect('dashboard')

    departments = _scope_departments(request).order_by('name')
    students_base = Student.objects.select_related('user', 'department').filter(
        department__in=departments,
        status='ACTIVE',
        is_deleted=False,
    ).order_by('roll_number')
    year_options = list(
        students_base.order_by('-admission_year').values_list('admission_year', flat=True).distinct()
    )

    filter_source = request.POST if request.method == 'POST' else request.GET
    selected_year = (filter_source.get('year') or '').strip()
    selected_department = (filter_source.get('department') or '').strip()

    eligible_students_qs = students_base
    if selected_year:
        eligible_students_qs = eligible_students_qs.filter(admission_year=selected_year)
    if selected_department:
        eligible_students_qs = eligible_students_qs.filter(department_id=selected_department)
    eligible_students = list(eligible_students_qs)

    semester_set = sorted({student.current_semester for student in eligible_students if student.current_semester})
    current_semester_label = ''
    if len(semester_set) == 1:
        current_semester_label = f'Semester {semester_set[0]}'
    elif len(semester_set) > 1:
        current_semester_label = 'Multiple semesters'

    preview_students = []
    for student in eligible_students:
        next_semester = student.current_semester + 1 if student.current_semester and student.current_semester < 8 else None
        preview_students.append({
            'pk': student.pk,
            'roll_number': student.roll_number,
            'name': student.user.get_full_name() or student.user.username,
            'current_semester': student.current_semester,
            'next_semester': next_semester,
            'next_label': f'Semester {next_semester}' if next_semester else 'Graduate',
        })

    if request.method == 'POST' and (request.POST.get('action') or '').strip() == 'promote':
        selected_ids = request.POST.getlist('student_ids')

        if not selected_year or not selected_department:
            messages.error(request, 'Select academic year and department first.')
        elif not eligible_students:
            messages.error(request, 'No eligible students found for the selected academic year and department.')
        elif not selected_ids:
            messages.error(request, 'Select at least one student to promote.')
        else:
            selected_students = list(eligible_students_qs.filter(pk__in=selected_ids))
            if not selected_students:
                messages.error(request, 'The selected students could not be found.')
            else:
                promoted_count = 0
                graduated_count = 0
                with transaction.atomic():
                    for student in selected_students:
                        from_sem = student.current_semester or 1
                        if from_sem >= 8:
                            StudentLifecycleEvent.objects.create(
                                student=student,
                                event_type='GRADUATED',
                                from_status='ACTIVE',
                                to_status='GRADUATED',
                                from_semester=from_sem,
                                to_semester=from_sem,
                                reason='Bulk promotion graduation',
                                performed_by=request.user,
                            )
                            student.status = 'GRADUATED'
                            student.save(update_fields=['status'])
                            graduated_count += 1
                        else:
                            StudentLifecycleEvent.objects.create(
                                student=student,
                                event_type='PROMOTED',
                                from_status='ACTIVE',
                                to_status='ACTIVE',
                                from_semester=from_sem,
                                to_semester=from_sem + 1,
                                reason=f'Bulk promotion Sem {from_sem} to Sem {from_sem + 1}',
                                performed_by=request.user,
                            )
                            student.current_semester = from_sem + 1
                            student.save(update_fields=['current_semester'])
                            promoted_count += 1

                selected_department_obj = departments.filter(pk=selected_department).first()
                dept_code = selected_department_obj.code if selected_department_obj else selected_department
                _audit(
                    'USER_PROMOTED',
                    request.user,
                    f'Selective bulk promotion for {dept_code} {selected_year}: {promoted_count} promoted, {graduated_count} graduated',
                    college=_get_admin_college(request),
                    request=request,
                )
                messages.success(
                    request,
                    f'{promoted_count} student(s) promoted and {graduated_count} student(s) marked as graduated.'
                )
                return redirect(f"{reverse('admin_students_bulk_promote')}?year={selected_year}&department={selected_department}")

    return render(request, 'admin_panel/bulk_promote.html', {
        'college': _get_admin_college(request),
        'branding': _get_college_branding(_get_admin_college(request)),
        'departments': departments,
        'year_options': year_options,
        'selected_year': selected_year,
        'selected_department': selected_department,
        'eligible_students': preview_students,
        'eligible_count': len(preview_students),
        'current_semester_label': current_semester_label,
    })


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
        roll_number = student.roll_number
        user = student.user
        with transaction.atomic():
            Payment.objects.filter(Q(user=user) | Q(fee__student=student)).delete()
            Fee.objects.filter(student=student).delete()
            UserRole.objects.filter(user=user).delete()
            user.delete()
        messages.success(request, f'Student {roll_number} and linked records were deleted.')
    return redirect('/dashboard/admin/#students')


# ── FACULTY ─────────────────────────────────────────────

@login_required
def admin_faculty_list(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    dept_filter = request.GET.get('dept', '').strip()
    search_query = request.GET.get('search', '').strip()

    college = _get_admin_college(request)
    departments = _scope_departments(request).order_by('name')
    faculty = Faculty.objects.filter(
        department__in=departments,
        is_deleted=False,
    ).select_related('user', 'department')
    hods = HOD.objects.filter(
        department__in=departments,
        is_active=True,
    ).select_related('user', 'department')

    if dept_filter:
        faculty = faculty.filter(department_id=dept_filter)
        hods = hods.filter(department_id=dept_filter)
    if search_query:
        faculty = faculty.filter(
            Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(employee_id__icontains=search_query)
            | Q(department__name__icontains=search_query)
            | Q(department__code__icontains=search_query)
            | Q(designation__icontains=search_query)
        )
        hods = hods.filter(
            Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(employee_id__icontains=search_query)
            | Q(department__name__icontains=search_query)
            | Q(department__code__icontains=search_query)
            | Q(designation__icontains=search_query)
        )

    faculty = faculty.order_by('department__name', 'user__first_name', 'user__last_name')
    hods = hods.order_by('department__name', 'user__first_name', 'user__last_name')
    total_faculty = faculty.count()
    total_hods = hods.count()
    faculty_page = _paginate_queryset(request, faculty, per_page=25, page_param='faculty_page')
    hod_page = _paginate_queryset(request, hods, per_page=15, page_param='hod_page')

    return render(request, 'admin_panel/faculty.html', {
        'college': college,
        'branding': _get_college_branding(college),
        'departments': departments,
        'faculty': faculty_page.object_list,
        'hods': hod_page.object_list,
        'faculty_page': faculty_page,
        'hod_page': hod_page,
        'faculty_summary': _enterprise_summary(total_faculty, faculty_page),
        'hod_summary': _enterprise_summary(total_hods, hod_page),
        'dept_filter': dept_filter,
        'search_query': search_query,
    })


@login_required
def admin_faculty_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
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

        errors = _validate_staff_admin_payload(request, departments, is_hod=False)
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            department = get_object_or_404(departments, pk=dept_id)
            password_value, password_generated = _resolve_password(password)
            user = User.objects.create_user(
                username=username, email=email, password=password_value,
                first_name=first_name, last_name=last_name
            )
            UserRole.objects.create(user=user, role=3, college=department.college)
            faculty = Faculty.objects.create(
                user=user, employee_id=employee_id, department=department,
                designation=designation, qualification=qualification,
                experience_years=_safe_int(experience), phone_number=_digits_only(phone)
            )
            _audit(
                'USER_CREATED', request.user,
                f'Faculty account created for {user.get_full_name() or user.username}',
                faculty=faculty,
                college=department.college,
                new_value=f'employee_id={employee_id}, department={department.code}, designation={designation}',
                request=request,
            )
            if password_generated:
                messages.success(request, f'Faculty {first_name} {last_name} added. Temporary password: {password_value}')
            else:
                messages.success(request, f'Faculty {first_name} {last_name} added.')
            return redirect('/dashboard/admin/#faculty')
    return render(request, 'admin_panel/faculty_form.html', {
        'departments': departments,
        'action': 'Add',
        'college': college,
        'branding': _get_college_branding(college),
    })


@login_required
def admin_faculty_profile(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')

    departments = _scope_departments(request).order_by('name')
    faculty = get_object_or_404(
        Faculty.objects.select_related('user', 'department').filter(department__in=departments),
        pk=pk,
    )
    dept = faculty.department

    assigned_subjects = FacultySubject.objects.filter(faculty=faculty).select_related('subject').order_by('subject__semester', 'subject__name')
    now = timezone.now()
    sessions_this_month = AttendanceSession.objects.filter(
        faculty=faculty, date__year=now.year, date__month=now.month
    ).count()
    sessions_total = AttendanceSession.objects.filter(faculty=faculty).count()

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

    pending_reviews = AssignmentSubmission.objects.filter(
        assignment__created_by=faculty.user, marks__isnull=True
    ).count()
    leave_history = LeaveApplication.objects.filter(faculty=faculty).order_by('-from_date')[:10]

    feedback_avg = None
    responses = FacultyFeedbackResponse.objects.filter(cycle__faculty=faculty)
    ratings = []
    for response in responses:
        for value in response.ratings.values():
            try:
                ratings.append(float(value))
            except (TypeError, ValueError):
                pass
    if ratings:
        feedback_avg = round(sum(ratings) / len(ratings), 1)

    leave_summary = {
        'approved': LeaveApplication.objects.filter(faculty=faculty, status='APPROVED').count(),
        'pending': LeaveApplication.objects.filter(faculty=faculty, status='PENDING').count(),
        'rejected': LeaveApplication.objects.filter(faculty=faculty, status='REJECTED').count(),
    }

    context = {
        'dept': dept,
        'college': dept.college,
        'faculty': faculty,
        'assigned_subjects': assigned_subjects,
        'subject_stats': subject_stats,
        'sessions_this_month': sessions_this_month,
        'sessions_total': sessions_total,
        'pending_reviews': pending_reviews,
        'leave_history': leave_history,
        'feedback_avg': feedback_avg,
        'leave_summary': leave_summary,
        'branding': _get_college_branding(dept.college),
        'profile_view_mode': 'admin',
    }
    
    # If AJAX request, return just the profile content
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'admin_panel/faculty_profile_modal.html', context)
    
    return render(request, 'hod/faculty_profile.html', context)


@login_required
def admin_faculty_edit(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    faculty = get_object_or_404(Faculty.objects.filter(department__in=departments), pk=pk)
    if request.method == 'POST':
        errors = _validate_staff_admin_payload(
            request, departments, is_hod=False,
            existing_user=faculty.user, existing_staff=faculty
        )
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            old_snapshot = f"department={faculty.department.code}, designation={faculty.designation}, phone={faculty.phone_number}"
            faculty.user.first_name = request.POST.get('first_name', '').strip()
            faculty.user.last_name  = request.POST.get('last_name', '').strip()
            faculty.user.email      = request.POST.get('email', '').strip()
            faculty.user.username   = request.POST.get('username', faculty.user.username).strip() or faculty.user.username
            faculty.user.save()
            faculty.employee_id     = request.POST.get('employee_id', faculty.employee_id).strip()
            faculty.department_id   = request.POST.get('department', faculty.department_id)
            faculty.designation     = request.POST.get('designation', faculty.designation).strip()
            faculty.qualification   = request.POST.get('qualification', faculty.qualification).strip()
            faculty.experience_years= _safe_int(request.POST.get('experience_years', faculty.experience_years))
            faculty.phone_number    = _digits_only(request.POST.get('phone_number', faculty.phone_number).strip())
            faculty.save()
            UserRole.objects.filter(user=faculty.user).update(college=faculty.department.college)
            _audit(
                'OTHER', request.user,
                f'Faculty profile updated for {faculty.user.get_full_name() or faculty.user.username}',
                faculty=faculty,
                college=faculty.department.college,
                old_value=old_snapshot,
                new_value=f"department={faculty.department.code}, designation={faculty.designation}, phone={faculty.phone_number}",
                request=request,
            )
            messages.success(request, 'Faculty updated.')
            return redirect('/dashboard/admin/#faculty')
    return render(request, 'admin_panel/faculty_form.html', {
        'faculty': faculty,
        'departments': departments,
        'action': 'Edit',
        'college': faculty.department.college,
        'branding': _get_college_branding(faculty.department.college),
    })


@login_required
def admin_faculty_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    faculty = get_object_or_404(Faculty.objects.filter(department__in=_scope_departments(request)), pk=pk)
    if request.method == 'POST':
        _audit(
            'OTHER', request.user,
            f'Faculty account deleted for {faculty.user.get_full_name() or faculty.user.username}',
            faculty=faculty,
            college=faculty.department.college,
            old_value=f"employee_id={faculty.employee_id}, department={faculty.department.code}",
            request=request,
        )
        faculty.user.delete()
        messages.success(request, 'Faculty deleted.')
    return redirect('/dashboard/admin/#faculty')


@login_required
def admin_faculty_feedback(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    departments = _scope_departments(request).order_by('name')
    faculty = Faculty.objects.filter(department__college=college, is_deleted=False).select_related('user', 'department').order_by('department__code', 'user__first_name')
    subjects = Subject.objects.filter(department__college=college).select_related('department').order_by('department__code', 'semester', 'code')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        dept_id = request.POST.get('department') or None
        semester = _safe_int(request.POST.get('semester'), default=0) or None
        subject_id = request.POST.get('subject') or None
        faculty_id = request.POST.get('faculty') or None
        questions = request.POST.get('questions', '').strip()
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if not title or not start_date or not end_date or not questions:
            messages.error(request, 'Title, dates, and questions are required.')
        elif end_date < start_date:
            messages.error(request, 'End date must be on or after start date.')
        else:
            FacultyFeedbackCycle.objects.create(
                college=college,
                title=title,
                department_id=dept_id,
                semester=semester,
                subject_id=subject_id,
                faculty_id=faculty_id,
                questions=questions,
                start_date=start_date,
                end_date=end_date,
                created_by=request.user,
            )
            messages.success(request, 'Faculty feedback cycle created.')
            return redirect('admin_faculty_feedback')

    cycles = FacultyFeedbackCycle.objects.filter(college=college).select_related(
        'department', 'subject', 'faculty__user'
    ).prefetch_related('responses')
    cycle_rows = []
    for cycle in cycles:
        responses = list(cycle.responses.all())
        avg = round(sum(r.average_rating for r in responses) / len(responses), 2) if responses else 0
        cycle_rows.append({'cycle': cycle, 'responses': len(responses), 'avg': avg})

    return render(request, 'admin_panel/faculty_feedback.html', {
        'departments': departments,
        'faculty': faculty,
        'subjects': subjects,
        'cycle_rows': cycle_rows,
        'today': timezone.localdate(),
        'branding': _get_college_branding(college),
    })


@login_required
def admin_faculty_feedback_toggle(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    cycle = get_object_or_404(FacultyFeedbackCycle, pk=pk, college=college)
    if request.method == 'POST':
        cycle.is_active = not cycle.is_active
        cycle.save(update_fields=['is_active'])
        messages.success(request, f'Feedback cycle {"opened" if cycle.is_active else "closed"}.')
    return redirect('admin_faculty_feedback')


# ── HODs ────────────────────────────────────────────────

@login_required
def admin_hod_profile(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')

    departments = _scope_departments(request).order_by('name')
    hod = get_object_or_404(
        HOD.objects.select_related('user', 'department').filter(department__in=departments),
        pk=pk,
    )
    dept = hod.department
    faculty_profile = getattr(hod, 'faculty_profile', None)
    assigned_subjects = []
    subject_stats = []
    sessions_this_month = 0
    sessions_total = 0
    leave_history = []
    pending_reviews = 0
    feedback_avg = None
    leave_summary = {'approved': 0, 'pending': 0, 'rejected': 0}

    if faculty_profile:
        assigned_subjects = FacultySubject.objects.filter(faculty=faculty_profile).select_related('subject').order_by('subject__semester', 'subject__name')
        now = timezone.now()
        sessions_this_month = AttendanceSession.objects.filter(
            faculty=faculty_profile, date__year=now.year, date__month=now.month
        ).count()
        sessions_total = AttendanceSession.objects.filter(faculty=faculty_profile).count()
        subject_ids = [fs.subject_id for fs in assigned_subjects]
        att_agg = Attendance.objects.filter(
            session__faculty=faculty_profile, session__subject_id__in=subject_ids
        ).values('session__subject_id').annotate(
            total=Count('id'), present=Count('id', filter=Q(status='PRESENT'))
        )
        att_map = {r['session__subject_id']: r for r in att_agg}
        for fs in assigned_subjects:
            agg = att_map.get(fs.subject_id, {'total': 0, 'present': 0})
            pct = round(agg['present'] / agg['total'] * 100, 1) if agg['total'] > 0 else 0
            subject_stats.append({'subject': fs.subject, 'total': agg['total'], 'present': agg['present'], 'pct': pct})

        pending_reviews = AssignmentSubmission.objects.filter(
            assignment__created_by=hod.user, marks__isnull=True
        ).count()
        leave_history = LeaveApplication.objects.filter(faculty=faculty_profile).order_by('-from_date')[:10]
        leave_summary = {
            'approved': LeaveApplication.objects.filter(faculty=faculty_profile, status='APPROVED').count(),
            'pending': LeaveApplication.objects.filter(faculty=faculty_profile, status='PENDING').count(),
            'rejected': LeaveApplication.objects.filter(faculty=faculty_profile, status='REJECTED').count(),
        }
        responses = FacultyFeedbackResponse.objects.filter(cycle__faculty=faculty_profile)
        ratings = []
        for response in responses:
            for value in response.ratings.values():
                try:
                    ratings.append(float(value))
                except (TypeError, ValueError):
                    pass
        if ratings:
            feedback_avg = round(sum(ratings) / len(ratings), 1)

    context = {
        'hod': hod,
        'dept': dept,
        'college': dept.college,
        'faculty_profile': faculty_profile,
        'assigned_subjects': assigned_subjects,
        'subject_stats': subject_stats,
        'sessions_this_month': sessions_this_month,
        'sessions_total': sessions_total,
        'pending_reviews': pending_reviews,
        'leave_history': leave_history,
        'feedback_avg': feedback_avg,
        'leave_summary': leave_summary,
        'branding': _get_college_branding(dept.college),
    }
    
    # If AJAX request, return just the profile content
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'admin_panel/hod_profile_modal.html', context)
    
    return render(request, 'admin_panel/hod_profile.html', context)


@login_required
def admin_hod_edit(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    hod = get_object_or_404(HOD.objects.select_related('user', 'department').filter(department__in=departments), pk=pk)
    faculty_profile = getattr(hod, 'faculty_profile', None)

    if request.method == 'POST':
        dept_id = request.POST.get('department')
        employee_id = request.POST.get('employee_id', '').strip()
        username = request.POST.get('username', '').strip()
        can_take_classes = request.POST.get('can_take_classes') == 'on'
        joined_date_str = request.POST.get('joined_date', '').strip()

        joined_date = None
        if joined_date_str:
            try:
                joined_date = datetime.fromisoformat(joined_date_str).date()
            except (ValueError, TypeError):
                joined_date = hod.joined_date

        if not dept_id:
            messages.error(request, 'Select a department.')
        elif User.objects.exclude(pk=hod.user_id).filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        elif HOD.objects.exclude(pk=hod.pk).filter(employee_id=employee_id).exists():
            messages.error(request, 'Employee ID already exists.')
        elif HOD.objects.exclude(pk=hod.pk).filter(department_id=dept_id, is_active=True).exists():
            messages.error(request, 'This department already has an active HOD.')
        else:
            department = get_object_or_404(departments, pk=dept_id)
            hod.user.first_name = request.POST.get('first_name', '').strip()
            hod.user.last_name = request.POST.get('last_name', '').strip()
            hod.user.username = username
            hod.user.email = request.POST.get('email', '').strip()
            hod.user.save()

            hod.employee_id = employee_id
            hod.department = department
            hod.qualification = request.POST.get('qualification', '').strip()
            hod.experience_years = _safe_int(request.POST.get('experience_years', hod.experience_years))
            hod.phone_number = request.POST.get('phone_number', '').strip()
            hod.designation = request.POST.get('designation', '').strip() or 'Head of Department'
            hod.specialization = request.POST.get('specialization', '').strip()
            hod.joined_date = joined_date
            hod.can_take_classes = can_take_classes
            hod.save()

            UserRole.objects.filter(user=hod.user).update(college=department.college)

            if can_take_classes:
                faculty_profile, _ = Faculty.objects.get_or_create(
                    user=hod.user,
                    defaults={
                        'employee_id': employee_id,
                        'department': department,
                        'designation': hod.designation,
                        'qualification': hod.qualification,
                        'experience_years': hod.experience_years,
                        'phone_number': hod.phone_number,
                        'joined_date': hod.joined_date,
                    }
                )
                faculty_profile.employee_id = employee_id
                faculty_profile.department = department
                faculty_profile.designation = hod.designation
                faculty_profile.qualification = hod.qualification
                faculty_profile.experience_years = hod.experience_years
                faculty_profile.phone_number = hod.phone_number
                faculty_profile.joined_date = hod.joined_date
                faculty_profile.save()

            messages.success(request, 'HOD updated.')
            return redirect('/dashboard/admin/#faculty')

    return render(request, 'admin_panel/hod_form.html', {
        'departments': departments,
        'hod': hod,
        'action': 'Edit',
        'college': hod.department.college,
        'branding': _get_college_branding(hod.department.college),
    })


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
    college = _get_admin_college(request)
    departments = _scope_departments(request).order_by('name')
    if request.method == 'POST':
        first_name    = request.POST.get('first_name', '').strip()
        last_name     = request.POST.get('last_name', '').strip()
        username      = request.POST.get('username', '').strip()
        email         = request.POST.get('email', '').strip()
        password      = request.POST.get('password', '')
        employee_id   = request.POST.get('employee_id', '').strip()
        dept_id       = request.POST.get('department')
        qualification = request.POST.get('qualification', '').strip()
        experience    = request.POST.get('experience_years', 0)
        phone         = request.POST.get('phone_number', '').strip()
        designation   = request.POST.get('designation', 'Head of Department').strip()
        specialization= request.POST.get('specialization', '').strip()
        joined_date_str = request.POST.get('joined_date', '').strip()
        can_take_classes = request.POST.get('can_take_classes') == 'on'

        joined_date = None
        if joined_date_str:
            try:
                joined_date = datetime.fromisoformat(joined_date_str).date()
            except (ValueError, TypeError):
                joined_date = None

        errors = _validate_staff_admin_payload(request, departments, is_hod=True)
        if dept_id and HOD.objects.filter(department_id=dept_id, is_active=True).exists():
            errors.append('This department already has an active HOD.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            department = get_object_or_404(departments, pk=dept_id)
            password_value, password_generated = _resolve_password(password)
            user = User.objects.create_user(
                username=username, email=email, password=password_value,
                first_name=first_name, last_name=last_name
            )
            UserRole.objects.create(user=user, role=2, college=department.college)
            hod = HOD.objects.create(
                user=user, employee_id=employee_id, department=department,
                qualification=qualification, experience_years=_safe_int(experience),
                phone_number=_digits_only(phone), is_active=True,
                designation=designation, specialization=specialization,
                joined_date=joined_date, can_take_classes=can_take_classes,
            )
            # If HOD also teaches, auto-create a Faculty record so they can be assigned subjects/timetable
            if can_take_classes:
                Faculty.objects.get_or_create(
                    user=user,
                    defaults={
                        'employee_id': employee_id,
                        'department': department,
                        'designation': designation,
                        'qualification': qualification,
                        'experience_years': _safe_int(experience),
                        'phone_number': _digits_only(phone),
                        'joined_date': joined_date,
                    }
                )
                # Give them faculty role too (role=3) — keep HOD role as primary
                UserRole.objects.filter(user=user).update(role=2)  # HOD role stays

            _audit(
                'USER_CREATED',
                request.user,
                f'HOD created: {user.get_full_name() or user.username} ({department.code})',
                college=department.college,
                request=request,
                new_value={
                    'username': user.username,
                    'employee_id': employee_id,
                    'department': department.code,
                    'can_take_classes': can_take_classes,
                },
            )

            if password_generated:
                messages.success(request, f'HOD {first_name} {last_name} added. Temporary password: {password_value}')
            else:
                messages.success(request, f'HOD {first_name} {last_name} added.')
            return redirect('/dashboard/admin/#faculty')
    return render(request, 'admin_panel/hod_form.html', {
        'departments': departments,
        'college': college,
        'branding': _get_college_branding(college),
    })


@login_required
def admin_hod_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    hod = get_object_or_404(HOD.objects.filter(department__in=_scope_departments(request)), pk=pk)
    if request.method == 'POST':
        _audit(
            'OTHER',
            request.user,
            f'HOD deleted: {hod.user.get_full_name() or hod.user.username} ({hod.department.code})',
            college=hod.department.college,
            request=request,
            old_value={'employee_id': hod.employee_id, 'department': hod.department.code},
        )
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
    semester_filter = request.GET.get('sem', '').strip()
    search_query = request.GET.get('q', '').strip()
    subjects = Subject.objects.filter(
        department__in=departments
    ).select_related('department').order_by('department__code', 'semester', 'code')
    if dept_filter:
        subjects = subjects.filter(department_id=dept_filter)
    if semester_filter:
        subjects = subjects.filter(semester=semester_filter)
    if search_query:
        subjects = subjects.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(department__name__icontains=search_query) |
            Q(department__code__icontains=search_query)
        )
    return render(request, 'admin_panel/subjects.html', {
        'subjects': subjects,
        'departments': departments,
        'dept_filter': dept_filter,
        'semester_filter': semester_filter,
        'search_query': search_query,
        'college': _get_admin_college(request),
        'branding': _get_college_branding(_get_admin_college(request)),
    })


@login_required
def admin_subject_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    selected_dept = request.GET.get('dept', '').strip()
    selected_semester = request.GET.get('sem', '').strip()
    subject_form = None
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        code    = request.POST.get('code', '').strip().upper()
        dept_id = request.POST.get('department')
        semester= request.POST.get('semester')
        subject_form = {
            'name': name,
            'code': code,
            'category': request.POST.get('category', 'PC'),
            'lecture_hours': _safe_int(request.POST.get('lecture_hours')) or 3,
            'tutorial_hours': _safe_int(request.POST.get('tutorial_hours')) or 0,
            'practical_hours': _safe_int(request.POST.get('practical_hours')) or 0,
            'credits': _safe_int(request.POST.get('credits')) or 3,
        }
        selected_dept = dept_id or selected_dept
        selected_semester = semester or selected_semester
        if not all([name, code, dept_id, semester]):
            messages.error(request, 'Subject name, code, department, and semester are required.')
        else:
            department = get_object_or_404(departments, pk=dept_id)
            semester_no = _safe_int(semester)
            code_max_length = Subject._meta.get_field('code').max_length or 20
            name_max_length = Subject._meta.get_field('name').max_length or 100
            if len(code) > code_max_length:
                messages.error(request, f'Subject code cannot exceed {code_max_length} characters.')
            elif len(name) > name_max_length:
                messages.error(request, f'Subject name cannot exceed {name_max_length} characters.')
            else:
                duplicate_qs = Subject.objects.filter(department=department)
                if duplicate_qs.filter(code=code).exists():
                    existing_subject = duplicate_qs.filter(code=code).first()
                    messages.error(
                        request,
                        f'Subject code "{code}" is already taken in {department.code}'
                        f'{f" for semester {existing_subject.semester}" if existing_subject else ""}. '
                        'Please use a different code.'
                    )
                elif duplicate_qs.filter(name__iexact=name, semester=semester_no).exists():
                    messages.error(request, f'Subject "{name}" already exists for {department.code} semester {semester_no}.')
                else:
                    try:
                        Subject.objects.create(
                            name=name, code=code, department=department, semester=semester_no,
                            lecture_hours=_safe_int(request.POST.get('lecture_hours')) or 3,
                            tutorial_hours=_safe_int(request.POST.get('tutorial_hours')) or 0,
                            practical_hours=_safe_int(request.POST.get('practical_hours')) or 0,
                            credits=_safe_int(request.POST.get('credits')) or 3,
                            category=request.POST.get('category', 'PC'),
                        )
                    except IntegrityError:
                        messages.error(
                            request,
                            f'Subject code "{code}" is already taken in {department.code}. Please use a different code.'
                        )
                    except DataError:
                        messages.error(
                            request,
                            f'Subject code or name is too long. Keep the code within {code_max_length} characters '
                            f'and the name within {name_max_length} characters.'
                        )
                    else:
                        messages.success(request, f'Subject "{name}" added.')
                        return redirect(f"{reverse('admin_subjects')}?dept={department.pk}&sem={semester_no}")
    cancel_url = reverse('admin_subjects')
    if selected_dept or selected_semester:
        params = []
        if selected_dept:
            params.append(f"dept={selected_dept}")
        if selected_semester:
            params.append(f"sem={selected_semester}")
        cancel_url = f"{cancel_url}?{'&'.join(params)}"
    return render(request, 'admin_panel/subject_form.html', {
        'departments': departments,
        'action': 'Add',
        'subject': subject_form,
        'selected_dept': selected_dept,
        'selected_semester': selected_semester,
        'cancel_url': cancel_url,
        'college': _get_admin_college(request),
        'branding': _get_college_branding(_get_admin_college(request)),
    })


@login_required
def admin_subject_edit(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    subject = get_object_or_404(Subject.objects.filter(department__in=departments).select_related('department'), pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        dept_id = request.POST.get('department')
        semester = request.POST.get('semester')
        if not all([name, code, dept_id, semester]):
            messages.error(request, 'Subject name, code, department, and semester are required.')
        else:
            department = get_object_or_404(departments, pk=dept_id)
            semester_no = _safe_int(semester)
            code_max_length = Subject._meta.get_field('code').max_length or 20
            name_max_length = Subject._meta.get_field('name').max_length or 100
            if len(code) > code_max_length:
                messages.error(request, f'Subject code cannot exceed {code_max_length} characters.')
            elif len(name) > name_max_length:
                messages.error(request, f'Subject name cannot exceed {name_max_length} characters.')
            else:
                duplicate_qs = Subject.objects.filter(department=department).exclude(pk=subject.pk)
                if duplicate_qs.filter(code=code).exists():
                    existing_subject = duplicate_qs.filter(code=code).first()
                    messages.error(
                        request,
                        f'Subject code "{code}" is already taken in {department.code}'
                        f'{f" for semester {existing_subject.semester}" if existing_subject else ""}. '
                        'Please use a different code.'
                    )
                elif duplicate_qs.filter(name__iexact=name, semester=semester_no).exists():
                    messages.error(request, f'Subject "{name}" already exists for {department.code} semester {semester_no}.')
                else:
                    subject.name = name
                    subject.code = code
                    subject.department = department
                    subject.semester = semester_no
                    subject.lecture_hours = _safe_int(request.POST.get('lecture_hours')) or 3
                    subject.tutorial_hours = _safe_int(request.POST.get('tutorial_hours')) or 0
                    subject.practical_hours = _safe_int(request.POST.get('practical_hours')) or 0
                    subject.credits = _safe_int(request.POST.get('credits')) or 3
                    subject.category = request.POST.get('category', 'PC')
                    subject.weekly_hours = (
                        subject.lecture_hours +
                        subject.tutorial_hours +
                        subject.practical_hours
                    )
                    try:
                        subject.save()
                    except IntegrityError:
                        messages.error(
                            request,
                            f'Subject code "{code}" is already taken in {department.code}. Please use a different code.'
                        )
                    except DataError:
                        messages.error(
                            request,
                            f'Subject code or name is too long. Keep the code within {code_max_length} characters '
                            f'and the name within {name_max_length} characters.'
                        )
                    else:
                        messages.success(request, f'Subject "{subject.name}" updated.')
                        return redirect(f"{reverse('admin_subjects')}?dept={department.pk}&sem={semester_no}")
    cancel_url = f"{reverse('admin_subjects')}?dept={subject.department_id}&sem={subject.semester}"
    return render(request, 'admin_panel/subject_form.html', {
        'departments': departments,
        'action': 'Edit',
        'subject': subject,
        'selected_dept': str(subject.department_id),
        'selected_semester': str(subject.semester),
        'cancel_url': cancel_url,
        'college': _get_admin_college(request),
        'branding': _get_college_branding(_get_admin_college(request)),
    })


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
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        name  = request.POST.get('name', '').strip()
        code  = request.POST.get('code', '').strip().upper()
        desc  = request.POST.get('description', '').strip()
        year  = _safe_int(request.POST.get('effective_from_year'))
        
        if not all([name, code, year]):
            if is_ajax:
                return JsonResponse({'ok': False, 'error': 'Name, code, and effective year are required.'})
            messages.error(request, 'Name, code, and effective year are required.')
        elif Regulation.objects.filter(college=college, code=code).exists():
            if is_ajax:
                return JsonResponse({'ok': False, 'error': f'Regulation code "{code}" already exists.'})
            messages.error(request, f'Regulation code "{code}" already exists.')
        else:
            Regulation.objects.create(college=college, name=name, code=code,
                                      description=desc, effective_from_year=year)
            if is_ajax:
                return JsonResponse({'ok': True})
            messages.success(request, f'Regulation "{name}" created.')
            return redirect('admin_regulations')
    
    if is_ajax:
        return JsonResponse({'ok': False, 'error': 'Invalid request.'})
    return redirect('admin_regulations')


@login_required
def admin_regulation_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    reg = get_object_or_404(Regulation, pk=pk, college=_get_admin_college(request))
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if request.method == 'POST':
        reg.delete()
        if is_ajax:
            return JsonResponse({'ok': True})
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
    feature_cfg, _ = CollegeFeatureConfig.objects.get_or_create(college=college)
    regulations = Regulation.objects.filter(college=college, is_active=True)
    departments = _scope_departments(request).order_by('name')
    return render(request, 'admin_panel/elective_pools.html', {
        'pools': pools, 'college': college,
        'feature_cfg': feature_cfg,
        'branding': _get_college_branding(college),
        'regulations': regulations,
        'departments': departments,
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
            error_msg = 'Slot name is required (e.g. PE-1).'
        elif not subj_ids:
            error_msg = 'Select at least one subject for this elective pool.'
        else:
            error_msg = None
        
        if error_msg:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg})
            messages.error(request, error_msg)
        else:
            from django.utils.dateparse import parse_datetime
            deadline = parse_datetime(deadline_str) if deadline_str else None
            pool = ElectivePool.objects.create(
                regulation=regulation, department=department, semester=semester,
                slot_name=slot, elective_type=el_type, quota_per_subject=quota,
                deadline=deadline, created_by=request.user,
            )
            pool.subjects.set(Subject.objects.filter(pk__in=subj_ids))
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': True})
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
def admin_course_registration_toggle(request):
    """
    Admin opens/closes the course registration window for a specific semester.
    POST params: action (open|close), semester (int)
    """
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    cfg, _ = CollegeFeatureConfig.objects.get_or_create(college=college)

    if request.method == 'POST':
        action = request.POST.get('action')
        semester = _safe_int(request.POST.get('semester'), 0)
        if action == 'open' and semester > 0:
            cfg.course_registration_open = True
            cfg.course_registration_semester = semester
            cfg.save(update_fields=['course_registration_open', 'course_registration_semester'])
            messages.success(request, f'Course registration opened for Semester {semester}. Students can now register.')
        elif action == 'close':
            cfg.course_registration_open = False
            cfg.save(update_fields=['course_registration_open'])
            messages.success(request, 'Course registration window closed.')
        else:
            messages.error(request, 'Invalid action or semester.')

    return redirect(request.POST.get('next', 'admin_elective_pools'))


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


# ── API: SUBJECTS BY DEPARTMENT ───────────────────────────────────────────────

def api_subjects_by_department(request):
    """API endpoint to get subjects for a given department."""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    dept_id = request.GET.get('department')
    if not dept_id:
        return JsonResponse({'subjects': []})
    
    try:
        dept = Department.objects.get(pk=dept_id)
        subjects = Subject.objects.filter(department=dept).values('id', 'code', 'name').order_by('code')
        return JsonResponse({'subjects': list(subjects)})
    except Department.DoesNotExist:
        return JsonResponse({'subjects': []})


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
            messages.warning(request, 'Subjects are managed from the Subjects page. The semester planner only uses the approved catalog.')
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
                # Derive section label A/B/C from position in ordered assignment list
                count = FacultySubject.objects.filter(subject=subject).count()
                section_label = chr(64 + count)  # 1→A, 2→B, 3→C...
                messages.success(request, f'{faculty.user.get_full_name()} assigned to {subject.code} — Section {section_label}.')
        elif action == 'remove_assignment':
            assignment_id = request.POST.get('assignment_id')
            FacultySubject.objects.filter(pk=assignment_id, subject__department=department, subject__semester=selected_semester).delete()
            messages.success(request, 'Faculty assignment removed.')
        elif action == 'add_availability':
            faculty_id = request.POST.get('faculty_id')
            college = _get_admin_college(request)
            faculty = Faculty.objects.filter(pk=faculty_id, department__college=college).first()
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
            result = _auto_generate_timetable(department, selected_semester)
            created_count = result['created']
            skipped = result['skipped_subjects']
            no_avail = result['no_availability']
            if created_count:
                messages.success(request, f'Timetable updated with {created_count} scheduled class slot(s).')
            else:
                messages.warning(request, 'No timetable entries could be generated. Confirm subjects, sections, faculty mappings, rooms, and try again.')
            # Fix 6 — warn about skipped subjects
            if skipped:
                names = ', '.join(s.code for s in skipped)
                messages.warning(request, f'{len(skipped)} subject(s) skipped — no faculty assigned: {names}')
            # Fix 3 — warn about faculty with no availability
            if no_avail:
                names = ', '.join(f.user.get_full_name() or f.user.username for f in no_avail[:5])
                messages.info(request, f'{len(no_avail)} faculty member(s) have no availability set (using default grid): {names}')
        elif action == 'add_break':
            label = request.POST.get('break_label', 'Break').strip()
            day = request.POST.get('break_day', '').strip().upper()
            start = request.POST.get('break_start', '').strip()
            end = request.POST.get('break_end', '').strip()
            scope = request.POST.get('break_scope', 'all')
            college = _get_admin_college(request)
            if day and start and end and college:
                applies_to_all = scope == 'all'
                _, created = TimetableBreak.objects.get_or_create(
                    college=college, day_of_week=day, start_time=start, end_time=end,
                    applies_to_all=applies_to_all,
                    department=None if applies_to_all else department,
                    applies_to='college' if applies_to_all else 'department',
                    defaults={'label': label, 'break_type': 'regular'},
                )
                if created:
                    messages.success(request, f'Break "{label}" added for {day}.')
                else:
                    messages.warning(request, f'A break already exists at {day} {start}–{end} with the same scope. No duplicate added.')
            else:
                messages.error(request, 'Day, start time, and end time are required.')
        elif action == 'delete_break':
            break_id = request.POST.get('break_id')
            college = _get_admin_college(request)
            TimetableBreak.objects.filter(pk=break_id, college=college).delete()
            messages.success(request, 'Break removed.')
        elif action == 'add_classroom':
            room_number = request.POST.get('room_number', '').strip()
            building    = request.POST.get('building', '').strip()
            capacity    = _safe_int(request.POST.get('capacity', '60'), default=60)
            room_type   = request.POST.get('room_type', 'lecture').strip()
            features    = request.POST.get('features', '').strip()
            college = _get_admin_college(request)
            if room_number and college:
                Classroom.objects.get_or_create(
                    college=college, room_number=room_number,
                    defaults={'building': building, 'capacity': capacity,
                              'room_type': room_type, 'features': features}
                )
                messages.success(request, f'Room {room_number} added.')
            else:
                messages.error(request, 'Room number is required.')
        return redirect(f"{reverse('admin_academic_planner')}?dept={department.pk}&sem={selected_semester}&step={request.POST.get('step', 1)}")

    college = _get_admin_college(request)
    faculty = Faculty.objects.filter(department__college=college).select_related('user', 'department').order_by('department__code', 'user__first_name') if department else Faculty.objects.none()
    subjects = Subject.objects.filter(department=department, semester=selected_semester).order_by('name') if department else Subject.objects.none()
    subject_assignments = FacultySubject.objects.filter(subject__in=subjects).select_related('subject', 'faculty__user').order_by('subject__name')
    availability = FacultyAvailability.objects.filter(faculty__in=faculty).select_related('faculty__user').order_by('faculty__user__first_name', 'day_of_week', 'start_time')
    timetable_entries = Timetable.objects.filter(subject__in=subjects).select_related('subject', 'faculty__user', 'classroom').order_by('day_of_week', 'start_time')
    college_breaks = TimetableBreak.objects.filter(
        Q(applies_to_all=True) | Q(department=department),
        college=college,
    ).order_by('day_of_week', 'start_time') if college and department else TimetableBreak.objects.none()
    classrooms = Classroom.objects.filter(college=college).order_by('building', 'room_number') if college else Classroom.objects.none()
    sections = Section.objects.filter(department=department, semester=selected_semester).order_by('label') if department else Section.objects.none()
    section_mappings = SectionSubjectFacultyMap.objects.filter(
        section__department=department,
        section__semester=selected_semester,
        subject__semester=selected_semester,
    ).select_related('section', 'subject', 'faculty__user', 'faculty__department', 'classroom').order_by('section__label', 'subject__name') if department else SectionSubjectFacultyMap.objects.none()
    mapped_subject_ids = section_mappings.values_list('subject_id', flat=True) if department else []
    unmapped_subjects = subjects.exclude(id__in=mapped_subject_ids) if department else Subject.objects.none()
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
    regulations = Regulation.objects.filter(college=college).order_by('-effective_from_year', 'name') if college else Regulation.objects.none()

    return render(request, 'admin_panel/academic_planner.html', {
        'departments': departments,
        'department': department,
        'selected_semester': selected_semester,
        'faculty': faculty,
        'subjects': subjects,
        'subject_assignments': subject_assignments,
        'sections': sections,
        'section_mappings': section_mappings,
        'unmapped_subjects': unmapped_subjects,
        'availability': availability,
        'timetable_entries': timetable_entries,
        'timetable_matrix': timetable_matrix,
        'college_breaks': college_breaks,
        'classrooms': classrooms,
        'section_strength_summary': section_strength_summary,
        'regulations': regulations,
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
    csv_file = request.FILES.get('timetable_csv') or request.FILES.get('csv_file')

    if not csv_file:
        messages.error(request, 'No file uploaded.')
        return redirect(f"{reverse('admin_academic_planner')}?dept={dept_id}&sem={semester}&step=4")

    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'Only .csv files are accepted.')
        return redirect(f"{reverse('admin_academic_planner')}?dept={dept_id}&sem={semester}&step=4")

    VALID_DAYS = {'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'}

    # Pre-fetch lookups for this dept/semester
    subject_map = {s.code.upper(): s for s in Subject.objects.filter(department=department, semester=semester)}
    # Fix 5 — allow any-dept faculty in CSV (matches UI behaviour where any-college faculty can be assigned)
    faculty_map = {f.employee_id.upper(): f for f in Faculty.objects.filter(department__college=college)}
    room_map    = {r.room_number.upper(): r for r in Classroom.objects.filter(college=college)}

    created = skipped = errors = 0
    error_lines = []

    try:
        decoded = csv_file.read().decode('utf-8-sig').splitlines()
    except UnicodeDecodeError:
        messages.error(request, 'File encoding error. Save the CSV as UTF-8 and try again.')
        return redirect(f"{reverse('admin_academic_planner')}?dept={dept_id}&sem={semester}&step=4")

    reader = csv.DictReader(decoded)
    required_cols = {'day', 'start_time', 'end_time', 'subject_code', 'faculty_employee_id', 'room_number'}
    if not required_cols.issubset({c.strip().lower() for c in (reader.fieldnames or [])}):
        messages.error(request, f'CSV must have columns: {", ".join(sorted(required_cols))}')
        return redirect(f"{reverse('admin_academic_planner')}?dept={dept_id}&sem={semester}&step=4")

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
        section_val = (row.get('section') or '').strip().upper()
        _, was_created = Timetable.objects.update_or_create(
            subject=subject, day_of_week=day, start_time=start_time,
            defaults={
                'faculty': faculty,
                'end_time': end_time,
                'classroom': classroom,
                'section': section_val,
                'generation_mode': 'manual',
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

    return redirect(f"{reverse('admin_academic_planner')}?dept={dept_id}&sem={semester}&step=4")


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
    departments = _scope_departments(request).order_by('name')
    students_base = Student.objects.select_related('user', 'department').filter(
        department__in=departments,
        is_deleted=False,
        status='ACTIVE',
    ).order_by('roll_number')
    year_options = list(
        students_base.order_by('-admission_year').values_list('admission_year', flat=True).distinct()
    )

    filter_source = request.POST if request.method == 'POST' else request.GET
    selected_year = (filter_source.get('year') or '').strip()
    selected_department = (filter_source.get('department') or '').strip()

    filtered_students = students_base
    if selected_year:
        filtered_students = filtered_students.filter(admission_year=selected_year)
    if selected_department:
        filtered_students = filtered_students.filter(department_id=selected_department)
    filtered_students = list(filtered_students)

    preview_students = []
    preview_academic_year = ''
    if filtered_students:
        preview_academic_year = _student_academic_year(filtered_students[0])
        existing_pairs = set(
            Fee.objects.filter(student__in=filtered_students).values_list('student_id', 'semester')
        )
        for student in filtered_students:
            preview_students.append({
                'pk': student.pk,
                'roll_number': student.roll_number,
                'name': student.user.get_full_name() or student.user.username,
                'semester': student.current_semester,
                'department_code': student.department.code,
                'has_fee_record': (student.pk, student.current_semester) in existing_pairs,
            })

    if request.method == 'POST':
        academic_year = request.POST.get('academic_year', '').strip()
        total_amount = _safe_decimal(request.POST.get('total_amount', 0) or 0)
        component_amounts = {
            key: _safe_decimal(request.POST.get(f'comp_{key}', 0) or 0)
            for key, _, _ in FEE_COMPONENTS
        }
        component_total = sum(component_amounts.values(), Decimal('0'))
        payload_errors = _validate_fee_payload(float(total_amount), 0.0, None, academic_year)

        if not selected_year or not selected_department:
            messages.error(request, 'Select admission year and department first.')
        elif not filtered_students:
            messages.error(request, 'No active students found for the selected year and department.')
        elif payload_errors:
            for error in payload_errors:
                messages.error(request, error)
        elif component_total > 0 and abs(component_total - total_amount) > Decimal('0.01'):
            messages.error(request, 'Fee component total must match the total fee amount.')
        else:
            department = get_object_or_404(departments, pk=selected_department)
            conflicting_fees = []
            existing_fees = {
                (fee.student_id, fee.semester): fee
                for fee in Fee.objects.filter(
                    student__in=filtered_students,
                    semester__in=[student.current_semester or 1 for student in filtered_students],
                )
            }
            for student in filtered_students:
                semester = student.current_semester or 1
                existing_fee = existing_fees.get((student.pk, semester))
                if existing_fee and Decimal(str(existing_fee.paid_amount)) > total_amount:
                    conflicting_fees.append(student.roll_number)

            if conflicting_fees:
                messages.error(
                    request,
                    'Cannot reduce total fee below already paid amount for: ' + ', '.join(conflicting_fees[:5]),
                )
                return render(request, 'admin_panel/fee_form.html', {
                    'action': 'Add',
                    'fee_components': FEE_COMPONENTS,
                    'departments': departments,
                    'year_options': year_options,
                    'selected_year': selected_year,
                    'selected_department': selected_department,
                    'preview_students': preview_students,
                    'preview_count': len(preview_students),
                    'preview_academic_year': preview_academic_year,
                    'breakdown_map': {},
                })

            created_count = 0
            updated_count = 0
            semester_structures = {}

            with transaction.atomic():
                for student in filtered_students:
                    semester = student.current_semester or 1
                    structure = semester_structures.get(semester)
                    if structure is None:
                        structure, _ = FeeStructure.objects.get_or_create(
                            college=department.college,
                            department=department,
                            semester=semester,
                            defaults={'total_fees': float(total_amount)},
                        )
                        structure.total_fees = float(total_amount)
                        structure.save(update_fields=['total_fees'])
                        semester_structures[semester] = structure

                        for key, _, _ in FEE_COMPONENTS:
                            amount = component_amounts[key]
                            if amount > Decimal('0'):
                                FeeBreakdown.objects.update_or_create(
                                    structure=structure,
                                    category=key,
                                    defaults={'amount': float(amount)},
                                )
                            else:
                                FeeBreakdown.objects.filter(structure=structure, category=key).delete()

                    fee, created = Fee.objects.get_or_create(
                        student=student,
                        semester=semester,
                        defaults={
                            'total_amount': float(total_amount),
                            'paid_amount': 0.0,
                            'academic_year': academic_year or _student_academic_year(student, semester),
                        },
                    )
                    if created:
                        created_count += 1
                    else:
                        fee.total_amount = float(total_amount)
                        fee.academic_year = academic_year or _student_academic_year(student, semester)
                        updated_count += 1
                    _sync_fee_status(fee)
                    fee.save()

            _audit(
                'OTHER',
                request.user,
                f'Bulk fee structure processed for {department.code} {selected_year}',
                college=department.college,
                request=request,
                new_value={
                    'students': len(filtered_students),
                    'created': created_count,
                    'updated': updated_count,
                    'total_amount': float(total_amount),
                    'academic_year': academic_year or preview_academic_year,
                },
            )

            messages.success(
                request,
                f'Fee records processed for {len(filtered_students)} student(s): {created_count} created, {updated_count} updated.'
            )
            return redirect('/dashboard/admin/#finance')

    return render(request, 'admin_panel/fee_form.html', {
        'action': 'Add',
        'fee_components': FEE_COMPONENTS,
        'departments': departments,
        'year_options': year_options,
        'selected_year': selected_year,
        'selected_department': selected_department,
        'preview_students': preview_students,
        'preview_count': len(preview_students),
        'preview_academic_year': preview_academic_year,
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
        total_amount = _safe_decimal(request.POST.get('total_amount', fee.total_amount) or fee.total_amount)
        paid_amount = _safe_decimal(request.POST.get('paid_amount', fee.paid_amount) or fee.paid_amount)
        semester = _safe_int(request.POST.get('semester', '')) or fee.semester or fee.student.current_semester or None
        academic_year = request.POST.get('academic_year', fee.academic_year or '').strip()
        component_amounts = {
            key: _safe_decimal(request.POST.get(f'comp_{key}', 0) or 0)
            for key, _, _ in FEE_COMPONENTS
        }
        component_total = sum(component_amounts.values(), Decimal('0'))
        payload_errors = _validate_fee_payload(float(total_amount), float(paid_amount), semester, academic_year)

        if component_total > 0 and abs(component_total - total_amount) > Decimal('0.01'):
            payload_errors.append('Fee component total must match the total fee amount.')

        if payload_errors:
            for error in payload_errors:
                messages.error(request, error)
        else:
            target_structure, _ = FeeStructure.objects.get_or_create(
                college=fee.student.department.college,
                department=fee.student.department,
                semester=semester,
                defaults={'total_fees': float(total_amount)},
            )
            old_snapshot = {
                'total_amount': fee.total_amount,
                'paid_amount': fee.paid_amount,
                'semester': fee.semester,
                'academic_year': fee.academic_year,
            }
            fee.total_amount = float(total_amount)
            fee.paid_amount = float(paid_amount)
            fee.semester = semester
            fee.academic_year = academic_year
            _sync_fee_status(fee)
            fee.save()

            for key, label, _ in FEE_COMPONENTS:
                amt = component_amounts[key]
                if amt > Decimal('0'):
                    FeeBreakdown.objects.update_or_create(
                        structure=target_structure, category=key,
                        defaults={'amount': float(amt)}
                    )
                else:
                    FeeBreakdown.objects.filter(structure=target_structure, category=key).delete()

            target_structure.total_fees = float(total_amount)
            target_structure.save(update_fields=['total_fees'])

            _audit(
                'OTHER',
                request.user,
                f'Fee updated for {fee.student.roll_number}',
                student=fee.student,
                college=fee.student.department.college,
                request=request,
                old_value=old_snapshot,
                new_value={
                    'total_amount': fee.total_amount,
                    'paid_amount': fee.paid_amount,
                    'semester': fee.semester,
                    'academic_year': fee.academic_year,
                    'status': fee.status,
                },
            )

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
    return render(request, 'admin_panel/announcement_form.html', {
        'college': college,
        'branding': _get_college_branding(college),
    })


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
    today = timezone.now().date()
    exams_qs = _scope_exams(request).select_related('created_by').order_by('-start_date', '-id')
    page_obj = _paginate_queryset(request, exams_qs, per_page=20)
    departments = Department.objects.filter(college=college).order_by('name') if college else Department.objects.none()
    return render(request, 'admin_panel/exams.html', {
        'exams': page_obj.object_list,
        'exams_page': page_obj,
        'college': college,
        'branding': _get_college_branding(college),
        'departments': departments,
        'exam_summary': _enterprise_summary(exams_qs.count(), page_obj),
        'upcoming_count': exams_qs.filter(start_date__gt=today).count(),
        'ongoing_count': exams_qs.filter(start_date__lte=today, end_date__gte=today).count(),
        'completed_count': exams_qs.filter(end_date__lt=today).count(),
        'published_count': exams_qs.count(),
    })


@login_required
def admin_exam_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    if request.method == 'POST':
        name       = request.POST.get('name', '').strip()
        semester_raw = request.POST.get('semester')
        semester = _safe_int(semester_raw)
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        effective_college = college or _get_user_college(request.user)
        errors, parsed_start_date, parsed_end_date = _validate_exam_payload(
            name,
            semester,
            start_date,
            end_date,
            effective_college,
        )
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            exam = Exam.objects.create(
                college=effective_college,
                name=name,
                semester=semester,
                start_date=parsed_start_date,
                end_date=parsed_end_date,
                created_by=request.user,
            )
            _audit(
                'OTHER',
                request.user,
                f'Exam created: {exam.name} (Sem {exam.semester})',
                college=effective_college,
                request=request,
                new_value={
                    'exam_id': exam.pk,
                    'start_date': str(exam.start_date),
                    'end_date': str(exam.end_date),
                },
            )
            messages.success(request, f'Exam "{name}" created.')
            return redirect('/dashboard/admin/#exams')
    return render(request, 'admin_panel/exam_form.html', {
        'college': college,
        'branding': _get_college_branding(college),
    })


@login_required
def admin_exam_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    exam = get_object_or_404(_scope_exams(request), pk=pk)
    if request.method == 'POST':
        _audit(
            'OTHER',
            request.user,
            f'Exam deleted: {exam.name} (Sem {exam.semester})',
            college=exam.college,
            request=request,
            old_value={
                'start_date': str(exam.start_date),
                'end_date': str(exam.end_date),
            },
        )
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
    try:
        report.file.save(filename, ContentFile(payload), save=True)
    except OSError:
        # The download should still work if local archival storage is unavailable.
        pass

    response = HttpResponse(payload, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    _audit(
        'OTHER',
        request.user,
        f'Report exported: {report_type}',
        college=college,
        request=request,
        new_value={'filename': filename, 'report_type': system_report_type},
    )
    return response


def system_health(request):
    db_ok = True
    db_error = ''
    pending_migrations = None
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        executor = MigrationExecutor(connections['default'])
        pending_migrations = len(executor.migration_plan(executor.loader.graph.leaf_nodes()))
    except Exception as exc:
        db_ok = False
        db_error = str(exc)

    status_label = 'ok' if db_ok and not pending_migrations else 'degraded'
    response_status = 200 if db_ok else 503
    return JsonResponse({
        'status': status_label,
        'application': 'studentmanagementsystem',
        'version': getattr(settings, 'APP_VERSION', 'dev'),
        'timestamp': timezone.now().isoformat(),
        'database': 'ok' if db_ok else 'error',
        'database_error': db_error,
        'pending_migrations': pending_migrations,
        'debug': settings.DEBUG,
        'environment': os.environ.get('DJANGO_ENV', 'development'),
    }, status=response_status)


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
        'announcements': _scope_announcements_for_college(college).order_by('-created_at')[:10],
        'notifications': Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:20],
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
        # Build seating arrangement: sort eligible students by roll number, assign rooms
        eligible_students = []
        for student in students_qs:
            att = att_map.get(student.id, {'total': 0, 'present': 0})
            pct = round(att['present'] / att['total'] * 100, 1) if att['total'] > 0 else 0
            has_dues = student.id in fee_dues
            exam_rule = _get_attendance_rule(ec.college, student.department, exam.semester)
            threshold = exam_rule.effective_min_overall
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
            eligible_students.append((student, pct, has_dues, status))

        # Auto-assign seats to ISSUED students using available classrooms
        classrooms = list(Classroom.objects.filter(
            college=ec.college
        ).order_by('room_number'))
        seat_map = {}  # student_id -> (room_number, seat_number, row_number)
        if classrooms:
            room_idx = 0
            seat_num = 1
            for student, pct, has_dues, status in eligible_students:
                if status != 'ISSUED':
                    continue
                if room_idx >= len(classrooms):
                    break
                room = classrooms[room_idx]
                capacity = room.capacity or 30
                row = chr(65 + ((seat_num - 1) // 10))  # A, B, C, ...
                seat_in_row = ((seat_num - 1) % 10) + 1
                seat_map[student.id] = (room.room_number, f'{row}{seat_in_row}', row)
                seat_num += 1
                if seat_num > capacity:
                    room_idx += 1
                    seat_num = 1

        for student, pct, has_dues, status in eligible_students:
            room_no, seat_no, row_no = seat_map.get(student.id, ('', '', ''))
            ht, was_created = HallTicket.objects.update_or_create(
                student=student, exam=exam,
                defaults={
                    'status': status, 'attendance_pct': pct,
                    'has_fee_dues': has_dues,
                    'issued_at': timezone.now() if status == 'ISSUED' else None,
                    'generated_by': request.user,
                    'room_number': room_no,
                    'seat_number': seat_no,
                    'row_number': row_no,
                }
            )
            if was_created:
                created += 1
            else:
                updated += 1
        messages.success(request, f'Hall tickets generated: {created} new, {updated} updated. Seats auto-assigned.')
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
                affected_students = list(marks_qs.values_list('student_id', flat=True).distinct())
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
                applied_count = 0
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
                    applied_count += 1
                # Recalculate SGPA for all affected students after moderation
                for sid in affected_students:
                    student_obj = Student.objects.filter(pk=sid).first()
                    if student_obj:
                        sgpa, total_credits = _compute_sgpa(student_obj, exam.semester, exam)
                        Result.objects.filter(student_id=sid, semester=exam.semester).update(
                            gpa=sgpa, sgpa=sgpa, total_credits=total_credits
                        )
                mod.applied = True
                mod.applied_by = request.user
                mod.applied_at = timezone.now()
                mod.save()
                _audit('MARKS_UPDATED', request.user,
                       f"Moderation applied: {mod.subject.code} {mod.get_moderation_type_display()} {mod.value}. Reason: {mod.reason}",
                       college=ec.college, request=request)
                messages.success(request, f'Moderation applied to {applied_count} marks records. SGPA recalculated.')
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
                # Pre-fetch student→department map for per-dept scheme lookup
                student_dept_map = {
                    s.id: s.department
                    for s in students_qs
                }
                student_obj_map = {s.id: s for s in students_qs}
                scheme_cache = {}
                for sid in student_ids:
                    m = marks_map.get(sid, {'total_obtained': 0, 'total_max': 0})
                    obtained = m['total_obtained'] or 0
                    max_m = m['total_max'] or 0
                    pct = round(obtained / max_m * 100, 1) if max_m > 0 else 0
                    dept = student_dept_map.get(sid)
                    if dept and dept.id not in scheme_cache:
                        scheme_cache[dept.id] = _get_evaluation_scheme(ec.college, dept)
                    _scheme = scheme_cache.get(dept.id if dept else None) or _get_evaluation_scheme(ec.college)
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
                    student_obj = student_obj_map.get(sid) or Student.objects.get(pk=sid)
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


@login_required
def exam_profile(request):
    """Signed-in examination officer profile."""
    ec = _exam_controller_guard(request)
    if not ec:
        messages.error(request, 'Exam Department access not found. Contact admin.')
        return redirect('dashboard')

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.email = request.POST.get('email', '').strip()
        request.user.save(update_fields=['first_name', 'last_name', 'email'])

        ec.phone_number = request.POST.get('phone_number', '').strip()
        ec.save(update_fields=['phone_number'])
        messages.success(request, 'Profile updated.')
        return redirect('exam_profile')

    scoped_departments = []
    if isinstance(ec, ExamStaff):
        scoped_departments = list(ec.departments.all().order_by('name'))

    recent_log = ExamStaffLog.objects.filter(staff=ec).select_related('exam')[:10] if isinstance(ec, ExamStaff) else []

    return render(request, 'exam/profile.html', {
        'ec': ec,
        'college': ec.college,
        'scoped_departments': scoped_departments,
        'recent_log': recent_log,
        'branding': _get_college_branding(ec.college),
    })


# ── EXAM STAFF MANAGEMENT ─────────────────────────────────────────────────────

@login_required
def exam_staff_list(request):
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
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
    roles = ExamStaff.EXAM_ROLE_CHOICES

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        exam_role = request.POST.get('exam_role', 'COORDINATOR')
        employee_id = request.POST.get('employee_id', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        dept_ids = request.POST.getlist('departments')

        form_context = {'ec': ec, 'departments': departments, 'roles': roles, 'branding': _get_college_branding(college)}

        if not username or not first_name or not last_name or not employee_id:
            messages.error(request, 'First name, last name, username, and employee ID are required.')
            return render(request, 'exam/staff_form.html', form_context)

        user = User.objects.filter(username=username).first()
        if user and ExamStaff.objects.filter(user=user).exists():
            messages.error(request, f'{username} is already an exam staff member.')
            return render(request, 'exam/staff_form.html', form_context)

        if ExamStaff.objects.filter(employee_id=employee_id).exists():
            messages.error(request, f'Employee ID "{employee_id}" already exists.')
            return render(request, 'exam/staff_form.html', form_context)

        generated_password = ''
        with transaction.atomic():
            if user:
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                if password:
                    user.set_password(password)
                user.save()
            else:
                generated_password = password or get_random_string(10)
                user = User.objects.create_user(
                    username=username,
                    password=generated_password,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                )

            staff = ExamStaff.objects.create(
                user=user, college=college, exam_role=exam_role,
                employee_id=employee_id, phone_number=phone,
            )
            if dept_ids:
                staff.departments.set(Department.objects.filter(pk__in=dept_ids, college=college))

            UserRole.objects.update_or_create(user=user, defaults={'role': 7, 'college': college})

            ExamStaffLog.objects.create(
                staff=ec if isinstance(ec, ExamStaff) else None,
                action='STAFF_ADDED',
                description=f'Added {user.get_full_name()} as {staff.get_exam_role_display()}',
            )

        if generated_password:
            messages.success(request, f'{user.get_full_name()} added as {staff.get_exam_role_display()}. Temporary password: {generated_password}')
        else:
            messages.success(request, f'{user.get_full_name()} added as {staff.get_exam_role_display()}.')
        return redirect('exam_staff_list')

    return render(request, 'exam/staff_form.html', {
        'ec': ec, 'departments': departments, 'roles': roles,
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
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        p = request.POST
        dept_id  = p.get('department') or None
        semester = _safe_int(p.get('semester')) if p.get('semester') else None

        if AttendanceRule.objects.filter(college=college, department_id=dept_id, semester=semester).exists():
            if is_ajax:
                return JsonResponse({'ok': False, 'error': 'A rule for this department/semester combination already exists.'})
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
            if is_ajax:
                return JsonResponse({'ok': True})
            messages.success(request, 'Attendance rule created.')
            return redirect('admin_attendance_rules')

    if is_ajax:
        return JsonResponse({'ok': False, 'error': 'Invalid request.'})
    return redirect('admin_attendance_rules')


@login_required
def admin_attendance_rule_edit(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    rule = get_object_or_404(AttendanceRule, pk=pk, college=college)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

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
        if is_ajax:
            return JsonResponse({'ok': True})
        messages.success(request, 'Attendance rule updated.')
        return redirect('admin_attendance_rules')

    if is_ajax:
        return JsonResponse({'ok': False, 'error': 'Invalid request.'})
    return redirect('admin_attendance_rules')


@login_required
def admin_attendance_rule_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    rule = get_object_or_404(AttendanceRule, pk=pk, college=_get_admin_college(request))
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if request.method == 'POST':
        rule.delete()
        if is_ajax:
            return JsonResponse({'ok': True})
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
            ex_id = request.POST.get('exemption_id')
            ex = get_object_or_404(AttendanceExemption, pk=ex_id, student__department=hod.department)
            if action in ('APPROVED', 'REJECTED'):
                ex.status = action
                ex.reviewed_by = request.user
                ex.review_note = note
                ex.save()
                messages.success(request, f'Exemption {action.lower()}.')

        # Re-fetch after POST so partial re-render shows updated state
        exemptions = AttendanceExemption.objects.filter(
            student__department=hod.department
        ).select_related('student__user').order_by('-created_at')[:50]

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            ctx = {'exemptions': exemptions, 'hod': hod,
                   'college': hod.department.college,
                   'branding': _get_college_branding(hod.department.college)}
            return render(request, 'attendance/hod_exemptions_partial.html', ctx)
        return redirect('hod_exemptions')

    ctx = {
        'exemptions': exemptions, 'hod': hod,
        'college': hod.department.college,
        'branding': _get_college_branding(hod.department.college),
    }
    if request.GET.get('partial') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'attendance/hod_exemptions_partial.html', ctx)
    return render(request, 'attendance/hod_exemptions.html', ctx)


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

    ctx = {
        'rows': rows, 'hod': hod, 'dept': dept,
        'college': college,
        'semester_filter': semester_filter,
        'semesters': semesters,
        'branding': _get_college_branding(college),
    }
    if request.GET.get('partial') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'attendance/hod_defaulters_partial.html', ctx)
    return render(request, 'attendance/hod_defaulters.html', ctx)


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


# ── GRACE MARKS ───────────────────────────────────────────────────────────────

@login_required
def exam_grace_marks_overview(request):
    ec = _exam_controller_guard(request)
    if not ec or not ec.can_verify:
        return redirect('exam_dashboard')

    exams = Exam.objects.filter(college=ec.college).order_by('-start_date')
    rows = []
    for exam in exams:
        rows.append({
            'exam': exam,
            'marks_count': Marks.objects.filter(exam=exam).count(),
            'grace_count': GraceMarksApplication.objects.filter(marks__exam=exam, status='APPLIED').count(),
        })

    return render(request, 'exam/exam_picker.html', {
        'ec': ec,
        'rows': rows,
        'mode': 'grace',
        'page_title': 'Grace Marks',
        'page_sub': 'Choose an exam to review and apply grace marks',
        'empty_text': 'No exams available for grace marks yet.',
        'branding': _get_college_branding(ec.college),
    })


@login_required
def exam_grace_marks(request, exam_id):
    """COE applies grace marks to borderline failing students per subject."""
    ec = _exam_controller_guard(request)
    if not ec or not ec.can_verify:
        return redirect('exam_dashboard')
    exam = get_object_or_404(Exam, pk=exam_id, college=ec.college)

    # Only allow if results are computed (DRAFT or VERIFIED), not yet published
    freeze_rec = ResultFreeze.objects.filter(college=ec.college, exam=exam).first()
    if freeze_rec and freeze_rec.is_frozen:
        messages.error(request, 'Results are frozen. Unfreeze before applying grace marks.')
        return redirect('exam_results', exam_id=exam.pk)

    # Get grace rule for this college's default scheme
    scheme = EvaluationScheme.objects.filter(college=ec.college, is_active=True).first()
    grace_rule = GraceMarksRule.objects.filter(scheme=scheme).first() if scheme else None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'apply':
            marks_id = request.POST.get('marks_id')
            grace_amount = request.POST.get('grace_amount', '').strip()
            reason = request.POST.get('reason', '').strip()

            try:
                grace_val = float(grace_amount)
                if grace_val <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                messages.error(request, 'Enter a valid positive grace amount.')
                return redirect('exam_grace_marks', exam_id=exam.pk)

            marks_obj = get_object_or_404(Marks, pk=marks_id, exam=exam)

            # Validate against rule limits
            if grace_rule:
                if grace_val > grace_rule.max_grace_per_subject:
                    messages.error(request, f'Grace cannot exceed {grace_rule.max_grace_per_subject} per subject.')
                    return redirect('exam_grace_marks', exam_id=exam.pk)
                if grace_rule.apply_only_if_failing:
                    pct = (marks_obj.marks_obtained / marks_obj.max_marks * 100) if marks_obj.max_marks else 0
                    passing_min = scheme.overall_passing_min if scheme else 40.0
                    if pct >= passing_min:
                        messages.error(request, 'Grace marks can only be applied to failing students.')
                        return redirect('exam_grace_marks', exam_id=exam.pk)

            with transaction.atomic():
                # Check if already applied
                existing = GraceMarksApplication.objects.filter(
                    marks=marks_obj, status='APPLIED'
                ).first()
                if existing:
                    messages.warning(request, 'Grace marks already applied for this student/subject.')
                    return redirect('exam_grace_marks', exam_id=exam.pk)

                app = GraceMarksApplication.objects.create(
                    marks=marks_obj,
                    rule=grace_rule,
                    grace_amount=grace_val,
                    reason=reason,
                    status='APPLIED',
                    requested_by=request.user,
                    approved_by=request.user,
                    applied_at=timezone.now(),
                )

                # Apply to marks
                old_marks = marks_obj.marks_obtained
                marks_obj.marks_obtained = min(marks_obj.marks_obtained + grace_val, marks_obj.max_marks)
                marks_obj.grade = _calculate_grade(marks_obj.marks_obtained, marks_obj.max_marks)
                marks_obj.grade_point = _grade_to_point(marks_obj.grade)
                marks_obj.save(update_fields=['marks_obtained', 'grade', 'grade_point'])

                # Recalculate SGPA
                sgpa, total_credits = _compute_sgpa(marks_obj.student, marks_obj.subject.semester, exam)
                Result.objects.filter(
                    student=marks_obj.student, semester=marks_obj.subject.semester
                ).update(gpa=sgpa, sgpa=sgpa, total_credits=total_credits)

                _audit('MARKS_UPDATED', request.user,
                       f"Grace marks applied: {marks_obj.student.roll_number} {marks_obj.subject.code} +{grace_val} ({old_marks} → {marks_obj.marks_obtained})",
                       student=marks_obj.student, college=ec.college, request=request,
                       old_value=str(old_marks), new_value=str(marks_obj.marks_obtained))

            messages.success(request, f'Grace marks of {grace_val} applied to {marks_obj.student.roll_number} — {marks_obj.subject.code}.')
            return redirect('exam_grace_marks', exam_id=exam.pk)

    # Build list of borderline students (failing but close to passing)
    passing_min = scheme.overall_passing_min if scheme else 40.0
    dept_filter = request.GET.get('dept')
    subject_filter = request.GET.get('subject')

    marks_qs = Marks.objects.filter(exam=exam).select_related(
        'student__user', 'student__department', 'subject'
    ).order_by('student__roll_number', 'subject__name')

    if dept_filter:
        marks_qs = marks_qs.filter(student__department_id=dept_filter)
    if subject_filter:
        marks_qs = marks_qs.filter(subject_id=subject_filter)

    # Annotate with grace application status
    applied_ids = set(
        GraceMarksApplication.objects.filter(
            marks__exam=exam, status='APPLIED'
        ).values_list('marks_id', flat=True)
    )

    borderline = []
    for m in marks_qs:
        pct = (m.marks_obtained / m.max_marks * 100) if m.max_marks else 0
        gap = passing_min - pct
        borderline.append({
            'marks': m,
            'pct': round(pct, 1),
            'gap': round(gap, 1),
            'is_failing': pct < passing_min,
            'grace_applied': m.pk in applied_ids,
            'max_grace': grace_rule.max_grace_per_subject if grace_rule else 5,
        })

    # Sort: failing first, then by gap ascending
    borderline.sort(key=lambda x: (not x['is_failing'], x['gap']))

    departments = Department.objects.filter(college=ec.college, is_deleted=False).order_by('name')
    subjects = Subject.objects.filter(
        department__college=ec.college, semester=exam.semester
    ).order_by('name')

    return render(request, 'exam/grace_marks.html', {
        'ec': ec, 'exam': exam,
        'borderline': borderline,
        'grace_rule': grace_rule,
        'scheme': scheme,
        'passing_min': passing_min,
        'departments': departments,
        'subjects': subjects,
        'dept_filter': dept_filter,
        'subject_filter': subject_filter,
        'branding': _get_college_branding(ec.college),
    })


# ── RESULT VERSION HISTORY ────────────────────────────────────────────────────

@login_required
def exam_result_versions_overview(request):
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')

    exams = Exam.objects.filter(college=ec.college).order_by('-start_date')
    rows = []
    for exam in exams:
        result_ids = Result.objects.filter(
            semester=exam.semester,
            student__department__college=ec.college,
        ).values_list('id', flat=True)
        rows.append({
            'exam': exam,
            'marks_count': Marks.objects.filter(exam=exam).count(),
            'version_count': ResultVersion.objects.filter(result_id__in=result_ids).count(),
        })

    return render(request, 'exam/exam_picker.html', {
        'ec': ec,
        'rows': rows,
        'mode': 'versions',
        'page_title': 'Result History',
        'page_sub': 'Choose an exam to view result version history',
        'empty_text': 'No exams available for result history yet.',
        'branding': _get_college_branding(ec.college),
    })


@login_required
def exam_result_versions(request, exam_id):
    """COE views the full version history of results for an exam."""
    ec = _exam_controller_guard(request)
    if not ec:
        return redirect('dashboard')
    exam = get_object_or_404(Exam, pk=exam_id, college=ec.college)

    dept_filter = request.GET.get('dept')
    roll_filter = request.GET.get('roll', '').strip()

    results_qs = Result.objects.filter(
        semester=exam.semester,
        student__department__college=ec.college,
    ).select_related('student__user', 'student__department').order_by('student__roll_number')

    if dept_filter:
        results_qs = results_qs.filter(student__department_id=dept_filter)
    if roll_filter:
        results_qs = results_qs.filter(student__roll_number__icontains=roll_filter)

    # Prefetch versions
    result_ids = list(results_qs.values_list('id', flat=True))
    versions_map = {}
    for v in ResultVersion.objects.filter(result_id__in=result_ids).select_related('created_by').order_by('result_id', '-version_no'):
        versions_map.setdefault(v.result_id, []).append(v)

    rows = []
    for r in results_qs:
        rows.append({
            'result': r,
            'versions': versions_map.get(r.pk, []),
        })

    departments = Department.objects.filter(college=ec.college, is_deleted=False).order_by('name')

    return render(request, 'exam/result_versions.html', {
        'ec': ec, 'exam': exam, 'rows': rows,
        'departments': departments,
        'dept_filter': dept_filter,
        'roll_filter': roll_filter,
        'branding': _get_college_branding(ec.college),
    })


# ── FORMAL TRANSCRIPT PDF ─────────────────────────────────────────────────────

@login_required
def student_transcript_pdf(request):
    """Generate a formal academic transcript PDF for the student."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, KeepTogether
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    try:
        student = Student.objects.select_related('department__college', 'user').get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')

    college = student.department.college
    branding = _get_college_branding(college)
    PRIMARY_HEX = branding.primary_color if branding else '#0d7377'

    try:
        profile = student.user.studentprofile
    except Exception:
        profile = None

    # ── Data gathering ────────────────────────────────────────────────────────
    results = Result.objects.filter(student=student).order_by('semester')
    all_marks = (
        Marks.objects.filter(student=student)
        .select_related('subject')
        .order_by('subject__semester', 'subject__name')
    )
    marks_by_sem = {}
    for m in all_marks:
        marks_by_sem.setdefault(m.subject.semester, []).append(m)

    # Credit-weighted CGPA
    cgpa = None
    total_cp, total_cr = 0.0, 0
    for r in results:
        for m in marks_by_sem.get(r.semester, []):
            cr = m.subject.credits or 0
            total_cp += cr * _grade_to_point(m.grade or 'F')
            total_cr += cr
    if total_cr > 0:
        cgpa = round(total_cp / total_cr, 2)

    # ── Page setup ────────────────────────────────────────────────────────────
    # A4 usable width = 210 - 15*2 = 180 mm
    PAGE_W = 180 * mm
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=12*mm, bottomMargin=14*mm,
    )

    TEAL  = colors.HexColor(PRIMARY_HEX)
    DEEP  = colors.HexColor('#071e26')
    MUTED = colors.HexColor('#64748b')
    LIGHT = colors.HexColor('#f0fdfa')
    BORDER = colors.HexColor('#cbd5e1')
    WHITE = colors.white

    LABEL_STYLE = ParagraphStyle('lbl', fontName='Helvetica-Bold', fontSize=8,
                                  textColor=DEEP, leading=11)
    VALUE_STYLE = ParagraphStyle('val', fontName='Helvetica', fontSize=8,
                                  textColor=DEEP, leading=11)
    HDR_STYLE   = ParagraphStyle('hdr', fontName='Helvetica-Bold', fontSize=8,
                                  textColor=WHITE, leading=11)
    CELL_STYLE  = ParagraphStyle('cel', fontName='Helvetica', fontSize=8,
                                  textColor=DEEP, leading=11)

    def P(text, style=None, **kw):
        """Shorthand Paragraph factory. Pass a ParagraphStyle or keyword overrides."""
        if style is not None and not kw:
            return Paragraph(text, style)
        # Build a one-off style from keyword args
        s = ParagraphStyle('_p', **kw)
        return Paragraph(text, s)

    elems = []

    # ── 1. Header band ────────────────────────────────────────────────────────
    header_tbl = Table([[
        P(f'<b>{college.name}</b>',
          fontName='Helvetica-Bold', fontSize=14, textColor=WHITE, leading=18),
        P('<b>OFFICIAL TRANSCRIPT</b>',
          fontName='Helvetica-Bold', fontSize=11, textColor=WHITE,
          leading=14, alignment=TA_RIGHT),
    ]], colWidths=[PAGE_W * 0.62, PAGE_W * 0.38])
    header_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), TEAL),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING',   (0, 0), (0,  -1), 14),
        ('RIGHTPADDING',  (1, 0), (1,  -1), 14),
        ('LEFTPADDING',   (1, 0), (1,  -1), 6),
    ]))
    elems.append(header_tbl)
    elems.append(Spacer(1, 5*mm))

    # ── 2. Student info table ─────────────────────────────────────────────────
    # 4 columns: label | value | label | value
    # widths: 32 + 56 + 36 + 56 = 180 mm
    dob_str = (profile.date_of_birth.strftime('%d %b %Y')
               if profile and profile.date_of_birth else '—')
    full_name = student.user.get_full_name() or student.user.username

    info_rows = [
        [P('Student Name',    style=LABEL_STYLE),
         P(full_name,         style=VALUE_STYLE),
         P('Roll Number',     style=LABEL_STYLE),
         P(student.roll_number, style=VALUE_STYLE)],
        [P('Department',      style=LABEL_STYLE),
         P(student.department.name, style=VALUE_STYLE),
         P('Admission Year',  style=LABEL_STYLE),
         P(str(student.admission_year), style=VALUE_STYLE)],
        [P('Date of Birth',   style=LABEL_STYLE),
         P(dob_str,           style=VALUE_STYLE),
         P('Current Semester',style=LABEL_STYLE),
         P(str(student.current_semester), style=VALUE_STYLE)],
        [P('College',         style=LABEL_STYLE),
         P(college.name,      style=VALUE_STYLE),
         P('Status',          style=LABEL_STYLE),
         P(student.get_status_display(), style=VALUE_STYLE)],
    ]
    info_tbl = Table(info_rows, colWidths=[32*mm, 58*mm, 34*mm, 56*mm])
    info_tbl.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [WHITE, LIGHT]),
        ('GRID',           (0, 0), (-1, -1), 0.3, BORDER),
        ('TOPPADDING',     (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 5),
        ('LEFTPADDING',    (0, 0), (-1, -1), 7),
        ('RIGHTPADDING',   (0, 0), (-1, -1), 7),
        ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elems.append(info_tbl)
    elems.append(Spacer(1, 4*mm))
    elems.append(HRFlowable(width='100%', thickness=1, color=TEAL, spaceAfter=4*mm))

    # ── 3. Semester-wise marks ────────────────────────────────────────────────
    # col widths: Subject(60) Code(18) Credits(15) Marks(15) Max(13) %(14) Grade(14) GP(11) = 160mm
    # + 20mm left/right padding absorbed → fits 180mm
    COL_W = [60*mm, 18*mm, 15*mm, 15*mm, 13*mm, 14*mm, 14*mm, 11*mm]

    for r in results:
        sem_marks = marks_by_sem.get(r.semester, [])

        # Semester header row — teal band
        sem_label = (
            f'Semester {r.semester}'
            f'   SGPA: {r.sgpa:.2f}'
            f'   Percentage: {r.percentage:.1f}%'
            f'   Credits: {r.total_credits}'
        )
        sem_hdr = Table([[
            P(f'<b>{sem_label}</b>',
              fontName='Helvetica-Bold', fontSize=8.5, textColor=WHITE, leading=12),
        ]], colWidths=[PAGE_W])
        sem_hdr.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), TEAL),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING',   (0, 0), (-1, -1), 8),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ]))

        block = [sem_hdr]

        if sem_marks:
            # Column headers
            hdr_row = [
                P('<b>Subject</b>',  style=HDR_STYLE),
                P('<b>Code</b>',     style=HDR_STYLE),
                P('<b>Credits</b>',  style=HDR_STYLE),
                P('<b>Marks</b>',    style=HDR_STYLE),
                P('<b>Max</b>',      style=HDR_STYLE),
                P('<b>%</b>',        style=HDR_STYLE),
                P('<b>Grade</b>',    style=HDR_STYLE),
                P('<b>GP</b>',       style=HDR_STYLE),
            ]
            tbl_rows = [hdr_row]
            for m in sem_marks:
                pct = round(m.marks_obtained / m.max_marks * 100, 1) if m.max_marks else 0
                tbl_rows.append([
                    P(m.subject.name,                style=CELL_STYLE),
                    P(m.subject.code,                style=CELL_STYLE),
                    P(str(m.subject.credits or '—'), style=CELL_STYLE),
                    P(f'{m.marks_obtained:.0f}',     style=CELL_STYLE),
                    P(f'{m.max_marks:.0f}',          style=CELL_STYLE),
                    P(f'{pct:.1f}',                  style=CELL_STYLE),
                    P(m.grade or '—',                style=CELL_STYLE),
                    P(f'{m.grade_point:.1f}',        style=CELL_STYLE),
                ])

            marks_tbl = Table(tbl_rows, colWidths=COL_W)
            marks_tbl.setStyle(TableStyle([
                # Header row
                ('BACKGROUND',    (0, 0), (-1, 0),  TEAL),
                ('TEXTCOLOR',     (0, 0), (-1, 0),  WHITE),
                # Data rows
                ('ROWBACKGROUNDS',(0, 1), (-1, -1), [WHITE, LIGHT]),
                ('GRID',          (0, 0), (-1, -1), 0.3, BORDER),
                # Alignment — left for subject, center for all numeric cols
                ('ALIGN',         (0, 0), (0,  -1), 'LEFT'),
                ('ALIGN',         (1, 0), (-1, -1), 'CENTER'),
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                # Padding
                ('TOPPADDING',    (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING',   (0, 0), (0,  -1), 6),
                ('LEFTPADDING',   (1, 0), (-1, -1), 4),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
            ]))
            block.append(marks_tbl)
        else:
            block.append(
                P('No marks recorded for this semester.',
                  fontName='Helvetica', fontSize=8, textColor=MUTED,
                  leading=12, leftIndent=6)
            )

        block.append(Spacer(1, 3*mm))
        elems.append(KeepTogether(block))

    # ── 4. CGPA summary ───────────────────────────────────────────────────────
    elems.append(HRFlowable(width='100%', thickness=1, color=TEAL, spaceBefore=2*mm, spaceAfter=3*mm))

    if cgpa is not None:
        standing = ('Distinction' if cgpa >= 8.5 else
                    'First Class' if cgpa >= 7.0 else
                    'Second Class' if cgpa >= 6.0 else
                    'Pass' if cgpa >= 5.0 else 'Below Pass')
        # 3 rows × 2 cols — much cleaner than 6 cols in one row
        summary_rows = [
            [P('<b>Semesters Completed</b>', style=LABEL_STYLE),
             P(str(results.count()),         style=VALUE_STYLE)],
            [P('<b>CGPA</b>',                style=LABEL_STYLE),
             P(f'<b><font color="{PRIMARY_HEX}">{cgpa}</font></b>',
               fontName='Helvetica-Bold', fontSize=11, textColor=TEAL, leading=14)],
            [P('<b>Academic Standing</b>',   style=LABEL_STYLE),
             P(standing,                     style=VALUE_STYLE)],
        ]
        sum_tbl = Table(summary_rows, colWidths=[50*mm, 130*mm])
        sum_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), LIGHT),
            ('GRID',          (0, 0), (-1, -1), 0.3, BORDER),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING',   (0, 0), (-1, -1), 8),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elems.append(sum_tbl)

    # ── 5. Footer ─────────────────────────────────────────────────────────────
    elems.append(Spacer(1, 5*mm))
    elems.append(P(
        f'Generated on {timezone.localdate().strftime("%d %B %Y")}  |  {college.name}',
        fontName='Helvetica', fontSize=7, textColor=MUTED,
        leading=10, alignment=TA_CENTER,
    ))
    elems.append(P(
        'This is a computer-generated transcript. For official use, obtain a stamped copy from the Examination Department.',
        fontName='Helvetica', fontSize=6.5, textColor=MUTED,
        leading=9, alignment=TA_CENTER, spaceBefore=2,
    ))

    doc.build(elems)
    pdf_bytes = buf.getvalue()
    buf.close()
    roll = student.roll_number.replace('/', '-')
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transcript_{roll}.pdf"'
    response['Content-Length'] = str(len(pdf_bytes))
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response


# ── SEMESTER RESULT VIEWS ─────────────────────────────────────────────────────

@login_required
def admin_semester_results(request):
    if not _admin_guard(request):
        return redirect('dashboard')

    college = _get_admin_college(request)
    departments = _scope_departments(request).filter(is_deleted=False).order_by('name')
    academic_year_options = _get_semester_result_academic_year_options(college)
    selected_department = None
    selected_students = Student.objects.none()
    selected_subjects = Subject.objects.none()
    selected_batches = []
    current_batch = None

    academic_year = (request.GET.get('academic_year') or '').strip()
    department_id = (request.GET.get('department') or '').strip()
    semester = _safe_int(request.GET.get('semester'), default=None)

    if academic_year and department_id and semester:
        selected_department = departments.filter(pk=department_id).first()
        if selected_department:
            selected_students = _get_semester_result_students(college, selected_department, semester, academic_year)
            selected_subjects = _get_semester_result_subjects(selected_department, semester, academic_year)
            selected_batches = _dedupe_semester_result_batches(SemesterResultBatch.objects.filter(
                college=college,
                department=selected_department,
                academic_year=academic_year,
                semester=semester,
            ).select_related('uploaded_by', 'approved_by').prefetch_related('student_results'))
            current_batch = selected_batches[0] if selected_batches else None

    recent_batches = _dedupe_semester_result_batches(SemesterResultBatch.objects.filter(college=college).select_related(
        'department', 'uploaded_by', 'approved_by'
    ))[:20]

    return render(request, 'admin_panel/semester_results.html', {
        'college': college,
        'branding': _get_college_branding(college),
        'departments': departments,
        'academic_year_options': academic_year_options,
        'selected_department': selected_department,
        'academic_year': academic_year,
        'semester': semester,
        'selected_students': selected_students,
        'selected_subjects': selected_subjects,
        'selected_batches': selected_batches,
        'current_batch': current_batch,
        'recent_batches': recent_batches,
    })


@login_required
def admin_semester_result_template(request):
    if not _admin_guard(request):
        return redirect('dashboard')

    college = _get_admin_college(request)
    academic_year = (request.GET.get('academic_year') or '').strip()
    department_id = (request.GET.get('department') or '').strip()
    semester = _safe_int(request.GET.get('semester'), default=None)
    department = _scope_departments(request).filter(pk=department_id, is_deleted=False).first()

    if not (academic_year and department and semester):
        messages.error(request, 'Select academic year, department, and semester first.')
        return redirect('admin_semester_results')

    students = list(_get_semester_result_students(college, department, semester, academic_year))
    subjects = list(_get_semester_result_subjects(department, semester, academic_year))

    if not students:
        messages.error(request, 'No matching students found for the selected filters.')
        return redirect(_semester_result_redirect_url(academic_year, department.pk, semester))
    if not subjects:
        messages.error(request, 'No matching subjects found for the selected filters.')
        return redirect(_semester_result_redirect_url(academic_year, department.pk, semester))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="semester-result-template-{department.code}-sem-{semester}-{academic_year}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(_semester_result_fixed_headers() + _semester_result_subject_headers(subjects))
    for student in students:
        writer.writerow([
            student.roll_number,
            student.user.username,
            student.user.first_name,
            student.user.last_name,
            academic_year,
            department.code,
            semester,
            *([''] * len(subjects)),
        ])
    return response


@login_required
def admin_semester_result_upload(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('admin_semester_results')

    college = _get_admin_college(request)
    academic_year = (request.POST.get('academic_year') or '').strip()
    department_id = (request.POST.get('department') or '').strip()
    semester = _safe_int(request.POST.get('semester'), default=None)
    upload_file = request.FILES.get('result_file')
    department = _scope_departments(request).filter(pk=department_id, is_deleted=False).first()

    if not (academic_year and department and semester and upload_file):
        messages.error(request, 'Academic year, department, semester, and result file are required.')
        return redirect('admin_semester_results')

    students = list(_get_semester_result_students(college, department, semester, academic_year))
    subjects = list(_get_semester_result_subjects(department, semester, academic_year))

    base_redirect = (
        reverse('admin_semester_results') +
        f'?academic_year={academic_year}&department={department.pk}&semester={semester}'
    )

    if not students or not subjects:
        messages.error(request, 'The selected filters do not have matching students or subjects.')
        return redirect(base_redirect)

    try:
        upload_bytes = upload_file.read()
        decoded_rows = upload_bytes.decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_rows)
    except Exception:
        messages.error(request, 'Could not read the uploaded file. Please upload the latest CSV template.')
        return redirect(base_redirect)

    expected_headers = _semester_result_fixed_headers() + _semester_result_subject_headers(subjects)
    if reader.fieldnames != expected_headers:
        messages.error(request, 'The uploaded file does not match the current template for the selected filters.')
        return redirect(base_redirect)

    student_map = {s.roll_number.strip().upper(): s for s in students}
    rows = list(reader)
    if not rows:
        messages.error(request, 'The uploaded file is empty.')
        return redirect(base_redirect)

    processed_students = set()
    try:
        with transaction.atomic():
            existing_batches = SemesterResultBatch.objects.filter(
                college=college,
                department=department,
                academic_year=academic_year,
                semester=semester,
            ).order_by('-uploaded_at', '-id')
            batch = existing_batches.first()
            duplicate_ids = list(existing_batches.values_list('id', flat=True)[1:])

            if batch is None:
                batch = SemesterResultBatch(
                    college=college,
                    department=department,
                    academic_year=academic_year,
                    semester=semester,
                )
            else:
                batch.student_results.all().delete()
                if batch.generated_pdf:
                    batch.generated_pdf.delete(save=False)
                batch.generated_pdf = None

            batch.uploaded_by = request.user
            batch.status = 'UPLOADED'
            batch.student_count = len(students)
            batch.subject_count = len(subjects)
            batch.generated_at = None
            batch.approved_at = None
            batch.approved_by = None
            batch.source_file.save(upload_file.name or 'semester-result-upload.csv', ContentFile(upload_bytes), save=False)
            batch.save()

            if duplicate_ids:
                SemesterResultBatch.objects.filter(id__in=duplicate_ids).delete()

            for line_number, row in enumerate(rows, start=2):
                roll_number = (row.get('roll_number') or '').strip().upper()
                username = (row.get('username') or '').strip()
                first_name = (row.get('first_name') or '').strip()
                last_name = (row.get('last_name') or '').strip()
                row_year = (row.get('academic_year') or '').strip()
                row_dept = (row.get('department_code') or '').strip().upper()
                row_sem = _safe_int(row.get('semester'), default=None)

                if row_year != academic_year or row_dept != department.code.upper() or row_sem != semester:
                    raise ValueError(
                        f'Row {line_number}: file filters do not match selected academic year, department, and semester.'
                    )

                student = student_map.get(roll_number)
                if not student:
                    raise ValueError(f'Row {line_number}: roll number {roll_number} is not part of the selected cohort.')
                if student.user.username != username:
                    raise ValueError(f'Row {line_number}: username mismatch for {roll_number}.')

                transcript = SemesterResultStudent.objects.create(
                    batch=batch, student=student,
                    roll_number_snapshot=student.roll_number,
                    username_snapshot=username,
                    full_name_snapshot=(
                        f'{first_name} {last_name}'.strip() or student.user.get_full_name() or username
                    ),
                )

                total_marks = 0.0
                total_max = 0.0
                total_credits = 0
                total_credit_points = 0.0
                overall_pass = True

                for order, subject in enumerate(subjects, start=1):
                    header = f'{subject.code} - {subject.name}'
                    raw_mark = (row.get(header) or '').strip()
                    if raw_mark == '':
                        raise ValueError(f'Row {line_number}: missing mark for {subject.code}.')
                    try:
                        mark_value = float(raw_mark)
                    except ValueError:
                        raise ValueError(f'Row {line_number}: invalid mark for {subject.code}.')
                    if not (0 <= mark_value <= 100):
                        raise ValueError(f'Row {line_number}: {subject.code} mark must be between 0 and 100.')

                    grade = _calculate_grade(mark_value, 100)
                    grade_point = _grade_to_point(grade)
                    row_status = 'PASS' if grade != 'F' else 'FAIL'
                    credits = subject.credits or 0

                    SemesterResultSubject.objects.create(
                        student_result=transcript, subject=subject,
                        subject_code_snapshot=subject.code,
                        subject_name_snapshot=subject.name,
                        marks_obtained=mark_value, max_marks=100,
                        grade=grade, grade_point=grade_point,
                        status=row_status, credits=credits, display_order=order,
                    )

                    total_marks += mark_value
                    total_max += 100
                    total_credits += credits
                    total_credit_points += credits * grade_point
                    overall_pass = overall_pass and row_status == 'PASS'

                transcript.total_marks_obtained = round(total_marks, 2)
                transcript.total_max_marks = round(total_max, 2)
                transcript.percentage = round((total_marks / total_max) * 100, 2) if total_max else 0
                transcript.semester_credits = total_credits
                transcript.sgpa = round(total_credit_points / total_credits, 2) if total_credits else 0
                previous_results = list(Result.objects.filter(student=student).exclude(semester=semester))
                semester_count = len(previous_results) + 1
                transcript.cgpa = round(
                    (sum(r.sgpa for r in previous_results) + transcript.sgpa) / semester_count, 2
                ) if semester_count else transcript.sgpa
                transcript.overall_credits = sum(r.total_credits for r in previous_results) + total_credits
                transcript.result_status = 'PASS' if overall_pass else 'FAIL'
                transcript.save(update_fields=[
                    'total_marks_obtained', 'total_max_marks', 'percentage',
                    'semester_credits', 'sgpa', 'cgpa', 'overall_credits', 'result_status',
                ])
                processed_students.add(student.id)

            if len(processed_students) != len(student_map):
                missing = [s.roll_number for s in students if s.id not in processed_students]
                raise ValueError(
                    'File must contain every student in the cohort. Missing: ' + ', '.join(missing[:5])
                )

    except Exception as exc:
        messages.error(request, str(exc))
        return redirect(base_redirect)

    messages.success(request, f'Semester result data uploaded for {len(processed_students)} students.')
    return redirect(base_redirect)


@login_required
def admin_semester_result_generate(request, batch_id):
    if not _admin_guard(request):
        return redirect('dashboard')

    batch = get_object_or_404(
        SemesterResultBatch.objects.select_related('college', 'department'),
        pk=batch_id, college=_get_admin_college(request),
    )
    combined_pdf, pdf_map = _build_semester_result_preview_pdf(batch)
    timestamp = timezone.localtime(timezone.now()).strftime('%Y%m%d%H%M%S')
    batch.generated_pdf.save(
        f'semester-results-{batch.department.code}-sem-{batch.semester}-{batch.academic_year}-{timestamp}.pdf',
        ContentFile(combined_pdf), save=False,
    )
    batch.status = 'GENERATED'
    batch.generated_at = timezone.now()
    batch.save(update_fields=['generated_pdf', 'status', 'generated_at'])

    for transcript in batch.student_results.all():
        pdf_bytes = pdf_map.get(transcript.pk)
        if not pdf_bytes:
            continue
        transcript.pdf_file.save(
            f'{transcript.roll_number_snapshot}-sem-{batch.semester}-{batch.academic_year}.pdf',
            ContentFile(pdf_bytes), save=False,
        )
        transcript.status = 'GENERATED'
        transcript.save(update_fields=['pdf_file', 'status'])

    messages.success(request, 'Transcript preview generated successfully.')
    return redirect(_semester_result_redirect_url(batch.academic_year, batch.department_id, batch.semester))


@login_required
def admin_semester_result_view(request, batch_id):
    if not _admin_guard(request):
        return redirect('dashboard')

    batch = get_object_or_404(
        SemesterResultBatch.objects.select_related('college'),
        pk=batch_id, college=_get_admin_college(request),
    )
    if not batch.generated_pdf:
        messages.error(request, 'Generate the transcript preview first.')
        return redirect('admin_semester_results')

    response = HttpResponse(batch.generated_pdf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{batch.generated_pdf.name.rsplit("/", 1)[-1]}"'
    return response


@login_required
def admin_semester_result_source_download(request, batch_id):
    if not _admin_guard(request):
        return redirect('dashboard')

    batch = get_object_or_404(
        SemesterResultBatch.objects.select_related('college'),
        pk=batch_id, college=_get_admin_college(request),
    )
    if not batch.source_file:
        messages.error(request, 'Uploaded result file is not available for this batch.')
        return redirect(_semester_result_redirect_url(batch.academic_year, batch.department_id, batch.semester))

    response = HttpResponse(batch.source_file.read(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{batch.source_file.name.rsplit("/", 1)[-1]}"'
    return response


@login_required
def admin_semester_result_approve(request, batch_id):
    if not _admin_guard(request):
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('admin_semester_results')

    batch = get_object_or_404(
        SemesterResultBatch.objects.select_related('college', 'department'),
        pk=batch_id, college=_get_admin_college(request),
    )
    if not batch.generated_pdf:
        messages.error(request, 'Generate the transcript preview before approval.')
        return redirect('admin_semester_results')

    approval_time = timezone.now()
    with transaction.atomic():
        SemesterResultBatch.objects.filter(
            college=batch.college,
            department=batch.department,
            academic_year=batch.academic_year,
            semester=batch.semester,
        ).exclude(pk=batch.pk).delete()

        batch.status = 'APPROVED'
        batch.approved_at = approval_time
        batch.approved_by = request.user
        batch.save(update_fields=['status', 'approved_at', 'approved_by'])

        for transcript in batch.student_results.select_related('student'):
            SemesterResultStudent.objects.filter(
                student=transcript.student,
                batch__semester=batch.semester,
            ).exclude(batch=batch).delete()

            previous_results = list(Result.objects.filter(student=transcript.student).exclude(semester=batch.semester))
            semester_count = len(previous_results) + 1
            transcript.cgpa = round(
                (sum(r.sgpa for r in previous_results) + transcript.sgpa) / semester_count, 2
            ) if semester_count else transcript.sgpa
            transcript.overall_credits = sum(r.total_credits for r in previous_results) + transcript.semester_credits
            transcript.status = 'APPROVED'
            transcript.approved_at = approval_time
            transcript.approved_by = request.user
            transcript.save(update_fields=['cgpa', 'overall_credits', 'status', 'approved_at', 'approved_by'])

            Result.objects.update_or_create(
                student=transcript.student,
                semester=batch.semester,
                defaults={
                    'gpa': transcript.sgpa,
                    'sgpa': transcript.sgpa,
                    'total_marks': transcript.total_marks_obtained,
                    'percentage': transcript.percentage,
                    'total_credits': transcript.semester_credits,
                },
            )

    messages.success(request, 'Semester transcripts approved and published to students.')
    return redirect(_semester_result_redirect_url(batch.academic_year, batch.department_id, batch.semester))


@login_required
def student_semester_transcript_download(request, transcript_id):
    transcript = get_object_or_404(
        SemesterResultStudent.objects.select_related('student__user', 'batch'),
        pk=transcript_id, status='APPROVED', batch__status='APPROVED',
    )
    if (request.user != transcript.student.user
            and not _admin_guard(request)
            and not request.user.is_superuser):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    if not transcript.pdf_file:
        messages.error(request, 'Transcript file is not available yet.')
        return redirect('student_dashboard')

    response = HttpResponse(transcript.pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{transcript.pdf_file.name.rsplit("/", 1)[-1]}"'
    return response


@login_required
def student_hall_ticket_pdf(request, ht_id):
    """Render a printable hall ticket for the student."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    ht = get_object_or_404(HallTicket, pk=ht_id)

    # Only the student themselves (or admin/HOD) can download
    try:
        student = Student.objects.select_related('department__college', 'user').get(user=request.user)
    except Student.DoesNotExist:
        student = None

    if student and ht.student != student:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    if ht.status != 'ISSUED':
        messages.error(request, 'Hall ticket is not yet issued for this exam.')
        return redirect('student_dashboard')

    college = ht.student.department.college
    branding = _get_college_branding(college)
    PRIMARY = colors.HexColor(branding.primary_color if branding else '#0d7377')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)

    styles_h1 = ParagraphStyle('h1', fontSize=16, fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=4)
    styles_h2 = ParagraphStyle('h2', fontSize=12, fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=2)
    styles_sub = ParagraphStyle('sub', fontSize=9, fontName='Helvetica', alignment=TA_CENTER, spaceAfter=10, textColor=colors.grey)
    styles_label = ParagraphStyle('lbl', fontSize=9, fontName='Helvetica-Bold', alignment=TA_LEFT)
    styles_val = ParagraphStyle('val', fontSize=9, fontName='Helvetica', alignment=TA_LEFT)
    styles_note = ParagraphStyle('note', fontSize=8, fontName='Helvetica', alignment=TA_LEFT, leading=13, textColor=colors.grey)

    story = []
    story.append(Paragraph(college.name, styles_h1))
    story.append(Paragraph('HALL TICKET', styles_h2))
    story.append(Paragraph(f'{ht.exam.name} &mdash; Semester {ht.exam.semester}', styles_sub))
    story.append(HRFlowable(width='100%', thickness=1.5, color=PRIMARY, spaceAfter=10))

    # Student info table
    info_data = [
        [Paragraph('Name', styles_label), Paragraph(ht.student.user.get_full_name() or ht.student.user.username, styles_val),
         Paragraph('Roll Number', styles_label), Paragraph(ht.student.roll_number, styles_val)],
        [Paragraph('Branch', styles_label), Paragraph(ht.student.department.name, styles_val),
         Paragraph('Semester', styles_label), Paragraph(str(ht.exam.semester), styles_val)],
        [Paragraph('Examination', styles_label), Paragraph(ht.exam.name, styles_val),
         Paragraph('Month & Year', styles_label), Paragraph(ht.exam.start_date.strftime('%b %Y') if ht.exam.start_date else '—', styles_val)],
        [Paragraph('Room No.', styles_label), Paragraph(ht.room_number or '—', styles_val),
         Paragraph('Seat No.', styles_label), Paragraph(ht.seat_number or '—', styles_val)],
    ]
    info_table = Table(info_data, colWidths=[35*mm, 60*mm, 35*mm, 40*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10*mm))

    # Subjects
    story.append(Paragraph('<b>Subjects</b>', ParagraphStyle('sh', fontSize=10, fontName='Helvetica-Bold', spaceAfter=6)))
    subjects = Subject.objects.filter(
        department=ht.student.department,
        semester=ht.exam.semester,
    ).order_by('name')
    subj_data = [['#', 'Subject Code', 'Subject Name', 'Credits']]
    for i, s in enumerate(subjects, 1):
        subj_data.append([str(i), s.code, s.name, str(s.credits or '—')])
    subj_data.append(['', '', f'Total: {len(subjects)} subjects', ''])
    subj_table = Table(subj_data, colWidths=[10*mm, 30*mm, 100*mm, 20*mm])
    subj_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8fafc')]),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(subj_table)
    story.append(Spacer(1, 8*mm))

    # Instructions
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceAfter=6))
    story.append(Paragraph('<b>Instructions to be followed before the examination:</b>', styles_note))
    instructions = [
        'Code A: Possession of study material/mobile phone — "F" grade in the respective subject.',
        'Code B: Second offence — "F" grade in all subjects of that semester.',
        'Code C: Third offence — "F" grade in all subjects; allowed to appear after 6 months.',
        'Code D: Fourth offence — "F" grade in all subjects; allowed to appear after 1 year.',
    ]
    for inst in instructions:
        story.append(Paragraph(f'• {inst}', styles_note))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="hall-ticket-{ht.student.roll_number}-{ht.exam.pk}.pdf"'
    return response


# ── ADMIN HALL TICKET MANAGEMENT ─────────────────────────────────────────────

@login_required
def admin_hall_tickets(request):
    """College admin view to manage hall ticket generation across all exams."""
    if not _admin_guard(request):
        return redirect('dashboard')

    college = _get_admin_college(request)
    exams = Exam.objects.filter(college=college).order_by('-start_date')
    dept_filter = request.GET.get('dept')
    departments = Department.objects.filter(college=college, is_deleted=False).order_by('name')

    # Handle exemption approval/rejection from admin
    if request.method == 'POST':
        ov_id = request.POST.get('override_id')
        action = request.POST.get('action')
        note = request.POST.get('review_note', '').strip()
        if ov_id and action in ('APPROVED', 'REJECTED'):
            ov = get_object_or_404(EligibilityOverride, pk=ov_id, exam__college=college)
            ov.status = action
            ov.reviewed_by = request.user
            ov.review_note = note
            ov.save()
            if action == 'APPROVED':
                HallTicket.objects.filter(student=ov.student, exam=ov.exam).update(
                    status='ISSUED', issued_at=timezone.now()
                )
            messages.success(request, f'Exemption {action.lower()} for {ov.student.roll_number}.')
        return redirect('admin_hall_tickets')

    # Summary per exam
    exam_summaries = []
    for exam in exams:
        ht_qs = HallTicket.objects.filter(exam=exam)
        if dept_filter:
            ht_qs = ht_qs.filter(student__department_id=dept_filter)
        exam_summaries.append({
            'exam': exam,
            'total': ht_qs.count(),
            'issued': ht_qs.filter(status='ISSUED').count(),
            'detained': ht_qs.filter(status='DETAINED').count(),
            'withheld': ht_qs.filter(status='WITHHELD').count(),
        })

    # Pending exemption requests from HODs
    pending_overrides = EligibilityOverride.objects.filter(
        exam__college=college, status='PENDING'
    ).select_related('student__user', 'student__department', 'exam', 'requested_by').order_by('-created_at')

    return render(request, 'admin_panel/hall_tickets.html', {
        'exam_summaries': exam_summaries,
        'departments': departments,
        'dept_filter': dept_filter,
        'branding': _get_college_branding(college),
        'college': college,
        'pending_overrides': pending_overrides,
    })


@login_required
def hod_hall_tickets(request):
    """HOD view to manage hall tickets for their department's students."""
    try:
        hod = HOD.objects.select_related('department__college').get(user=request.user)
    except HOD.DoesNotExist:
        messages.error(request, 'HOD profile not found.')
        return redirect('dashboard')

    dept = hod.department
    college = dept.college
    exams = Exam.objects.filter(college=college).order_by('-start_date')

    exam_summaries = []
    for exam in exams:
        ht_qs = HallTicket.objects.filter(exam=exam, student__department=dept)
        exam_summaries.append({
            'exam': exam,
            'total': ht_qs.count(),
            'issued': ht_qs.filter(status='ISSUED').count(),
            'detained': ht_qs.filter(status='DETAINED').count(),
            'withheld': ht_qs.filter(status='WITHHELD').count(),
        })

    ctx = {
        'exam_summaries': exam_summaries,
        'departments': [],
        'dept_filter': None,
        'branding': _get_college_branding(college),
        'college': college,
        'hod_dept': dept,
    }
    if request.GET.get('partial') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'hod/hall_tickets_partial.html', ctx)
    return render(request, 'admin_panel/hall_tickets.html', ctx)


@login_required
def hod_exam_hall_tickets(request, exam_id):
    """
    HOD generates/views hall tickets for their department's students in a specific exam.
    Detained students can be granted exemptions — these go to college admin for approval.
    Once admin approves, HOD can regenerate to issue the hall ticket.
    """
    try:
        hod = HOD.objects.select_related('department__college').get(user=request.user)
    except HOD.DoesNotExist:
        messages.error(request, 'HOD profile not found.')
        return redirect('dashboard')

    dept = hod.department
    college = dept.college
    exam = get_object_or_404(Exam, pk=exam_id, college=college)

    students_qs = Student.objects.filter(
        department=dept,
        current_semester=exam.semester,
        status='ACTIVE',
    ).select_related('user').order_by('roll_number')

    existing_ht = {ht.student_id: ht for ht in HallTicket.objects.filter(exam=exam, student__department=dept)}
    existing_overrides = {ov.student_id: ov for ov in EligibilityOverride.objects.filter(exam=exam, student__department=dept)}

    att_agg = Attendance.objects.filter(
        student__in=students_qs,
        session__subject__semester=exam.semester,
    ).values('student_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    att_map = {row['student_id']: row for row in att_agg}

    fee_dues = set(
        Fee.objects.filter(student__in=students_qs, status__in=['PENDING', 'PARTIAL'])
        .values_list('student_id', flat=True)
    )

    exam_rule = _get_attendance_rule(college, dept, exam.semester)
    threshold = exam_rule.effective_min_overall

    rows = []
    for student in students_qs:
        att = att_map.get(student.id, {'total': 0, 'present': 0})
        pct = round(att['present'] / att['total'] * 100, 1) if att['total'] > 0 else 0
        has_dues = student.id in fee_dues
        att_fail = att['total'] >= exam_rule.min_sessions_for_check and pct < threshold
        override = existing_overrides.get(student.id)
        has_approved_override = override and override.status == 'APPROVED'
        if has_approved_override:
            auto_status = 'ELIGIBLE'
        elif att_fail:
            auto_status = 'DETAINED'
        elif has_dues:
            auto_status = 'WITHHELD'
        else:
            auto_status = 'ELIGIBLE'
        rows.append({
            'student': student, 'att_pct': pct, 'has_dues': has_dues,
            'hall_ticket': existing_ht.get(student.id),
            'threshold': threshold, 'auto_status': auto_status,
            'override': override,
        })

    def _row_counts(rows):
        return {
            'total': len(rows),
            'eligible': sum(1 for r in rows if r['auto_status'] == 'ELIGIBLE'),
            'detained': sum(1 for r in rows if r['auto_status'] == 'DETAINED'),
            'withheld': sum(1 for r in rows if r['auto_status'] == 'WITHHELD'),
        }

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'generate':
            # Generate hall tickets for this dept's students
            created = updated = 0
            classrooms = list(Classroom.objects.filter(college=college).order_by('room_number'))
            seat_map = {}
            seat_num = 1
            room_idx = 0
            eligible_rows = [r for r in rows if r['auto_status'] == 'ELIGIBLE']
            for r in eligible_rows:
                if room_idx >= len(classrooms):
                    break
                room = classrooms[room_idx]
                capacity = room.capacity or 30
                row_letter = chr(65 + ((seat_num - 1) // 10))
                seat_in_row = ((seat_num - 1) % 10) + 1
                seat_map[r['student'].id] = (room.room_number, f'{row_letter}{seat_in_row}', row_letter)
                seat_num += 1
                if seat_num > capacity:
                    room_idx += 1
                    seat_num = 1

            for r in rows:
                status = 'ISSUED' if r['auto_status'] == 'ELIGIBLE' else (
                    'DETAINED' if r['auto_status'] == 'DETAINED' else 'WITHHELD'
                )
                room_no, seat_no, row_no = seat_map.get(r['student'].id, ('', '', ''))
                ht, was_created = HallTicket.objects.update_or_create(
                    student=r['student'], exam=exam,
                    defaults={
                        'status': status, 'attendance_pct': r['att_pct'],
                        'has_fee_dues': r['has_dues'],
                        'issued_at': timezone.now() if status == 'ISSUED' else None,
                        'generated_by': request.user,
                        'room_number': room_no, 'seat_number': seat_no, 'row_number': row_no,
                    }
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            messages.success(request, f'Hall tickets generated: {created} new, {updated} updated.')
            # Re-fetch after generate
            existing_ht = {ht.student_id: ht for ht in HallTicket.objects.filter(exam=exam, student__department=dept)}
            existing_overrides = {ov.student_id: ov for ov in EligibilityOverride.objects.filter(exam=exam, student__department=dept)}
            for r in rows:
                r['hall_ticket'] = existing_ht.get(r['student'].id)
                r['override'] = existing_overrides.get(r['student'].id)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                ctx = {'hod': hod, 'dept': dept, 'exam': exam, 'rows': rows,
                       'threshold': threshold, 'counts': _row_counts(rows),
                       'branding': _get_college_branding(college)}
                return render(request, 'hod/exam_hall_tickets_partial.html', ctx)
            return redirect('hod_exam_hall_tickets', exam_id=exam.pk)

        elif action == 'request_exemption':
            # HOD submits exemption request for a detained student — goes to admin for approval
            student_id = request.POST.get('student_id')
            reason = request.POST.get('reason', '').strip()
            student_obj = get_object_or_404(Student, pk=student_id, department=dept)
            if not reason:
                messages.error(request, 'Please provide a reason for the exemption.')
            elif EligibilityOverride.objects.filter(student=student_obj, exam=exam).exists():
                messages.warning(request, f'Exemption already submitted for {student_obj.roll_number}.')
            else:
                att = att_map.get(student_obj.id, {'total': 0, 'present': 0})
                pct = round(att['present'] / att['total'] * 100, 1) if att['total'] > 0 else 0
                EligibilityOverride.objects.create(
                    student=student_obj, exam=exam,
                    requested_by=request.user,
                    reason=f'[HOD Exemption] {reason}',
                    attendance_pct_at_request=pct,
                    status='PENDING',
                )
                messages.success(request, f'Exemption request submitted for {student_obj.roll_number}. Awaiting college admin approval.')
            # Re-fetch overrides
            existing_overrides = {ov.student_id: ov for ov in EligibilityOverride.objects.filter(exam=exam, student__department=dept)}
            for r in rows:
                r['override'] = existing_overrides.get(r['student'].id)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                ctx = {'hod': hod, 'dept': dept, 'exam': exam, 'rows': rows,
                       'threshold': threshold, 'counts': _row_counts(rows),
                       'branding': _get_college_branding(college)}
                return render(request, 'hod/exam_hall_tickets_partial.html', ctx)
            return redirect('hod_exam_hall_tickets', exam_id=exam.pk)

    is_partial = request.GET.get('partial') or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    ctx = {
        'hod': hod, 'dept': dept, 'exam': exam, 'rows': rows,
        'threshold': threshold, 'counts': _row_counts(rows),
        'branding': _get_college_branding(college),
    }
    if is_partial:
        return render(request, 'hod/exam_hall_tickets_partial.html', ctx)
    return render(request, 'hod/exam_hall_tickets.html', ctx)



@login_required
def student_transcript_sem_pdf(request, semester):
    """Generate a single-semester transcript PDF for the student."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    try:
        student = Student.objects.select_related('department__college', 'user').get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')

    college = student.department.college
    branding = _get_college_branding(college)
    PRIMARY = colors.HexColor(branding.primary_color if branding else '#0d7377')
    DEEP = colors.HexColor('#071e26')
    MUTED = colors.HexColor('#64748b')
    LIGHT = colors.HexColor('#f0fdfa')
    BORDER = colors.HexColor('#cbd5e1')
    WHITE = colors.white

    result = Result.objects.filter(student=student, semester=semester).first()
    sem_marks = (
        Marks.objects.filter(student=student, subject__semester=semester)
        .select_related('subject', 'exam')
        .order_by('subject__name')
    )

    try:
        profile = student.user.studentprofile
    except Exception:
        profile = None

    LABEL = ParagraphStyle('lbl', fontName='Helvetica-Bold', fontSize=8, textColor=DEEP, leading=11)
    VALUE = ParagraphStyle('val', fontName='Helvetica', fontSize=8, textColor=DEEP, leading=11)
    HDR   = ParagraphStyle('hdr', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE, leading=11)
    CELL  = ParagraphStyle('cel', fontName='Helvetica', fontSize=8, textColor=DEEP, leading=11)

    buf = BytesIO()
    PAGE_W = 180 * mm
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=12*mm, bottomMargin=14*mm)
    story = []

    # Header
    hdr_tbl = Table([[
        Paragraph(f'<b>{college.name}</b>', ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=14, textColor=WHITE, leading=18)),
        Paragraph(f'<b>SEMESTER {semester} TRANSCRIPT</b>', ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=11, textColor=WHITE, leading=14, alignment=TA_RIGHT)),
    ]], colWidths=[PAGE_W * 0.62, PAGE_W * 0.38])
    hdr_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), PRIMARY),
        ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0),(-1,-1), 12), ('BOTTOMPADDING', (0,0),(-1,-1), 12),
        ('LEFTPADDING', (0,0),(0,-1), 14), ('RIGHTPADDING', (1,0),(1,-1), 14),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 5*mm))

    # Student info
    dob_str = profile.date_of_birth.strftime('%d %b %Y') if profile and profile.date_of_birth else '—'
    info_rows = [
        [Paragraph('Student Name', LABEL), Paragraph(student.user.get_full_name() or student.user.username, VALUE),
         Paragraph('Roll Number', LABEL), Paragraph(student.roll_number, VALUE)],
        [Paragraph('Department', LABEL), Paragraph(student.department.name, VALUE),
         Paragraph('Semester', LABEL), Paragraph(str(semester), VALUE)],
        [Paragraph('Date of Birth', LABEL), Paragraph(dob_str, VALUE),
         Paragraph('Admission Year', LABEL), Paragraph(str(student.admission_year), VALUE)],
    ]
    info_tbl = Table(info_rows, colWidths=[32*mm, 58*mm, 34*mm, 56*mm])
    info_tbl.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0),(-1,-1), [WHITE, LIGHT]),
        ('GRID', (0,0),(-1,-1), 0.3, BORDER),
        ('TOPPADDING', (0,0),(-1,-1), 5), ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING', (0,0),(-1,-1), 7), ('RIGHTPADDING', (0,0),(-1,-1), 7),
        ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width='100%', thickness=1, color=PRIMARY, spaceAfter=4*mm))

    # Result summary
    if result:
        summary_data = [[
            Paragraph('<b>SGPA</b>', HDR), Paragraph('<b>Percentage</b>', HDR),
            Paragraph('<b>Total Marks</b>', HDR), Paragraph('<b>Result</b>', HDR),
        ], [
            Paragraph(f'{result.gpa}', ParagraphStyle('v', fontName='Helvetica-Bold', fontSize=12, textColor=PRIMARY, leading=14)),
            Paragraph(f'{result.percentage:.1f}%', ParagraphStyle('v', fontName='Helvetica-Bold', fontSize=12, textColor=DEEP, leading=14)),
            Paragraph(f'{result.total_marks:.0f}', ParagraphStyle('v', fontName='Helvetica-Bold', fontSize=12, textColor=DEEP, leading=14)),
            Paragraph('PASS' if result.percentage >= 40 else 'FAIL',
                      ParagraphStyle('v', fontName='Helvetica-Bold', fontSize=12,
                                     textColor=colors.HexColor('#059669') if result.percentage >= 40 else colors.HexColor('#dc2626'), leading=14)),
        ]]
        sum_tbl = Table(summary_data, colWidths=[PAGE_W/4]*4)
        sum_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(-1,0), PRIMARY),
            ('BACKGROUND', (0,1),(-1,1), LIGHT),
            ('GRID', (0,0),(-1,-1), 0.3, BORDER),
            ('ALIGN', (0,0),(-1,-1), 'CENTER'),
            ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0),(-1,-1), 8), ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ]))
        story.append(sum_tbl)
        story.append(Spacer(1, 5*mm))

    # Marks table
    if sem_marks:
        story.append(Paragraph(f'<b>Subject-wise Marks — Semester {semester}</b>',
                                ParagraphStyle('sh', fontName='Helvetica-Bold', fontSize=10, textColor=DEEP, spaceAfter=6)))
        COL_W = [65*mm, 20*mm, 18*mm, 18*mm, 15*mm, 14*mm, 14*mm, 16*mm]
        hdr_row = [Paragraph(h, HDR) for h in ['Subject', 'Code', 'Credits', 'Marks', 'Max', '%', 'Grade', 'GP']]
        data = [hdr_row]
        for m in sem_marks:
            pct = round(m.marks_obtained / m.max_marks * 100, 1) if m.max_marks > 0 else 0
            data.append([
                Paragraph(m.subject.name, CELL),
                Paragraph(m.subject.code, CELL),
                Paragraph(str(m.subject.credits or '—'), CELL),
                Paragraph(f'{m.marks_obtained:.0f}', CELL),
                Paragraph(f'{m.max_marks:.0f}', CELL),
                Paragraph(f'{pct}%', CELL),
                Paragraph(m.grade or '—', CELL),
                Paragraph(f'{m.grade_point:.1f}' if m.grade_point else '—', CELL),
            ])
        marks_tbl = Table(data, colWidths=COL_W)
        marks_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(-1,0), PRIMARY),
            ('ROWBACKGROUNDS', (0,1),(-1,-1), [WHITE, LIGHT]),
            ('GRID', (0,0),(-1,-1), 0.3, BORDER),
            ('TOPPADDING', (0,0),(-1,-1), 5), ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('LEFTPADDING', (0,0),(-1,-1), 6), ('RIGHTPADDING', (0,0),(-1,-1), 6),
            ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
        ]))
        story.append(marks_tbl)
    else:
        story.append(Paragraph('No marks recorded for this semester.', VALUE))

    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceAfter=4*mm))
    story.append(Paragraph(f'Generated on {timezone.now().strftime("%d %b %Y")} &mdash; {college.name}',
                            ParagraphStyle('ft', fontName='Helvetica', fontSize=7, textColor=MUTED, alignment=TA_CENTER)))

    doc.build(story)
    buf.seek(0)
    response = HttpResponse(buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="transcript-sem{semester}-{student.roll_number}.pdf"'
    return response


@login_required
def student_library(request):
    """Student library portal — stub view, ready for full library module integration."""
    try:
        student = Student.objects.select_related('department__college', 'user').get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('home')

    tab = request.GET.get('tab', 'borrow')
    college = student.department.college
    branding = _get_college_branding(college)

    return render(request, 'student/library.html', {
        'student': student,
        'tab': tab,
        'branding': branding,
        'college': college,
    })


@login_required
def admin_leave_quotas(request):
    """Admin sets leave and substitution quotas for faculty."""
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    cfg, _ = CollegeFeatureConfig.objects.get_or_create(college=college)

    if request.method == 'POST':
        cfg.max_casual_leaves  = _safe_int(request.POST.get('max_casual_leaves'),  12)
        cfg.max_medical_leaves = _safe_int(request.POST.get('max_medical_leaves'), 10)
        cfg.max_earned_leaves  = _safe_int(request.POST.get('max_earned_leaves'),  15)
        cfg.max_od_leaves      = _safe_int(request.POST.get('max_od_leaves'),      20)
        cfg.max_substitutions  = _safe_int(request.POST.get('max_substitutions'),  10)
        cfg.save(update_fields=['max_casual_leaves','max_medical_leaves','max_earned_leaves','max_od_leaves','max_substitutions'])
        # store who last updated
        request.session['leave_quota_updated_by'] = request.user.get_full_name() or request.user.username
        messages.success(request, 'Leave and substitution quotas updated.')
        return redirect('admin_leave_quotas')

    last_updated_by = request.session.get('leave_quota_updated_by') or (request.user.get_full_name() or request.user.username)

    return render(request, 'admin_panel/leave_quotas.html', {
        'cfg': cfg, 'college': college,
        'branding': _get_college_branding(college),
        'last_updated_by': last_updated_by,
        'leave_fields': [
            ('max_casual_leaves',  'Casual Leave (CL)',  cfg.max_casual_leaves),
            ('max_medical_leaves', 'Medical Leave (ML)', cfg.max_medical_leaves),
            ('max_earned_leaves',  'Earned Leave (EL)',  cfg.max_earned_leaves),
            ('max_od_leaves',      'On Duty (OD)',       cfg.max_od_leaves),
        ],
    })


@login_required
def admin_college_settings(request):
    """
    Consolidated college configuration page.
    Covers: feature toggles, evaluation scheme (CGPA), hall ticket rules summary,
    leave/substitution quotas, and attendance rule overview.
    """
    if not _admin_guard(request):
        return redirect('dashboard')
    college = _get_admin_college(request)
    cfg, _ = CollegeFeatureConfig.objects.get_or_create(college=college)
    departments = _scope_departments(request).order_by('name')

    # Evaluation scheme — college-wide default
    scheme = EvaluationScheme.objects.filter(college=college, department__isnull=True, is_active=True).first()

    # Attendance rules summary
    att_rules = AttendanceRule.objects.filter(college=college).select_related('department').order_by('department__name', 'semester')

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Feature toggles ──────────────────────────────────────────────────
        if action == 'features':
            bool_fields = [
                'enable_electives', 'enable_online_payment', 'enable_quiz_module',
                'enable_assignment_module', 'enable_lesson_plans', 'enable_helpdesk',
                'enable_supply_exam', 'enable_revaluation', 'enable_grace_marks',
                'enable_fee_installments', 'require_hod_for_attendance_correction',
                'require_principal_for_result_publish', 'auto_promote_students',
            ]
            for field in bool_fields:
                setattr(cfg, field, request.POST.get(field) == 'on')
            cfg.save()
            messages.success(request, 'Feature settings updated.')

        # ── Leave & substitution quotas ───────────────────────────────────────
        elif action == 'quotas':
            cfg.max_casual_leaves  = _safe_int(request.POST.get('max_casual_leaves'),  12)
            cfg.max_medical_leaves = _safe_int(request.POST.get('max_medical_leaves'), 10)
            cfg.max_earned_leaves  = _safe_int(request.POST.get('max_earned_leaves'),  15)
            cfg.max_od_leaves      = _safe_int(request.POST.get('max_od_leaves'),      20)
            cfg.max_substitutions  = _safe_int(request.POST.get('max_substitutions'),  10)
            cfg.save(update_fields=[
                'max_casual_leaves', 'max_medical_leaves', 'max_earned_leaves',
                'max_od_leaves', 'max_substitutions'
            ])
            messages.success(request, 'Leave and substitution quotas updated.')

        # ── Evaluation scheme (CGPA) ──────────────────────────────────────────
        elif action == 'scheme':
            name         = request.POST.get('scheme_name', 'Default Scheme').strip()
            grading_type = request.POST.get('grading_type', 'CREDIT')
            cie_count    = _safe_int(request.POST.get('cie_count'), 2)
            cie_best_of  = _safe_int(request.POST.get('cie_best_of'), 2)
            cie_max      = _safe_int(request.POST.get('cie_max_per_test'), 25)
            cie_total    = _safe_int(request.POST.get('cie_total_max'), 50)
            see_max      = _safe_int(request.POST.get('see_max'), 100)
            see_scaled   = _safe_int(request.POST.get('see_scaled_to'), 50)
            see_pass     = _safe_int(request.POST.get('see_passing_min'), 20)
            overall_pass = _safe_int(request.POST.get('overall_passing_min'), 40)

            if scheme:
                scheme.name = name
                scheme.grading_type = grading_type
                scheme.cie_count = cie_count
                scheme.cie_best_of = cie_best_of
                scheme.cie_max_per_test = cie_max
                scheme.cie_total_max = cie_total
                scheme.see_max = see_max
                scheme.see_scaled_to = see_scaled
                scheme.see_passing_min = see_pass
                scheme.overall_passing_min = overall_pass
                scheme.save()
            else:
                scheme = EvaluationScheme.objects.create(
                    college=college, department=None, name=name,
                    grading_type=grading_type, cie_count=cie_count,
                    cie_best_of=cie_best_of, cie_max_per_test=cie_max,
                    cie_total_max=cie_total, see_max=see_max,
                    see_scaled_to=see_scaled, see_passing_min=see_pass,
                    overall_passing_min=overall_pass, is_active=True,
                )
            messages.success(request, 'Evaluation scheme updated.')

        return redirect('admin_college_settings')

    ctx = {
        'cfg': cfg, 'college': college, 'scheme': scheme,
        'att_rules': att_rules, 'departments': departments,
        'branding': _get_college_branding(college),
        'grading_choices': EvaluationScheme.GRADING_CHOICES,
        'leave_fields': [
            ('max_casual_leaves',  'Casual Leave (CL)',  cfg.max_casual_leaves),
            ('max_medical_leaves', 'Medical Leave (ML)', cfg.max_medical_leaves),
            ('max_earned_leaves',  'Earned Leave (EL)',  cfg.max_earned_leaves),
            ('max_od_leaves',      'On Duty (OD)',       cfg.max_od_leaves),
        ],
        'feature_toggles': [
            ('enable_electives',                    'Elective Courses',             'Allow students to register for elective subjects',                  cfg.enable_electives),
            ('enable_online_payment',               'Online Fee Payment',           'Enable Razorpay payment gateway for fees',                          cfg.enable_online_payment),
            ('enable_quiz_module',                  'Quiz Module',                  'Faculty can create and assign quizzes',                             cfg.enable_quiz_module),
            ('enable_assignment_module',            'Assignment Module',            'Faculty can create assignments; students submit online',             cfg.enable_assignment_module),
            ('enable_lesson_plans',                 'Lesson Plans',                 'Faculty can upload lesson plans per subject',                        cfg.enable_lesson_plans),
            ('enable_helpdesk',                     'Help Desk',                    'Students and staff can raise support tickets',                       cfg.enable_helpdesk),
            ('enable_supply_exam',                  'Supplementary Exams',          'Students can register for supply exams for failed subjects',         cfg.enable_supply_exam),
            ('enable_revaluation',                  'Revaluation Requests',         'Students can request revaluation of answer scripts',                 cfg.enable_revaluation),
            ('enable_grace_marks',                  'Grace Marks',                  'Exam dept can apply grace marks to borderline students',             cfg.enable_grace_marks),
            ('enable_fee_installments',             'Fee Installments',             'Allow partial fee payments in installments',                         cfg.enable_fee_installments),
            ('require_hod_for_attendance_correction','HOD Approval for Attendance Correction', 'Attendance corrections need HOD sign-off',               cfg.require_hod_for_attendance_correction),
            ('require_principal_for_result_publish','Principal Approval for Results','Results need principal approval before publishing',                 cfg.require_principal_for_result_publish),
            ('auto_promote_students',               'Auto-Promote Students',        'Automatically move students to next semester at year end',           cfg.auto_promote_students),
        ],
    }
    return render(request, 'admin_panel/college_settings.html', ctx)
