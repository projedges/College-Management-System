"""
DRF serializers for the EduTrack REST API.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Student, Faculty, Department, Subject, Attendance, AttendanceSession,
    Result, Marks, InternalMark, Assignment, AssignmentSubmission,
    Quiz, QuizAttempt, Fee, Announcement, Notification, Timetable,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code']


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'roll_number', 'department', 'admission_year',
                  'current_semester', 'section', 'status', 'user', 'full_name']

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class SubjectSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'semester', 'credits', 'department',
                  'lecture_hours', 'tutorial_hours', 'practical_hours']


class AttendanceSessionSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = AttendanceSession
        fields = ['id', 'subject', 'date', 'faculty']


class AttendanceSerializer(serializers.ModelSerializer):
    session = AttendanceSessionSerializer(read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'session', 'status', 'marked_by']


class MarksSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = Marks
        fields = ['id', 'subject', 'marks_obtained', 'max_marks', 'grade', 'grade_point']


class InternalMarkSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = InternalMark
        fields = ['id', 'subject', 'ia1', 'ia2', 'assignment_marks', 'attendance_marks', 'total']

    def get_total(self, obj):
        return obj.total()


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ['id', 'semester', 'gpa', 'sgpa', 'total_marks', 'percentage', 'total_credits']


class AssignmentSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'subject', 'deadline', 'is_published']


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    assignment = AssignmentSerializer(read_only=True)

    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'assignment', 'submitted_at', 'marks', 'feedback', 'file']


class QuizSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'subject', 'is_active', 'duration_minutes', 'total_marks']


class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz = QuizSerializer(read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'score', 'is_submitted', 'started_at', 'submitted_at']


class FeeSerializer(serializers.ModelSerializer):
    balance_due = serializers.SerializerMethodField()

    class Meta:
        model = Fee
        fields = ['id', 'semester', 'total_amount', 'paid_amount', 'status',
                  'due_date', 'balance_due']

    def get_balance_due(self, obj):
        return obj.balance_due()


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'content', 'created_at', 'target_role']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'is_read', 'created_at']


class TimetableSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = Timetable
        fields = ['id', 'subject', 'day_of_week', 'start_time', 'end_time', 'section']


# ── Dashboard summary serializers ─────────────────────────────────────────────

class StudentDashboardSerializer(serializers.Serializer):
    """Aggregated student dashboard data for mobile app."""
    student = StudentSerializer()
    overall_attendance = serializers.FloatField(allow_null=True)
    cgpa = serializers.FloatField(allow_null=True)
    backlog_count = serializers.IntegerField()
    academic_standing = serializers.CharField()
    balance_due = serializers.FloatField()
    pending_assignments_count = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
