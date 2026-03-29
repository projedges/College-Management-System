import csv
from datetime import datetime, timedelta, time as dt_time
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Q, Count
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from .models import (
    UserRole, College, Student, Faculty, Department, HOD, Principal,
    Fee, Announcement, ActivityLog, Attendance, AttendanceSession,
    Subject, FacultySubject, Timetable, Result, Marks, Exam,
    Assignment, AssignmentSubmission, HODApproval, FacultyPerformance,
    Payment, SystemReport, StudentProfile, Address, Parent,
    EmergencyContact, UserSecurity, RegistrationRequest,
    RegistrationInvite, HelpDeskTicket, FacultyAvailability, Classroom
)


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _get_or_create_security(user):
    security, _ = UserSecurity.objects.get_or_create(user=user)
    return security


def _sync_fee_status(fee):
    if fee.paid_amount >= fee.total_amount:
        fee.status = "PAID"
    elif fee.paid_amount > 0:
        fee.status = "PARTIAL"
    else:
        fee.status = "PENDING"
    return fee


def _assignment_deadline_from_input(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _pdf_escape(value):
    return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _simple_pdf_bytes(title, lines):
    visible_lines = list(lines[:32])
    if len(lines) > 32:
        visible_lines.append(f"... and {len(lines) - 32} more lines")

    y = 790
    commands = [
        "BT",
        "/F1 18 Tf",
        "50 790 Td",
        f"({_pdf_escape(title)}) Tj",
        "ET",
    ]
    y -= 28
    for line in visible_lines:
        commands.extend([
            "BT",
            "/F1 11 Tf",
            f"50 {y} Td",
            f"({_pdf_escape(line[:115])}) Tj",
            "ET",
        ])
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
    pdf.extend(
        f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("latin-1")
    )
    return bytes(pdf)


def _pdf_response(filename, title, lines, generated_by=None, report_type=None):
    payload = _simple_pdf_bytes(title, lines)
    if generated_by and report_type in {"ATTENDANCE", "RESULT", "PAYMENT"}:
        report = SystemReport(report_type=report_type, generated_by=generated_by)
        report.file.save(filename, ContentFile(payload), save=True)
    response = HttpResponse(payload, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
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


def _generate_roll_number(department, admission_year):
    year = str(admission_year)
    college_code = (department.college.code if department.college else "COL").upper()
    prefix = f"{year}-{college_code}-{department.code.upper()}-"
    latest_roll = (
        Student.objects.filter(roll_number__startswith=prefix)
        .order_by('-roll_number')
        .values_list('roll_number', flat=True)
        .first()
    )
    next_serial = 1
    if latest_roll:
        try:
            next_serial = int(latest_roll.split('-')[-1]) + 1
        except (TypeError, ValueError):
            next_serial = Student.objects.filter(roll_number__startswith=prefix).count() + 1
    return f"{prefix}{next_serial:03d}"


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
        breakdown.append({
            'result': result,
            'marks': marks_by_semester.get(result.semester, []),
        })
    uncovered_semesters = sorted(set(marks_by_semester.keys()) - {item['result'].semester for item in breakdown}, reverse=True)
    for semester in uncovered_semesters:
        breakdown.append({
            'result': None,
            'semester': semester,
            'marks': marks_by_semester[semester],
        })
    return breakdown, results


def _scope_helpdesk_tickets(request):
    college = _get_admin_college(request)
    qs = HelpDeskTicket.objects.select_related('college', 'submitted_by').order_by('-created_at')
    if request.user.is_superuser or college is None:
        return qs
    return qs.filter(Q(college=college) | Q(college__isnull=True))


def _auto_generate_timetable(department, semester):
    subjects = list(Subject.objects.filter(department=department, semester=semester).order_by('name'))
    faculty_assignments = list(
        FacultySubject.objects.filter(subject__in=subjects)
        .select_related('faculty__user', 'subject')
        .order_by('subject__name', 'faculty__user__first_name')
    )
    if not subjects or not faculty_assignments:
        return 0

    classrooms = list(Classroom.objects.order_by('room_number'))
    if not classrooms:
        classrooms.append(Classroom.objects.create(room_number=f"{department.code}-101", capacity=60))

    availability_map = {}
    for slot in FacultyAvailability.objects.filter(
        faculty__in=[assignment.faculty for assignment in faculty_assignments],
        is_available=True,
    ).order_by('day_of_week', 'start_time'):
        availability_map.setdefault(slot.faculty_id, []).append(slot)

    default_slots = [
        ('MON', dt_time(9, 0), dt_time(10, 0)),
        ('MON', dt_time(10, 0), dt_time(11, 0)),
        ('TUE', dt_time(9, 0), dt_time(10, 0)),
        ('TUE', dt_time(10, 0), dt_time(11, 0)),
        ('WED', dt_time(9, 0), dt_time(10, 0)),
        ('THU', dt_time(9, 0), dt_time(10, 0)),
        ('FRI', dt_time(9, 0), dt_time(10, 0)),
        ('SAT', dt_time(9, 0), dt_time(10, 0)),
    ]

    Timetable.objects.filter(subject__department=department, subject__semester=semester).delete()
    used_faculty_slots = set()
    used_room_slots = set()
    created_count = 0

    for index, assignment in enumerate(faculty_assignments):
        candidate_slots = availability_map.get(assignment.faculty_id) or default_slots
        slot_created = False
        for slot_index, slot in enumerate(candidate_slots):
            if hasattr(slot, 'day_of_week'):
                day_of_week, start_time, end_time = slot.day_of_week, slot.start_time, slot.end_time
            else:
                day_of_week, start_time, end_time = slot
            faculty_key = (assignment.faculty_id, day_of_week, start_time)
            classroom = classrooms[(index + slot_index) % len(classrooms)]
            room_key = (classroom.id, day_of_week, start_time)
            if faculty_key in used_faculty_slots or room_key in used_room_slots:
                continue
            Timetable.objects.create(
                subject=assignment.subject,
                faculty=assignment.faculty,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                classroom=classroom,
            )
            used_faculty_slots.add(faculty_key)
            used_room_slots.add(room_key)
            created_count += 1
            slot_created = True
            break
        if not slot_created:
            continue
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


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        existing_user = User.objects.filter(username=username).first()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            security = _get_or_create_security(user)
            security.login_attempts = 0
            security.last_login_ip = get_client_ip(request)
            security.save(update_fields=["login_attempts", "last_login_ip"])
            ActivityLog.objects.create(user=user, action="User logged in", ip_address=get_client_ip(request))
            next_url = request.GET.get("next", "dashboard")
            return redirect(next_url)
        else:
            if existing_user is not None:
                security = _get_or_create_security(existing_user)
                security.login_attempts += 1
                security.last_login_ip = get_client_ip(request)
                security.save(update_fields=["login_attempts", "last_login_ip"])
            messages.error(request, "Invalid username or password.")
    return render(request, "auth/login.html")


def logout_view(request):
    if request.user.is_authenticated:
        ActivityLog.objects.create(user=request.user, action="User logged out", ip_address=get_client_ip(request))
    logout(request)
    return redirect("home")


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
        if not first_name or not last_name or not email:
            messages.error(request, "First name, last name, and email are required.")
        elif email.lower() != invite.invited_email.lower():
            messages.error(request, "This one-time access link is tied to a different email address.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists. Please sign in.")
        elif RegistrationRequest.objects.filter(email=email, status__in=['PENDING', 'REVIEWED']).exists():
            messages.warning(request, "A registration request for this email is already pending.")
        else:
            department = None
            if desired_department:
                department = departments.filter(pk=desired_department).first()
            RegistrationRequest.objects.create(
                college=invite.college,
                desired_department=department or invite.department,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                admission_year=int(admission_year) if admission_year else invite.admission_year,
                current_semester=int(current_semester) if current_semester else invite.current_semester,
                message=message,
            )
            invite.used_at = timezone.now()
            invite.save(update_fields=["used_at"])
            messages.success(request, "Request submitted. The college admin will review and create your student account.")
            return redirect("login")
    return render(request, "auth/register.html", {
        'departments': departments,
        'invite': invite,
        'invite_required': invite is None,
    })


def helpdesk_view(request):
    colleges = College.objects.order_by('name')
    initial_college = _get_user_college(request.user) if request.user.is_authenticated else _default_college()
    if request.method == "POST":
        college_id = request.POST.get("college")
        college = College.objects.filter(pk=college_id).first() if college_id else initial_college
        name = request.POST.get("name", "").strip() or (request.user.get_full_name().strip() if request.user.is_authenticated else "")
        email = request.POST.get("email", "").strip() or (request.user.email.strip() if request.user.is_authenticated else "")
        issue_type = request.POST.get("issue_type", "GENERAL")
        subject = request.POST.get("subject", "").strip()
        description = request.POST.get("description", "").strip()

        if not name or not email or not subject or not description:
            messages.error(request, "Name, email, subject, and description are required.")
        else:
            HelpDeskTicket.objects.create(
                college=college,
                submitted_by=request.user if request.user.is_authenticated else None,
                name=name,
                email=email,
                issue_type=issue_type,
                subject=subject,
                description=description,
            )
            messages.success(request, "Support request submitted. The college team can review it from the help desk.")
            return redirect("helpdesk")

    return render(request, "helpdesk.html", {
        "colleges": colleges,
        "initial_college": initial_college,
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
    role_map = {1: "admin_dashboard", 2: "hod_dashboard", 3: "faculty_dashboard", 4: "student_dashboard", 5: "student_dashboard", 6: "principal_dashboard"}
    return redirect(role_map.get(role, "student_dashboard"))


@login_required
def super_admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    colleges = College.objects.annotate(
        department_count=Count('departments', distinct=True),
        admin_count=Count('user_roles', filter=Q(user_roles__role=1), distinct=True),
        student_count=Count('departments__student', distinct=True),
    ).order_by('name')
    college_admins = UserRole.objects.filter(role=1).select_related('user', 'college').order_by('college__name', 'user__username')
    recent_activity = ActivityLog.objects.select_related('user').order_by('-timestamp')[:8]

    context = {
        'colleges': colleges,
        'college_admins': college_admins,
        'recent_activity': recent_activity,
        'total_colleges': colleges.count(),
        'total_college_admins': college_admins.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'dashboards/super_admin.html', context)


@login_required
def super_admin_college_add(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        if not name or not code:
            messages.error(request, 'College name and code are required.')
        elif College.objects.filter(Q(name=name) | Q(code=code)).exists():
            messages.error(request, 'A college with this name or code already exists.')
        else:
            College.objects.create(name=name, code=code, city=city, state=state)
            messages.success(request, 'College created successfully.')
            return redirect('super_admin_dashboard')

    return render(request, 'super_admin/college_form.html')


@login_required
def super_admin_college_admin_add(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

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
        else:
            college = get_object_or_404(College, pk=college_id)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password or 'College@1234',
                first_name=first_name,
                last_name=last_name,
            )
            UserRole.objects.create(user=user, role=1, college=college)
            messages.success(request, 'College admin created successfully.')
            return redirect('super_admin_dashboard')

    return render(request, 'super_admin/college_admin_form.html', {'colleges': colleges})


@login_required
def admin_dashboard(request):
    user = request.user
    if not user.is_superuser:
        try:
            if user.userrole.role != 1:
                return redirect("dashboard")
        except UserRole.DoesNotExist:
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

    total_students    = student_qs.count()
    total_faculty     = faculty_qs.count()
    total_departments = department_qs.count()
    total_hods        = hod_qs.count()
    pending_fees      = fee_qs.filter(Q(status="PENDING") | Q(status="PARTIAL")).count()
    recent_students   = student_qs.order_by("-created_at")[:5]
    recent_announcements = announcement_qs.order_by("-created_at")[:5]
    recent_requests = request_qs[:5]
    departments       = department_qs
    total_collected   = fee_qs.aggregate(s=Sum("paid_amount"))["s"] or 0
    total_pending     = sum(f.total_amount - f.paid_amount for f in fee_qs.exclude(status="PAID"))

    context = {
        "total_students": total_students, "total_faculty": total_faculty,
        "total_departments": total_departments, "total_hods": total_hods,
        "pending_fees": pending_fees, "recent_students": recent_students,
        "recent_announcements": recent_announcements, "departments": departments,
        "fee_summary": {"total_collected": total_collected, "total_pending": total_pending},
        "pending_requests": request_qs.filter(status='PENDING').count(),
        "recent_requests": recent_requests,
        "active_invites": invite_qs.filter(used_at__isnull=True).count(),
        "open_helpdesk_tickets": helpdesk_qs.exclude(status='RESOLVED').count(),
        "college": college,
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
    departments = Department.objects.filter(college=college).order_by("name")
    faculty_list = Faculty.objects.filter(department__college=college).select_related("user", "department")
    students_list = Student.objects.filter(department__college=college).select_related("user", "department")
    hod_list = HOD.objects.filter(department__college=college).select_related("user", "department")
    announcements = _scope_announcements_for_college(college).order_by("-created_at")[:8]
    recent_students = students_list.order_by("-created_at")[:8]

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
        "total_faculty": faculty_list.count(),
        "total_students": students_list.count(),
        "total_hods": hod_list.count(),
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
    faculty_list   = Faculty.objects.filter(department=dept).select_related('user')
    students_list  = Student.objects.filter(department=dept).select_related('user')
    subjects_list  = Subject.objects.filter(department=dept)
    pending_approvals = HODApproval.objects.filter(department=dept, status='PENDING').select_related('requested_by')
    recent_approvals  = HODApproval.objects.filter(department=dept).order_by('-created_at')[:10]
    announcements  = _scope_announcements_for_college(dept.college).order_by('-created_at')[:5]

    # Attendance overview per subject
    subject_attendance = []
    for subj in subjects_list:
        total_sessions = AttendanceSession.objects.filter(subject=subj).count()
        total_present  = Attendance.objects.filter(session__subject=subj, status='PRESENT').count()
        total_records  = Attendance.objects.filter(session__subject=subj).count()
        pct = round((total_present / total_records * 100), 1) if total_records > 0 else 0
        subject_attendance.append({'subject': subj, 'sessions': total_sessions, 'pct': pct})

    context = {
        'hod': hod, 'dept': dept,
        'college': dept.college,
        'total_faculty': faculty_list.count(),
        'total_students': students_list.count(),
        'total_subjects': subjects_list.count(),
        'pending_approvals_count': pending_approvals.count(),
        'faculty_list': faculty_list,
        'pending_approvals': pending_approvals,
        'recent_approvals': recent_approvals,
        'subject_attendance': subject_attendance,
        'announcements': announcements,
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


# ── FACULTY DASHBOARD ────────────────────────────────────

@login_required
def faculty_dashboard(request):
    user = request.user
    try:
        faculty = Faculty.objects.select_related('department').get(user=user)
    except Faculty.DoesNotExist:
        messages.error(request, 'Faculty profile not found. Contact admin.')
        return redirect('home')

    assigned_subjects = FacultySubject.objects.filter(faculty=faculty).select_related('subject')
    subjects = [fs.subject for fs in assigned_subjects]
    subject_cards = []
    for subject in subjects:
        latest_exam = Exam.objects.filter(
            Q(college=faculty.department.college) | Q(college__isnull=True),
            semester=subject.semester
        ).order_by('-start_date').first()
        subject_cards.append({'subject': subject, 'exam': latest_exam})

    today = timezone.now().date()
    today_sessions = AttendanceSession.objects.filter(faculty=faculty, date=today).select_related('subject')

    # Timetable for today
    day_map = {0:'MON',1:'TUE',2:'WED',3:'THU',4:'FRI',5:'SAT',6:'SUN'}
    today_day = day_map.get(today.weekday(), '')
    today_timetable = Timetable.objects.filter(faculty=faculty, day_of_week=today_day).select_related('subject','classroom').order_by('start_time')

    # Recent attendance sessions
    recent_sessions = AttendanceSession.objects.filter(faculty=faculty).order_by('-date')[:5].select_related('subject')

    # Pending assignments to review
    pending_submissions = AssignmentSubmission.objects.filter(
        assignment__created_by=user, marks__isnull=True
    ).select_related('student__user', 'assignment')[:10]
    my_assignments = Assignment.objects.filter(created_by=user).select_related('subject').order_by('-deadline')[:10]

    announcements = _scope_announcements_for_college(faculty.department.college).order_by('-created_at')[:5]

    context = {
        'faculty': faculty,
        'college': faculty.department.college,
        'subjects': subjects,
        'subject_cards': subject_cards,
        'total_subjects': len(subjects),
        'today_sessions': today_sessions,
        'today_timetable': today_timetable,
        'recent_sessions': recent_sessions,
        'pending_submissions': pending_submissions,
        'my_assignments': my_assignments,
        'announcements': announcements,
    }
    return render(request, 'dashboards/faculty.html', context)


@login_required
def faculty_mark_attendance(request, subject_id):
    """Create an attendance session and mark students."""
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
    students = Student.objects.filter(
        department=subject.department,
        current_semester=subject.semester,
        status='ACTIVE'
    ).select_related('user').order_by('roll_number')

    if request.method == 'POST':
        date_str = request.POST.get('date', str(timezone.now().date()))
        try:
            from datetime import date as dt
            session_date = dt.fromisoformat(date_str)
        except ValueError:
            session_date = timezone.now().date()

        session, created = AttendanceSession.objects.get_or_create(
            subject=subject, faculty=faculty, date=session_date
        )
        if not created:
            messages.warning(request, 'Attendance already marked for this date.')
            return redirect('faculty_dashboard')

        for student in students:
            status = request.POST.get(f'status_{student.id}', 'ABSENT')
            Attendance.objects.create(
                session=session, student=student,
                status=status, marked_by=request.user
            )
        messages.success(request, f'Attendance marked for {subject.name} on {session_date}.')
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
    exam = get_object_or_404(Exam, pk=exam_id)
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
        except (TypeError, ValueError):
            max_marks = 100
        for student in students:
            obtained = request.POST.get(f'marks_{student.id}')
            if obtained is not None and obtained.strip() != '':
                obtained = float(obtained)
                grade = _calculate_grade(obtained, max_marks)
                Marks.objects.update_or_create(
                    student=student, subject=subject, exam=exam,
                    defaults={'marks_obtained': obtained, 'max_marks': max_marks, 'grade': grade}
                )
        messages.success(request, f'Marks saved for {subject.name} — {exam.name}.')
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
            submission.save(update_fields=['marks'])
            messages.success(request, 'Submission reviewed successfully.')
            return redirect(f"{reverse('faculty_dashboard')}#submissions")
    return render(request, 'faculty/review_submission.html', {'submission': submission})


def _calculate_grade(obtained, max_marks):
    pct = (obtained / max_marks) * 100
    if pct >= 90: return 'O'
    if pct >= 80: return 'A+'
    if pct >= 70: return 'A'
    if pct >= 60: return 'B+'
    if pct >= 50: return 'B'
    if pct >= 40: return 'C'
    return 'F'


# ── STUDENT DASHBOARD ────────────────────────────────────

@login_required
def student_dashboard(request):
    user = request.user
    try:
        student = Student.objects.select_related('user', 'department').get(user=user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Contact admin.')
        return redirect('home')

    # Attendance per subject
    subjects = Subject.objects.filter(
        department=student.department,
        semester=student.current_semester
    )
    attendance_data = []
    overall_present = overall_total = 0
    for subj in subjects:
        total   = Attendance.objects.filter(session__subject=subj, student=student).count()
        present = Attendance.objects.filter(session__subject=subj, student=student, status='PRESENT').count()
        pct     = round((present / total * 100), 1) if total > 0 else None
        overall_present += present
        overall_total   += total
        attendance_data.append({'subject': subj, 'present': present, 'total': total, 'pct': pct})

    overall_attendance = round((overall_present / overall_total * 100), 1) if overall_total > 0 else None

    # Results
    result_breakdown, results = _student_result_breakdown(student)
    latest_result = results.first()
    cgpa = None
    if results.exists():
        cgpa = round(sum(r.gpa for r in results) / results.count(), 2)

    profile = StudentProfile.objects.filter(user=user).first()
    address = Address.objects.filter(user=user).order_by('id').first()
    parent = Parent.objects.filter(user=user).order_by('id').first()
    emergency_contact = EmergencyContact.objects.filter(user=user).order_by('id').first()

    # Fee
    try:
        fee = Fee.objects.get(student=student)
    except Fee.DoesNotExist:
        fee = None
    balance_due = max((fee.total_amount - fee.paid_amount), 0) if fee else 0
    recent_payments = Payment.objects.filter(fee=fee).order_by('-paid_at', '-created_at')[:5] if fee else []

    # Timetable today
    today = timezone.now().date()
    day_map = {0:'MON',1:'TUE',2:'WED',3:'THU',4:'FRI',5:'SAT',6:'SUN'}
    today_day = day_map.get(today.weekday(), '')
    today_timetable = Timetable.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
        day_of_week=today_day
    ).select_related('subject','faculty__user','classroom').order_by('start_time')

    # Pending assignments
    pending_assignments = Assignment.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
        deadline__gte=timezone.now()
    ).exclude(
        assignmentsubmission__student=student
    ).select_related('subject').order_by('deadline')[:5]
    submitted_assignments = AssignmentSubmission.objects.filter(
        student=student
    ).select_related('assignment__subject').order_by('-submitted_at')[:8]

    # Announcements
    announcements = _scope_announcements_for_college(student.department.college).order_by('-created_at')[:5]

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
        'today_timetable': today_timetable,
        'pending_assignments': pending_assignments,
        'submitted_assignments': submitted_assignments,
        'announcements': announcements,
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
            'inter_passed_year': int(request.POST.get('inter_passed_year')),
            'inter_percentage': float(request.POST.get('inter_percentage')),
            'school_name': request.POST.get('school_name', '').strip(),
            'school_passed_year': int(request.POST.get('school_passed_year')),
            'school_percentage': float(request.POST.get('school_percentage')),
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
            address = Address.objects.create(user=request.user, **address_data)
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
            parent = Parent.objects.create(user=request.user, **parent_data)
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


@login_required
def student_fee_payment(request):
    try:
        student = Student.objects.select_related('department').get(user=request.user)
        fee = Fee.objects.get(student=student)
    except (Student.DoesNotExist, Fee.DoesNotExist):
        messages.error(request, 'Fee record not found. Contact admin.')
        return redirect('home')

    balance_due = max(fee.total_amount - fee.paid_amount, 0)
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except InvalidOperation:
            amount = Decimal('0')
        payment_method = request.POST.get('payment_method', '').strip() or 'UPI'

        if amount <= 0:
            messages.error(request, 'Enter a valid payment amount.')
        elif amount > Decimal(str(balance_due)):
            messages.error(request, 'Payment amount cannot be greater than the remaining balance.')
        else:
            payment = Payment.objects.create(
                user=request.user,
                fee=fee,
                amount=float(amount),
                payment_type='Tuition Fee',
                transaction_id=f"PAY-{timezone.now():%Y%m%d%H%M%S}-{uuid4().hex[:6].upper()}",
                status='SUCCESS',
                payment_method=payment_method,
                paid_at=timezone.now(),
            )
            fee.paid_amount = float(Decimal(str(fee.paid_amount)) + amount)
            _sync_fee_status(fee)
            fee.save(update_fields=['paid_amount', 'status'])
            messages.success(request, 'Payment completed successfully.')
            return redirect('student_payment_receipt', pk=payment.pk)

    recent_payments = Payment.objects.filter(fee=fee).order_by('-paid_at', '-created_at')[:8]
    return render(request, 'student/payment_form.html', {
        'student': student,
        'fee': fee,
        'balance_due': balance_due,
        'recent_payments': recent_payments,
    })


@login_required
def student_payment_receipt(request, pk):
    payment = get_object_or_404(Payment.objects.select_related('fee__student'), pk=pk, user=request.user)
    balance_due = max(payment.fee.total_amount - payment.fee.paid_amount, 0) if payment.fee_id else 0
    return render(request, 'student/payment_receipt.html', {
        'payment': payment,
        'balance_due': balance_due,
    })


@login_required
def student_payment_receipt_pdf(request, pk):
    payment = get_object_or_404(Payment.objects.select_related('fee__student'), pk=pk, user=request.user)
    fee = payment.fee
    student = fee.student if fee else None
    lines = [
        f"Receipt Date: {timezone.localtime(payment.paid_at).strftime('%d %b %Y %H:%M') if payment.paid_at else '-'}",
        f"Transaction ID: {payment.transaction_id}",
        f"Student: {student.user.get_full_name() if student else request.user.get_full_name()}",
        f"Roll Number: {student.roll_number if student else '-'}",
        f"Department: {student.department.code if student else '-'}",
        f"Paid Amount: Rs {payment.amount:.2f}",
        f"Payment Method: {payment.payment_method}",
        f"Fee Status: {fee.status if fee else payment.status}",
    ]
    return _pdf_response(
        f"payment-receipt-{payment.pk}.pdf",
        "EduTrack Payment Receipt",
        lines,
        generated_by=request.user,
        report_type='PAYMENT',
    )


@login_required
def student_result_report_pdf(request):
    try:
        student = Student.objects.select_related('department', 'user').get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Contact admin.')
        return redirect('home')

    result_breakdown, results = _student_result_breakdown(student)
    if not results.exists():
        messages.error(request, 'No published results found yet.')
        return redirect(f"{reverse('student_dashboard')}#results")

    lines = [
        f"Student: {student.user.get_full_name() or student.user.username}",
        f"Roll Number: {student.roll_number}",
        f"Department: {student.department.name}",
        "",
    ]
    for item in reversed(result_breakdown):
        result = item.get('result')
        semester = result.semester if result else item['semester']
        if result:
            lines.append(
                f"Semester {semester}: GPA {result.gpa:.2f}, Percentage {result.percentage:.1f}, Total Marks {result.total_marks:.0f}"
            )
        else:
            lines.append(f"Semester {semester}: Subject-wise marks available below")
        for mark in item['marks']:
            lines.append(
                f"  {mark.subject.code} {mark.subject.name}: {mark.marks_obtained:.0f}/{mark.max_marks:.0f} ({mark.grade or 'NA'})"
            )
        lines.append("")

    return _pdf_response(
        f"student-result-{student.roll_number}.pdf",
        "EduTrack Student Result Report",
        lines,
        generated_by=request.user,
        report_type='RESULT',
    )


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
    departments = _scope_departments(request).annotate(
        student_count=Count('student'),
        faculty_count=Count('faculty')
    ).order_by('name')
    return render(request, 'admin_panel/departments.html', {'departments': departments})


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
        elif Department.objects.filter(code=code).exists():
            messages.error(request, f'Department code "{code}" already exists.')
        else:
            Department.objects.create(
                college=college,
                name=name, code=code,
                description=desc or None,
                established_year=int(year) if year else None
            )
            messages.success(request, f'Department "{name}" added.')
            return redirect('admin_departments')
    return render(request, 'admin_panel/department_form.html', {'action': 'Add'})


@login_required
def admin_department_edit(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    dept = get_object_or_404(_scope_departments(request), pk=pk)
    if request.method == 'POST':
        dept.name  = request.POST.get('name', dept.name).strip()
        dept.code  = request.POST.get('code', dept.code).strip().upper()
        dept.description = request.POST.get('description', '').strip() or None
        year = request.POST.get('established_year', '').strip()
        dept.established_year = int(year) if year else None
        dept.save()
        messages.success(request, 'Department updated.')
        return redirect('admin_departments')
    return render(request, 'admin_panel/department_form.html', {'action': 'Edit', 'dept': dept})


@login_required
def admin_department_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    dept = get_object_or_404(_scope_departments(request), pk=pk)
    if request.method == 'POST':
        dept.delete()
        messages.success(request, 'Department deleted.')
    return redirect('admin_departments')


# ── STUDENTS ────────────────────────────────────────────

@login_required
def admin_students(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    dept_filter = request.GET.get('dept', '')
    sem_filter  = request.GET.get('sem', '')
    departments = _scope_departments(request).order_by('name')
    qs = Student.objects.select_related('user', 'department').filter(department__in=departments).order_by('-created_at')
    if dept_filter:
        qs = qs.filter(department_id=dept_filter)
    if sem_filter:
        qs = qs.filter(current_semester=sem_filter)
    return render(request, 'admin_panel/students.html', {
        'students': qs, 'departments': departments,
        'dept_filter': dept_filter, 'sem_filter': sem_filter,
    })


@login_required
def admin_students_export_csv(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    dept_filter = request.GET.get('dept', '')
    sem_filter = request.GET.get('sem', '')
    departments = _scope_departments(request).order_by('name')
    students = Student.objects.select_related('user', 'department').filter(department__in=departments).order_by('roll_number')
    if dept_filter:
        students = students.filter(department_id=dept_filter)
    if sem_filter:
        students = students.filter(current_semester=sem_filter)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students-export.csv"'
    writer = csv.writer(response)
    writer.writerow(['Roll Number', 'Username', 'Name', 'Email', 'College', 'Department', 'Semester', 'Admission Year', 'Status'])
    for student in students:
        writer.writerow([
            student.roll_number,
            student.user.username,
            student.user.get_full_name() or student.user.username,
            student.user.email,
            student.department.college.name if student.department.college else '',
            student.department.code,
            student.current_semester,
            student.admission_year,
            student.status,
        ])
    return response


@login_required
def admin_registration_requests(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    requests_qs = _scope_registration_requests(request)
    status_filter = request.GET.get('status', '')
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    return render(request, 'admin_panel/registration_requests.html', {
        'requests_list': requests_qs,
        'status_filter': status_filter,
    })


@login_required
def admin_registration_request_update(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    reg_request = get_object_or_404(_scope_registration_requests(request), pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action in {'REVIEWED', 'REJECTED', 'CONVERTED'}:
            reg_request.status = action
            reg_request.save(update_fields=['status'])
            messages.success(request, f'Request marked as {action.lower()}.')
    return redirect('admin_registration_requests')


@login_required
def admin_registration_invites(request):
    if not _admin_guard(request):
        return redirect('dashboard')

    college = _get_admin_college(request) or _default_college()
    departments = Department.objects.filter(college=college).order_by('name')
    invites = RegistrationInvite.objects.filter(college=college).select_related('department', 'created_by').order_by('-created_at')

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
            return redirect(f"{reverse('admin_registration_invites')}?created={invite.pk}")

    created_invite = None
    created_link = None
    created_id = request.GET.get('created')
    if created_id:
        created_invite = invites.filter(pk=created_id).first()
        if created_invite:
            created_link = _build_registration_invite_url(request, created_invite)

    return render(request, 'admin_panel/student_invites.html', {
        'invites': invites,
        'departments': departments,
        'created_invite': created_invite,
        'created_link': created_link,
    })


@login_required
def admin_student_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    request_id = request.GET.get('request') or request.POST.get('request_id')
    intake_request = None
    if request_id:
        intake_request = _scope_registration_requests(request).filter(pk=request_id).first()
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
        roll_number = _generate_roll_number(department, int(adm_year)) if department and adm_year else ''
        if not username and roll_number:
            username = roll_number.lower()

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        elif not department or not adm_year or not semester:
            messages.error(request, 'Department, admission year, and semester are required.')
        elif Student.objects.filter(roll_number=roll_number).exists():
            messages.error(request, 'Roll number already exists.')
        else:
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name
            )
            UserRole.objects.create(user=user, role=4, college=department.college)
            Student.objects.create(
                user=user, roll_number=roll_number,
                department=department,
                admission_year=int(adm_year),
                current_semester=int(semester),
                status=status
            )
            if intake_request:
                intake_request.status = 'CONVERTED'
                intake_request.save(update_fields=['status'])
            messages.success(request, f'Student {roll_number} added.')
            return redirect('admin_students')
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
        student.admission_year   = int(request.POST.get('admission_year', student.admission_year))
        student.current_semester = int(request.POST.get('current_semester', student.current_semester))
        student.status           = request.POST.get('status', student.status)
        student.save()
        UserRole.objects.filter(user=student.user).update(college=student.department.college)
        messages.success(request, 'Student updated.')
        return redirect('admin_students')
    return render(request, 'admin_panel/student_form.html', {
        'student': student, 'departments': departments, 'action': 'Edit'
    })


@login_required
def admin_student_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    student = get_object_or_404(Student.objects.filter(department__in=_scope_departments(request)), pk=pk)
    if request.method == 'POST':
        student.user.delete()  # cascades to Student
        messages.success(request, 'Student deleted.')
    return redirect('admin_students')


# ── FACULTY ─────────────────────────────────────────────

@login_required
def admin_faculty_list(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    faculty = Faculty.objects.select_related('user', 'department').filter(department__in=departments).order_by('department__name', 'user__first_name')
    dept_filter = request.GET.get('dept', '')
    if dept_filter:
        faculty = faculty.filter(department_id=dept_filter)
    return render(request, 'admin_panel/faculty.html', {
        'faculty': faculty, 'departments': departments, 'dept_filter': dept_filter
    })


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
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name
            )
            UserRole.objects.create(user=user, role=3, college=department.college)
            Faculty.objects.create(
                user=user, employee_id=employee_id, department=department,
                designation=designation, qualification=qualification,
                experience_years=int(experience), phone_number=phone
            )
            messages.success(request, f'Faculty {first_name} {last_name} added.')
            return redirect('admin_faculty_list')
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
        faculty.experience_years= int(request.POST.get('experience_years', faculty.experience_years))
        faculty.phone_number    = request.POST.get('phone_number', faculty.phone_number).strip()
        faculty.save()
        UserRole.objects.filter(user=faculty.user).update(college=faculty.department.college)
        messages.success(request, 'Faculty updated.')
        return redirect('admin_faculty_list')
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
    return redirect('admin_faculty_list')


# ── HODs ────────────────────────────────────────────────

@login_required
def admin_hods(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    departments = _scope_departments(request).order_by('name')
    hods = HOD.objects.select_related('user', 'department').filter(department__in=departments).order_by('department__name')
    return render(request, 'admin_panel/hods.html', {'hods': hods, 'departments': departments})


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

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        elif HOD.objects.filter(department_id=dept_id).exists():
            messages.error(request, 'This department already has an HOD.')
        else:
            department = get_object_or_404(departments, pk=dept_id)
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name
            )
            UserRole.objects.create(user=user, role=2, college=department.college)
            HOD.objects.create(
                user=user, employee_id=employee_id, department=department,
                qualification=qualification, experience_years=int(experience),
                phone_number=phone
            )
            messages.success(request, f'HOD {first_name} {last_name} added.')
            return redirect('admin_hods')
    return render(request, 'admin_panel/hod_form.html', {'departments': departments})


@login_required
def admin_hod_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    hod = get_object_or_404(HOD.objects.filter(department__in=_scope_departments(request)), pk=pk)
    if request.method == 'POST':
        hod.user.delete()
        messages.success(request, 'HOD deleted.')
    return redirect('admin_hods')


# ── SUBJECTS ────────────────────────────────────────────

@login_required
def admin_subjects(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    dept_filter = request.GET.get('dept', '')
    departments = _scope_departments(request).order_by('name')
    qs = Subject.objects.select_related('department').filter(department__in=departments).order_by('department__code', 'semester', 'name')
    if dept_filter:
        qs = qs.filter(department_id=dept_filter)
    return render(request, 'admin_panel/subjects.html', {
        'subjects': qs, 'departments': departments, 'dept_filter': dept_filter
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
        if Subject.objects.filter(code=code).exists():
            messages.error(request, f'Subject code "{code}" already exists.')
        else:
            department = get_object_or_404(departments, pk=dept_id)
            Subject.objects.create(name=name, code=code, department=department, semester=int(semester))
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


@login_required
def admin_academic_planner(request):
    if not _admin_guard(request):
        return redirect('dashboard')

    departments = _scope_departments(request).order_by('name')
    dept_filter = request.GET.get('dept') or request.POST.get('department')
    sem_filter = request.GET.get('sem') or request.POST.get('semester') or '1'
    department = departments.filter(pk=dept_filter).first() if dept_filter else departments.first()
    selected_semester = int(sem_filter) if str(sem_filter).isdigit() else 1

    if request.method == 'POST' and department:
        action = request.POST.get('planner_action')
        if action == 'add_subject':
            name = request.POST.get('name', '').strip()
            code = request.POST.get('code', '').strip().upper()
            if not name or not code:
                messages.error(request, 'Subject name and code are required.')
            elif Subject.objects.filter(code=code).exists():
                messages.error(request, 'Subject code already exists.')
            else:
                Subject.objects.create(name=name, code=code, department=department, semester=selected_semester)
                messages.success(request, 'Subject added to the selected semester.')
        elif action == 'assign_faculty':
            subject_id = request.POST.get('subject_id')
            faculty_id = request.POST.get('faculty_id')
            subject = Subject.objects.filter(pk=subject_id, department=department, semester=selected_semester).first()
            faculty = Faculty.objects.filter(pk=faculty_id, department=department).first()
            if not subject or not faculty:
                messages.error(request, 'Select a valid subject and faculty member.')
            else:
                FacultySubject.objects.get_or_create(subject=subject, faculty=faculty)
                messages.success(request, 'Faculty assigned to subject.')
        elif action == 'remove_assignment':
            assignment_id = request.POST.get('assignment_id')
            FacultySubject.objects.filter(pk=assignment_id, subject__department=department, subject__semester=selected_semester).delete()
            messages.success(request, 'Faculty assignment removed.')
        elif action == 'add_availability':
            faculty_id = request.POST.get('faculty_id')
            faculty = Faculty.objects.filter(pk=faculty_id, department=department).first()
            if not faculty:
                messages.error(request, 'Select a valid faculty member.')
            else:
                FacultyAvailability.objects.update_or_create(
                    faculty=faculty,
                    day_of_week=request.POST.get('day_of_week'),
                    start_time=request.POST.get('start_time'),
                    end_time=request.POST.get('end_time'),
                    defaults={'is_available': True},
                )
                messages.success(request, 'Faculty availability slot saved.')
        elif action == 'generate_timetable':
            created_count = _auto_generate_timetable(department, selected_semester)
            if created_count:
                messages.success(request, f'Automatic timetable updated with {created_count} scheduled class slot(s).')
            else:
                messages.warning(request, 'No timetable entries could be generated. Add subjects, faculty assignments, and availability first.')
        return redirect(f"{reverse('admin_academic_planner')}?dept={department.pk}&sem={selected_semester}")

    faculty = Faculty.objects.filter(department=department).select_related('user').order_by('user__first_name') if department else Faculty.objects.none()
    subjects = Subject.objects.filter(department=department, semester=selected_semester).order_by('name') if department else Subject.objects.none()
    subject_assignments = FacultySubject.objects.filter(subject__in=subjects).select_related('subject', 'faculty__user').order_by('subject__name')
    availability = FacultyAvailability.objects.filter(faculty__in=faculty).select_related('faculty__user').order_by('faculty__user__first_name', 'day_of_week', 'start_time')
    timetable_entries = Timetable.objects.filter(subject__in=subjects).select_related('subject', 'faculty__user', 'classroom').order_by('day_of_week', 'start_time')

    return render(request, 'admin_panel/academic_planner.html', {
        'departments': departments,
        'department': department,
        'selected_semester': selected_semester,
        'faculty': faculty,
        'subjects': subjects,
        'subject_assignments': subject_assignments,
        'availability': availability,
        'timetable_entries': timetable_entries,
    })


@login_required
def admin_helpdesk(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    tickets = _scope_helpdesk_tickets(request)
    status_filter = request.GET.get('status', '')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    return render(request, 'admin_panel/helpdesk.html', {
        'tickets': tickets,
        'status_filter': status_filter,
    })


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
            messages.success(request, 'Help desk ticket updated.')
    return redirect('admin_helpdesk')


# ── FEES ────────────────────────────────────────────────

@login_required
def admin_fees(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    status_filter = request.GET.get('status', '')
    qs = Fee.objects.select_related('student__user', 'student__department').filter(student__department__in=_scope_departments(request)).order_by('status', 'student__roll_number')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'admin_panel/fees.html', {'fees': qs, 'status_filter': status_filter})


@login_required
def admin_fee_add(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    students = Student.objects.select_related('user').filter(department__in=_scope_departments(request)).order_by('roll_number')
    if request.method == 'POST':
        student_id   = request.POST.get('student')
        total_amount = request.POST.get('total_amount')
        paid_amount  = request.POST.get('paid_amount', 0)
        status       = request.POST.get('status', 'PENDING')
        if Fee.objects.filter(student_id=student_id).exists():
            messages.error(request, 'Fee record already exists for this student. Use Edit instead.')
        else:
            fee = Fee(
                student_id=student_id,
                total_amount=float(total_amount),
                paid_amount=float(paid_amount),
                status=status
            )
            _sync_fee_status(fee)
            fee.save()
            messages.success(request, 'Fee record added.')
            return redirect('admin_fees')
    return render(request, 'admin_panel/fee_form.html', {'students': students, 'action': 'Add'})


@login_required
def admin_fee_edit(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    fee = get_object_or_404(Fee.objects.filter(student__department__in=_scope_departments(request)), pk=pk)
    if request.method == 'POST':
        fee.total_amount = float(request.POST.get('total_amount', fee.total_amount))
        fee.paid_amount  = float(request.POST.get('paid_amount', fee.paid_amount))
        fee.status       = request.POST.get('status', fee.status)
        _sync_fee_status(fee)
        fee.save()
        messages.success(request, 'Fee record updated.')
        return redirect('admin_fees')
    return render(request, 'admin_panel/fee_form.html', {'fee': fee, 'action': 'Edit'})


# ── ANNOUNCEMENTS ────────────────────────────────────────

@login_required
def admin_announcements(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    announcements = _scope_announcements_for_college(_get_admin_college(request)).select_related('created_by').order_by('-created_at')
    return render(request, 'admin_panel/announcements.html', {'announcements': announcements})


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
            return redirect('admin_announcements')
    return render(request, 'admin_panel/announcement_form.html')


@login_required
def admin_announcement_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    ann = get_object_or_404(_scope_announcements_for_college(_get_admin_college(request)), pk=pk)
    if request.method == 'POST':
        ann.delete()
        messages.success(request, 'Announcement deleted.')
    return redirect('admin_announcements')


# ── EXAMS ────────────────────────────────────────────────

@login_required
def admin_exams(request):
    if not _admin_guard(request):
        return redirect('dashboard')
    exams = _scope_exams(request).select_related('created_by').order_by('-start_date')
    return render(request, 'admin_panel/exams.html', {'exams': exams})


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
            name=name, semester=int(semester),
            start_date=start_date, end_date=end_date,
            created_by=request.user
        )
        messages.success(request, f'Exam "{name}" created.')
        return redirect('admin_exams')
    return render(request, 'admin_panel/exam_form.html')


@login_required
def admin_exam_delete(request, pk):
    if not _admin_guard(request):
        return redirect('dashboard')
    exam = get_object_or_404(_scope_exams(request), pk=pk)
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted.')
    return redirect('admin_exams')


@login_required
def admin_report_pdf(request, report_type):
    if not _admin_guard(request):
        return redirect('dashboard')

    departments = _scope_departments(request)
    college = _get_admin_college(request)

    if report_type == 'attendance':
        lines = [f"Attendance summary for {college.name if college else 'All Colleges'}", ""]
        for department in departments.order_by('code'):
            total_records = Attendance.objects.filter(student__department=department).count()
            total_present = Attendance.objects.filter(student__department=department, status='PRESENT').count()
            percentage = round((total_present / total_records * 100), 1) if total_records else 0
            lines.append(f"{department.code}: {total_present}/{total_records} present records ({percentage}%)")
        title = 'EduTrack Attendance Report'
        system_report_type = 'ATTENDANCE'
    elif report_type == 'payments':
        fee_qs = Fee.objects.filter(student__department__in=departments).select_related('student__user', 'student__department')
        lines = [f"Payment summary for {college.name if college else 'All Colleges'}", ""]
        for fee in fee_qs.order_by('student__roll_number'):
            balance = max(fee.total_amount - fee.paid_amount, 0)
            lines.append(
                f"{fee.student.roll_number} - {fee.student.user.get_full_name() or fee.student.user.username} - "
                f"{fee.student.department.code} - Paid Rs {fee.paid_amount:.0f} / Rs {fee.total_amount:.0f} - "
                f"Balance Rs {balance:.0f} - {fee.status}"
            )
        title = 'EduTrack Payment Report'
        system_report_type = 'PAYMENT'
    elif report_type == 'results':
        result_qs = Result.objects.filter(student__department__in=departments).select_related('student__user', 'student__department')
        lines = [f"Result summary for {college.name if college else 'All Colleges'}", ""]
        for result in result_qs.order_by('student__roll_number', 'semester'):
            lines.append(
                f"{result.student.roll_number} - {result.student.user.get_full_name() or result.student.user.username} - "
                f"Sem {result.semester} - GPA {result.gpa:.2f} - {result.percentage:.1f}%"
            )
        title = 'EduTrack Result Report'
        system_report_type = 'RESULT'
    else:
        raise PermissionDenied('Invalid report type.')

    return _pdf_response(
        f"{report_type}-report-{timezone.now():%Y%m%d%H%M%S}.pdf",
        title,
        lines,
        generated_by=request.user,
        report_type=system_report_type,
    )


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
