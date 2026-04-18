"""
Unified marks entry view — combines internal marks (IA1, IA2, assignment, attendance)
and external marks (exam marks) into a single tabbed page.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse

from ..models import (
    Faculty, FacultySubject, Subject, Exam, Marks, InternalMark,
    HODApproval, Notification, HOD,
)
from ._legacy import _get_section_students, _calculate_grade, _grade_to_point, _get_evaluation_scheme


@login_required
def faculty_marks_unified(request, subject_id):
    """
    Single unified marks entry page with two tabs:
      - Internal Marks (IA1, IA2, Assignment, Attendance)
      - External Marks (per exam, with grade preview)

    Replaces the three separate views:
      faculty_internal_marks, faculty_enter_marks, faculty_submit_ce_marks
    """
    faculty = get_object_or_404(Faculty, user=request.user)
    get_object_or_404(FacultySubject, faculty=faculty, subject_id=subject_id)
    subject = get_object_or_404(Subject, pk=subject_id)
    students = _get_section_students(faculty, subject)

    college = faculty.department.college
    scheme = _get_evaluation_scheme(college, faculty.department)

    # Available exams for this subject's semester
    exams = Exam.objects.filter(
        college=college, semester=subject.semester
    ).order_by('-start_date')

    # Selected exam (from GET param or first available)
    selected_exam_id = request.GET.get('exam_id') or request.POST.get('exam_id')
    selected_exam = None
    if selected_exam_id:
        selected_exam = Exam.objects.filter(pk=selected_exam_id, college=college).first()
    if not selected_exam and exams.exists():
        selected_exam = exams.first()

    # Existing internal marks
    internal_map = {
        im.student_id: im
        for im in InternalMark.objects.filter(subject=subject, student__in=students)
    }

    # Existing external marks for selected exam
    external_map = {}
    if selected_exam:
        external_map = {
            m.student_id: m
            for m in Marks.objects.filter(subject=subject, exam=selected_exam, student__in=students)
        }

    # CE submission status
    ce_submission = HODApproval.objects.filter(
        requested_by=request.user,
        approval_type='CE_MARKS',
        subject=subject,
    ).order_by('-created_at').first()

    # ── POST handling ─────────────────────────────────────────────────────────
    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'save_internal':
            _save_internal_marks(request, faculty, subject, students, internal_map)
            return redirect(f"{reverse('faculty_marks_unified', args=[subject_id])}?tab=internal&exam_id={selected_exam_id or ''}")

        elif action == 'submit_ce':
            _submit_ce_to_hod(request, faculty, subject, students)
            return redirect(f"{reverse('faculty_marks_unified', args=[subject_id])}?tab=internal&exam_id={selected_exam_id or ''}")

        elif action == 'save_external' and selected_exam:
            _save_external_marks(request, faculty, subject, selected_exam, students, scheme)
            return redirect(f"{reverse('faculty_marks_unified', args=[subject_id])}?tab=external&exam_id={selected_exam.pk}")

    # Build rows for both tabs
    internal_rows = [{'student': s, 'im': internal_map.get(s.id)} for s in students]
    external_rows = [{'student': s, 'existing_mark': external_map.get(s.id)} for s in students]

    # Default max marks from existing or 100
    default_max = 100
    if external_map:
        first = next(iter(external_map.values()))
        default_max = first.max_marks

    active_tab = request.GET.get('tab', 'internal')

    return render(request, 'faculty/marks_unified.html', {
        'subject': subject,
        'students': students,
        'exams': exams,
        'selected_exam': selected_exam,
        'internal_rows': internal_rows,
        'external_rows': external_rows,
        'ce_submission': ce_submission,
        'default_max': default_max,
        'active_tab': active_tab,
        'scheme': scheme,
    })


# ── Internal helpers ──────────────────────────────────────────────────────────

def _save_internal_marks(request, faculty, subject, students, existing_map):
    """Save IA1, IA2, assignment, attendance marks for all students."""
    saved = 0
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
            saved += 1
    messages.success(request, f'Internal marks saved for {subject.name} ({saved} students).')


def _submit_ce_to_hod(request, faculty, subject, students):
    """Submit CE marks to HOD for review."""
    existing = HODApproval.objects.filter(
        requested_by=request.user,
        approval_type='CE_MARKS',
        subject=subject,
        status='PENDING',
    ).first()
    if existing:
        messages.warning(request, f'CE marks for {subject.name} are already pending HOD review.')
        return

    filled = InternalMark.objects.filter(subject=subject, student__in=students).count()
    total = students.count()

    if filled == 0:
        messages.error(request, f'No internal marks entered for {subject.name} yet.')
        return

    HODApproval.objects.create(
        requested_by=request.user,
        department=subject.department,
        subject=subject,
        approval_type='CE_MARKS',
        description=(
            f'CE marks submission for {subject.name} ({subject.code}) — '
            f'Semester {subject.semester}. {filled}/{total} students have marks entered.'
        ),
    )

    # Notify HOD
    hod = HOD.objects.filter(department=subject.department, is_active=True).first()
    if hod:
        Notification.objects.create(
            user=hod.user,
            message=(
                f'{request.user.get_full_name() or request.user.username} submitted '
                f'CE marks for {subject.name} (Sem {subject.semester}) for your review.'
            ),
        )
    messages.success(request, f'CE marks for {subject.name} submitted to HOD for review.')


def _save_external_marks(request, faculty, subject, exam, students, scheme):
    """Save external exam marks for all students."""
    try:
        max_marks = float(request.POST.get('max_marks', 100))
        if max_marks <= 0:
            raise ValueError
    except (TypeError, ValueError):
        max_marks = 100

    saved = errors = 0
    with transaction.atomic():
        for student in students:
            raw = request.POST.get(f'marks_{student.id}', '').strip()
            if not raw:
                continue
            try:
                obtained = float(raw)
            except ValueError:
                messages.error(request, f'Invalid marks for {student.roll_number}.')
                errors += 1
                continue
            if obtained < 0 or obtained > max_marks:
                messages.error(request, f'Marks out of range for {student.roll_number}.')
                errors += 1
                continue

            grade = _calculate_grade(obtained, max_marks, scheme=scheme)
            Marks.objects.update_or_create(
                student=student, subject=subject, exam=exam,
                defaults={
                    'marks_obtained': obtained,
                    'max_marks': max_marks,
                    'grade': grade,
                    'grade_point': _grade_to_point(grade),
                }
            )
            saved += 1

    if saved:
        messages.success(request, f'External marks saved for {saved} student(s) in {subject.name} — {exam.name}.')
    if errors:
        messages.warning(request, f'{errors} row(s) had validation errors and were skipped.')
