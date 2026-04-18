"""
REST API views for EduTrack mobile app and external integrations.

Authentication: JWT (Bearer token)
Base URL: /api/v1/

Endpoints:
  POST /api/v1/token/          — Obtain JWT token pair
  POST /api/v1/token/refresh/  — Refresh access token

  GET  /api/v1/me/             — Current user profile
  GET  /api/v1/dashboard/      — Student dashboard summary
  GET  /api/v1/attendance/     — Student attendance per subject
  GET  /api/v1/results/        — Student results (all semesters)
  GET  /api/v1/timetable/      — Today's timetable
  GET  /api/v1/assignments/    — Pending assignments
  GET  /api/v1/quizzes/        — Active quizzes
  GET  /api/v1/fees/           — Fee status
  GET  /api/v1/notifications/  — Unread notifications
  POST /api/v1/notifications/mark-read/ — Mark all as read
  GET  /api/v1/announcements/  — College announcements
"""
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q, Sum
from django.utils import timezone

from .models import (
    Student, Subject, Attendance, Result, Marks, InternalMark,
    Assignment, AssignmentSubmission, Quiz, QuizAttempt, Fee,
    Announcement, Notification, Timetable, TimetableBreak,
    AttendanceRule, UserRole,
)
from .serializers import (
    StudentSerializer, AttendanceSerializer, ResultSerializer,
    MarksSerializer, InternalMarkSerializer, AssignmentSerializer,
    AssignmentSubmissionSerializer, QuizSerializer, QuizAttemptSerializer,
    FeeSerializer, AnnouncementSerializer, NotificationSerializer,
    TimetableSerializer, StudentDashboardSerializer,
)


def _get_student(request):
    """Return Student for the authenticated user, or None."""
    try:
        return Student.objects.select_related('user', 'department__college').get(user=request.user)
    except Student.DoesNotExist:
        return None


# ── Current user ──────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_me(request):
    """Return current user's role and basic profile."""
    user = request.user
    role_obj = UserRole.objects.filter(user=user).first()
    data = {
        'id': user.id,
        'username': user.username,
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'role': role_obj.get_role_display() if role_obj else ('Super Admin' if user.is_superuser else 'Unknown'),
        'role_id': role_obj.role if role_obj else None,
    }
    return Response(data)


# ── Student dashboard summary ─────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_student_dashboard(request):
    """Aggregated dashboard data for the student mobile app."""
    student = _get_student(request)
    if not student:
        return Response({'detail': 'Student profile not found.'}, status=404)

    college = student.department.college
    subjects = Subject.objects.filter(
        department=student.department,
        semester=student.current_semester,
    )

    # Overall attendance
    att_agg = Attendance.objects.filter(
        student=student, session__subject__in=subjects
    ).aggregate(total=Count('id'), present=Count('id', filter=Q(status='PRESENT')))
    total = att_agg['total'] or 0
    present = att_agg['present'] or 0
    overall_attendance = round(present / total * 100, 1) if total > 0 else None

    # CGPA
    results = Result.objects.filter(student=student)
    cgpa = None
    if results.exists():
        total_weighted = sum(r.gpa * r.total_marks for r in results if r.total_marks > 0)
        total_marks_sum = sum(r.total_marks for r in results if r.total_marks > 0)
        if total_marks_sum > 0:
            cgpa = round(total_weighted / total_marks_sum, 2)
        else:
            cgpa = round(sum(r.gpa for r in results) / results.count(), 2)

    # Backlogs
    all_marks = Marks.objects.filter(student=student)
    backlog_subjects = set()
    passed_subjects = set()
    for m in all_marks:
        if m.marks_obtained < m.max_marks * 0.4:
            backlog_subjects.add(m.subject_id)
        else:
            passed_subjects.add(m.subject_id)
    backlog_count = len(backlog_subjects - passed_subjects)

    # Academic standing
    if cgpa is None:
        standing = 'No Results'
    elif cgpa >= 8.5:
        standing = 'Distinction'
    elif cgpa >= 7.0:
        standing = 'First Class'
    elif cgpa >= 6.0:
        standing = 'Second Class'
    elif cgpa >= 5.0:
        standing = 'Pass'
    else:
        standing = 'At Risk'

    # Fee balance
    fee = Fee.objects.filter(student=student).order_by('-semester', '-id').first()
    balance_due = max((fee.total_amount - fee.paid_amount), 0) if fee else 0

    # Pending assignments
    pending_count = Assignment.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
        deadline__gte=timezone.now(),
        is_published=True,
    ).exclude(assignmentsubmission__student=student).count()

    # Unread notifications
    unread = Notification.objects.filter(user=request.user, is_read=False).count()

    return Response({
        'student': StudentSerializer(student).data,
        'overall_attendance': overall_attendance,
        'cgpa': cgpa,
        'backlog_count': backlog_count,
        'academic_standing': standing,
        'balance_due': float(balance_due),
        'pending_assignments_count': pending_count,
        'unread_notifications': unread,
    })


