"""
URL patterns for the EduTrack REST API v1.
Mounted at /api/v1/ in studentmanagementsystem/urls.py
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import api_views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path('token/', TokenObtainPairView.as_view(), name='api_token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),

    # ── User ──────────────────────────────────────────────────────────────────
    path('me/', api_views.api_me, name='api_me'),

    # ── Student ───────────────────────────────────────────────────────────────
    path('dashboard/', api_views.api_student_dashboard, name='api_student_dashboard'),
    path('attendance/', api_views.api_attendance, name='api_attendance'),
    path('results/', api_views.api_results, name='api_results'),
    path('timetable/', api_views.api_timetable, name='api_timetable'),
    path('assignments/', api_views.api_assignments, name='api_assignments'),
    path('quizzes/', api_views.api_quizzes, name='api_quizzes'),
    path('fees/', api_views.api_fees, name='api_fees'),

    # ── Notifications ─────────────────────────────────────────────────────────
    path('notifications/', api_views.api_notifications, name='api_notifications'),
    path('notifications/mark-read/', api_views.api_notifications_mark_read, name='api_notifications_mark_read'),

    # ── Announcements ─────────────────────────────────────────────────────────
    path('announcements/', api_views.api_announcements, name='api_announcements'),
]
