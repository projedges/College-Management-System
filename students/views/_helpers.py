"""
Shared helpers, utilities, and decorators used across all view modules.
"""
import csv
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
)


# ── Decorators ────────────────────────────────────────────────────────────────

def super_admin_required(view_func):
    """Restricts view to Django superusers only."""
    actual_decorator = user_passes_test(lambda u: u.is_superuser, login_url='super_admin_login')
    return actual_decorator(view_func)

def _admin_guard(request):
    """Returns True if the request user is a college admin (role=1) or superuser."""
    if request.user.is_superuser:
        return True
    role = _get_user_role(request.user)
    return role and role.role == 1


# ── Type coercion ─────────────────────────────────────────────────────────────

def _safe_int(val, default=0):
    try: return int(val)
    except (ValueError, TypeError): return default

def _safe_float(val, default=0.0):
    try: return float(val)
    except (ValueError, TypeError): return default


# ── Branding ──────────────────────────────────────────────────────────────────

def _get_college_branding(college):
    if not college:
        return None
    branding, _ = CollegeBranding.objects.get_or_create(college=college)
    return branding


# ── Network ───────────────────────────────────────────────────────────────────

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


# ── Security ──────────────────────────────────────────────────────────────────

def _get_or_create_security(user):
    security, _ = UserSecurity.objects.get_or_create(user=user)
    return security


# ── Timetable conflict check ──────────────────────────────────────────────────

def _check_timetable_conflict(day, start, end, faculty=None, classroom=None, ignore_id=None):
    qs = Timetable.objects.filter(day_of_week=day)
    if ignore_id:
        qs = qs.exclude(id=ignore_id)
    overlap_qs = qs.filter(Q(start_time__lt=end, end_time__gt=start))
    if faculty and overlap_qs.filter(faculty=faculty).exists():
        return True, f"Conflict: {faculty.user.get_full_name()} is already teaching during this time."
    if classroom and overlap_qs.filter(classroom=classroom).exists():
        return True, f"Conflict: Room {classroom.room_number} is occupied during this time."
    return False, ""


# ── Attendance permission ─────────────────────────────────────────────────────

def _check_attendance_permission(user, subject, slot=None):
    from django.conf import settings
    role = getattr(user, 'userrole', None)
    if not role: return False, "No role assigned."
    if user.is_superuser: return True, ""

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
                timetable_slot=slot, substitute_faculty=user.faculty, date=now.date()
            ).exists()
        if not (is_assigned or is_sub):
            return False, "You are not assigned to this subject."
        # Time lock bypass only via explicit env var (never via DEBUG flag)
        import os
        if os.environ.get('ATTENDANCE_TIME_LOCK_DISABLED') == '1':
            return True, ""
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


# ── Fee helpers ───────────────────────────────────────────────────────────────

def _sync_fee_status(fee):
    if fee.paid_amount >= fee.total_amount:
        fee.status = "PAID"
    elif fee.paid_amount > 0:
        fee.status = "PARTIAL"
    else:
        fee.status = "PENDING"
    return fee

def _create_default_fee(student):
    structure = FeeStructure.objects.filter(
        department=student.department,
        semester=student.current_semester
    ).first()
    # Use FeeStructure if configured, otherwise 0 (admin must set it manually)
    total = structure.total_fees if structure else 0.0
    Fee.objects.get_or_create(
        student=student,
        semester=student.current_semester,
        defaults={
            'total_amount': total,
            'paid_amount': 0.0,
            'status': 'PENDING',
        }
    )


# ── Assignment helpers ────────────────────────────────────────────────────────

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


# ── PDF generation ────────────────────────────────────────────────────────────

def _pdf_escape(value):
    return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

def _simple_pdf_bytes(title, lines, college_name=None):
    visible_lines = list(lines[:32])
    if len(lines) > 32:
        visible_lines.append(f"... and {len(lines) - 32} more lines")
    y = 790
    commands = ["BT", "/F1 18 Tf", "50 790 Td", f"({_pdf_escape(title)}) Tj", "ET"]
    if college_name:
        commands.extend(["BT", "/F1 10 Tf", "50 775 Td", f"({_pdf_escape(college_name)}) Tj", "ET"])
        y -= 15
    y -= 28
    for line in visible_lines:
        commands.extend(["BT", "/F1 11 Tf", f"50 {y} Td", f"({_pdf_escape(line[:115])}) Tj", "ET"])
        y -= 16
    stream = "\n".join(commands).encode("latin-1", "replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1") + stream + b"\nendstream endobj\n",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("latin-1"))
    return bytes(pdf)