# ── Attendance ────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_attendance(request):
    """Per-subject attendance stats for the current semester."""
    student = _get_student(request)
    if not student:
        return Response({'detail': 'Student profile not found.'}, status=404)

    subjects = Subject.objects.filter(
        department=student.department,
        semester=student.current_semester,
    )
    att_agg = Attendance.objects.filter(
        student=student, session__subject__in=subjects
    ).values('session__subject').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='PRESENT'))
    )
    stats = {row['session__subject']: row for row in att_agg}

    data = []
    for subj in subjects:
        s = stats.get(subj.id, {'total': 0, 'present': 0})
        pct = round(s['present'] / s['total'] * 100, 1) if s['total'] > 0 else 0
        data.append({
            'subject_id': subj.id,
            'subject_name': subj.name,
            'subject_code': subj.code,
            'total_classes': s['total'],
            'present': s['present'],
            'absent': s['total'] - s['present'],
            'percentage': pct,
        })

    return Response(data)


# ── Results ───────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_results(request):
    """All semester results for the student."""
    student = _get_student(request)
    if not student:
        return Response({'detail': 'Student profile not found.'}, status=404)

    results = Result.objects.filter(student=student).order_by('semester')
    return Response(ResultSerializer(results, many=True).data)


# ── Timetable ─────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_timetable(request):
    """Today's timetable for the student."""
    student = _get_student(request)
    if not student:
        return Response({'detail': 'Student profile not found.'}, status=404)

    today = timezone.localtime(timezone.now())
    day_map = {0: 'MON', 1: 'TUE', 2: 'WED', 3: 'THU', 4: 'FRI', 5: 'SAT', 6: 'SUN'}
    today_day = day_map.get(today.weekday(), '')

    slots = Timetable.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
        day_of_week=today_day,
    ).filter(
        Q(section='') | Q(section=student.section)
    ).select_related('subject', 'faculty__user', 'classroom').order_by('start_time')

    data = []
    for slot in slots:
        data.append({
            'subject': slot.subject.name,
            'subject_code': slot.subject.code,
            'faculty': slot.faculty.user.get_full_name() if slot.faculty else None,
            'room': slot.classroom.room_number if slot.classroom else None,
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'section': slot.section,
        })

    return Response({'day': today_day, 'date': today.date().isoformat(), 'slots': data})


# ── Assignments ───────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_assignments(request):
    """Pending and submitted assignments for the student."""
    student = _get_student(request)
    if not student:
        return Response({'detail': 'Student profile not found.'}, status=404)

    pending = Assignment.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
        deadline__gte=timezone.now(),
        is_published=True,
    ).exclude(assignmentsubmission__student=student).select_related('subject').order_by('deadline')

    submitted = AssignmentSubmission.objects.filter(
        student=student,
        assignment__subject__semester=student.current_semester,
    ).select_related('assignment__subject').order_by('-submitted_at')[:20]

    return Response({
        'pending': AssignmentSerializer(pending, many=True).data,
        'submitted': AssignmentSubmissionSerializer(submitted, many=True).data,
    })


# ── Quizzes ───────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_quizzes(request):
    """Active quizzes for the student."""
    student = _get_student(request)
    if not student:
        return Response({'detail': 'Student profile not found.'}, status=404)

    active = Quiz.objects.filter(
        subject__department=student.department,
        subject__semester=student.current_semester,
        is_active=True,
    ).select_related('subject').order_by('-created_at')

    attempted_ids = set(
        QuizAttempt.objects.filter(student=student, is_submitted=True)
        .values_list('quiz_id', flat=True)
    )

    data = []
    for quiz in active:
        d = QuizSerializer(quiz).data
        d['attempted'] = quiz.id in attempted_ids
        data.append(d)

    return Response(data)


# ── Fees ──────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_fees(request):
    """Fee status for all semesters."""
    student = _get_student(request)
    if not student:
        return Response({'detail': 'Student profile not found.'}, status=404)

    fees = Fee.objects.filter(student=student).order_by('semester')
    return Response(FeeSerializer(fees, many=True).data)


# ── Notifications ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_notifications(request):
    """Unread notifications for the user."""
    notifs = Notification.objects.filter(
        user=request.user, is_read=False
    ).order_by('-created_at')[:50]
    return Response(NotificationSerializer(notifs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_notifications_mark_read(request):
    """Mark all notifications as read."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({'status': 'ok'})


# ── Announcements ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_announcements(request):
    """Recent college announcements."""
    student = _get_student(request)
    college = student.department.college if student else None

    qs = Announcement.objects.filter(
        Q(college=college) | Q(college__isnull=True)
    ).order_by('-created_at')[:20]

    return Response(AnnouncementSerializer(qs, many=True).data)