def _pdf_response(filename, title, lines, generated_by=None, report_type=None, college=None):
    college_name = college.name if college else "EduTrack System"
    payload = _simple_pdf_bytes(title, lines, college_name=college_name)
    if generated_by and report_type in {"ATTENDANCE", "RESULT", "PAYMENT"}:
        report = SystemReport(report_type=report_type, generated_by=generated_by)
        report.file.save(filename, ContentFile(payload), save=True)
    response = HttpResponse(payload, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ── College / role scoping ────────────────────────────────────────────────────

def _default_college():
    return College.objects.order_by("id").first()

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

def _scope_helpdesk_tickets(request):
    college = _get_admin_college(request)
    qs = HelpDeskTicket.objects.select_related('college', 'submitted_by').order_by('-created_at')
    if request.user.is_superuser or college is None:
        return qs
    return qs.filter(Q(college=college) | Q(college__isnull=True))


# ── Registration helpers ──────────────────────────────────────────────────────

def _get_registration_invite(token):
    if not token:
        return None
    invite = RegistrationInvite.objects.select_related('college', 'department').filter(token=token).first()
    if invite and invite.is_usable:
        return invite
    return None

def _build_registration_invite_url(request, invite):
    return request.build_absolute_uri(f"{reverse('register')}?token={invite.token}")


# ── ID generation ─────────────────────────────────────────────────────────────

def _generate_roll_number(department, admission_year):
    college = department.college
    rule = getattr(college, 'student_id_rule', '{YEAR}-{CODE}-{DEPT}-{SERIAL}')
    prefix_template = rule.split('{SERIAL}')[0]
    prefix = prefix_template.format(
        YEAR=str(admission_year), CODE=college.code.upper(), DEPT=department.code.upper()
    )
    latest_roll = (
        Student.objects.filter(roll_number__startswith=prefix)
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
            next_serial = Student.objects.filter(roll_number__startswith=prefix).count() + 1
    return rule.format(
        YEAR=str(admission_year), CODE=college.code.upper(),
        DEPT=department.code.upper(), SERIAL=f"{next_serial:03d}"
    )

def _generate_faculty_id(department):
    college = department.college
    rule = getattr(college, 'faculty_id_rule', 'FAC-{CODE}-{SERIAL}')
    count = Faculty.objects.filter(department__college=college).count() + 1
    return rule.format(CODE=college.code.upper(), DEPT=department.code.upper(), SERIAL=f"{count:03d}")


# ── Result breakdown ──────────────────────────────────────────────────────────

def _student_result_breakdown(student):
    results = Result.objects.filter(student=student).order_by('-semester')
    marks = (
        Marks.objects.filter(student=student)
        .select_related('subject', 'exam')
        .order_by('-exam__semester', 'subject__name')
    )
    marks_by_semester = {}
    for mark in marks:
        semester = mark.exam.semester if mark.exam_id else mark.subject.semester
        marks_by_semester.setdefault(semester, []).append(mark)
    breakdown = []
    for result in results:
        breakdown.append({'result': result, 'marks': marks_by_semester.get(result.semester, [])})
    uncovered = sorted(
        set(marks_by_semester.keys()) - {item['result'].semester for item in breakdown}, reverse=True
    )
    for semester in uncovered:
        breakdown.append({'result': None, 'semester': semester, 'marks': marks_by_semester[semester]})
    return breakdown, results


# ── Timetable auto-generation ─────────────────────────────────────────────────

def _auto_generate_timetable(department, semester):
    """
    Generate timetable from SectionSubjectFacultyMap (preferred) or FacultySubject (fallback).
    50-min periods, lab = 2x50 min. Conflict-free college-wide.
    """
    from datetime import time as dt_time

    def add_min(t, m):
        total = t.hour * 60 + t.minute + m
        return dt_time(total // 60, total % 60)

    LECTURE_GRID = []
    for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
        for h in [9, 10, 11, 12]:
            s = dt_time(h, 0)
            LECTURE_GRID.append((day, s, add_min(s, 50)))
        for h in [14, 15]:
            s = dt_time(h, 0)
            LECTURE_GRID.append((day, s, add_min(s, 50)))

    # Lab = 2 consecutive 50-min slots on the same day (14:00–14:50 then 14:50–15:40)
    # Stored as two separate Timetable rows, not one merged block
    LAB_PAIRS = []
    for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
        s1 = dt_time(14, 0);  e1 = add_min(s1, 50)   # 14:00–14:50
        s2 = dt_time(14, 50); e2 = add_min(s2, 50)   # 14:50–15:40
        LAB_PAIRS.append((day, s1, e1, s2, e2))

    subjects = list(Subject.objects.filter(department=department, semester=semester).order_by('name'))
    if not subjects:
        return 0

    from students.models import SectionSubjectFacultyMap
    ssf_maps = list(
        SectionSubjectFacultyMap.objects.filter(
            section__department=department, section__semester=semester
        ).select_related('subject', 'faculty', 'section', 'classroom')
    )

    assignments = []
    if ssf_maps:
        for m in ssf_maps:
            assignments.append((m.subject, m.faculty, m.section.label, m.classroom))
    else:
        fa_qs = (FacultySubject.objects
                 .filter(subject__in=subjects)
                 .select_related('faculty__user', 'subject')
                 .order_by('subject__name', 'faculty__user__first_name'))
        subj_count = {}
        for fa in fa_qs:
            idx = subj_count.get(fa.subject_id, 0)
            subj_count[fa.subject_id] = idx + 1
            label = chr(65 + idx) if subj_count[fa.subject_id] > 1 else ''
            assignments.append((fa.subject, fa.faculty, label, None))

    if not assignments:
        return 0

    classrooms = list(Classroom.objects.filter(college=department.college).order_by('room_number'))
    if not classrooms:
        classrooms = [Classroom.objects.create(
            college=department.college, room_number=f"{department.code}-101", capacity=60
        )]

    used_faculty: set = set()
    used_rooms: set = set()
    existing = Timetable.objects.filter(
        subject__department__college=department.college
    ).exclude(
        subject__department=department, subject__semester=semester
    ).values_list('faculty_id', 'classroom_id', 'day_of_week', 'start_time')
    for fac_id, room_id, day, start in existing:
        used_faculty.add((fac_id, day, start))
        used_rooms.add((room_id, day, start))

    Timetable.objects.filter(subject__department=department, subject__semester=semester).delete()

    created_count = 0
    for idx, (subj, faculty, section, preferred_room) in enumerate(assignments):
        is_lab = '_LAB' in subj.code or subj.practical_hours >= 4

        if is_lab:
            # Lab: find a day where BOTH consecutive slots are free for faculty + room
            for day, s1, e1, s2, e2 in LAB_PAIRS:
                fkey1 = (faculty.id, day, s1)
                fkey2 = (faculty.id, day, s2)
                if fkey1 in used_faculty or fkey2 in used_faculty:
                    continue
                room = None
                for r in ([preferred_room] if preferred_room else []) + classrooms:
                    if not r:
                        continue
                    if (r.id, day, s1) not in used_rooms and (r.id, day, s2) not in used_rooms:
                        room = r
                        break
                if not room:
                    continue
                # Create two separate 50-min rows
                for s, e in [(s1, e1), (s2, e2)]:
                    Timetable.objects.create(
                        subject=subj, faculty=faculty,
                        day_of_week=day, start_time=s, end_time=e,
                        classroom=room, section=section,
                    )
                    used_faculty.add((faculty.id, day, s))
                    used_rooms.add((room.id, day, s))
                    created_count += 1
                break  # lab scheduled, move to next subject
        else:
            slots_needed = max(subj.lecture_hours, 1)
            placed = 0
            for day, start, end in LECTURE_GRID:
                if placed >= slots_needed:
                    break
                fkey = (faculty.id, day, start)
                if fkey in used_faculty:
                    continue
                room = None
                for r in ([preferred_room] if preferred_room else []) + classrooms:
                    if r and (r.id, day, start) not in used_rooms:
                        room = r
                        break
                if not room:
                    continue
                Timetable.objects.create(
                    subject=subj, faculty=faculty,
                    day_of_week=day, start_time=start, end_time=end,
                    classroom=room, section=section,
                )
                used_faculty.add(fkey)
                used_rooms.add((room.id, day, start))
                placed += 1
                created_count += 1
    return created_count

