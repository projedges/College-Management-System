# Tier 1 Architecture Fixes — Bugfix Design

## Overview

Six architectural defects in EduTrack are addressed in this document. The fixes
span view decomposition, REST API introduction, multi-tenancy enforcement,
email delivery wiring, data model additions, and a student dashboard UI gap.
Each fix is minimal and backward-compatible: existing URL names, template
rendering, and session behaviour are preserved throughout.

---

## Glossary

- **Bug_Condition (C)**: The condition that identifies a defective input or
  system state — the trigger for each of the six issues.
- **Property (P)**: The correct observable behaviour that must hold once the
  fix is applied.
- **Preservation**: All existing behaviour that must remain unchanged after
  each fix is applied.
- **`_legacy.py`**: `students/views/_legacy.py` — the 5200+ line monolithic
  views file that is the source of Issue 1.
- **`CollegeScopeMiddleware`**: `students/middleware.py` — the middleware whose
  `process_view` returns `None` unconditionally (Issue 3).
- **`_get_admin_college` / `_scope_departments`**: Helper functions in
  `students/views/_helpers.py` that perform manual per-view college scoping
  (replaced by the new mixin in Issue 3).
- **`Notification`**: `students.models.Notification` — model that stores
  in-app notifications but has no signal-driven email dispatch (Issue 4).
- **`Program`**: New model to be added to `students/models.py` (Issue 5).
- **`AcademicCalendar` / `Holiday`**: New models to be added to
  `students/models.py` (Issue 5).
- **`student_exemption_apply`**: Existing view at
  `dashboard/student/exemption/` — already wired in `students/urls.py` but
  not linked from the student dashboard (Issue 6).
- **`student_request_override`**: Existing view at
  `dashboard/student/exam/<id>/override/` — same gap as above (Issue 6).


---

## Bug Details

### Issue 1 — Monolithic Views File

#### Fault Condition

The bug manifests when any developer opens `students/views/_legacy.py`. The
file is a single 5200+ line module containing 130+ functions across at least
nine distinct domains (auth, super_admin, admin_panel, principal, hod, faculty,
student, exam, attendance). The `students/views/__init__.py` already documents
the intended split and re-exports everything via `from ._legacy import *`, but
the actual domain modules do not yet exist.

```
FUNCTION isBugCondition_issue1(context)
  INPUT: context — a developer action (open file, add view, run git diff)
  OUTPUT: boolean

  RETURN views/_legacy.py EXISTS
         AND lineCount(views/_legacy.py) > 500
         AND domainModules(auth, student, faculty, admin_panel,
                           exam, attendance) DO NOT EXIST
END FUNCTION
```

**Examples:**
- Opening `_legacy.py` presents 5200 lines with no domain separation.
- Adding a new student view requires editing the same file as auth and exam
  logic, causing merge conflicts on any team of >1 developer.
- `git blame` on `_legacy.py` shows unrelated domains interleaved throughout.

---

### Issue 2 — No REST API

#### Fault Condition

The bug manifests when any external client (mobile app, third-party service)
requests data from the application. No DRF is installed, no serializers exist,
and `students/urls.py` contains zero `/api/` routes.

```
FUNCTION isBugCondition_issue2(request)
  INPUT: request — an HTTP request to any URL
  OUTPUT: boolean

  RETURN '/api/' NOT IN urlpatterns
         AND djangoRestFramework NOT IN INSTALLED_APPS
         AND serializers/ DOES NOT EXIST
END FUNCTION
```

**Examples:**
- `GET /api/v1/students/` returns 404.
- A React Native app cannot retrieve student attendance data as JSON.
- No token authentication endpoint exists.

---

### Issue 3 — Multi-tenancy Not Enforced

#### Fault Condition

The bug manifests when a college-scoped user (role=1, college admin) makes any
request. `CollegeScopeMiddleware.process_view` returns `None` unconditionally.
Individual views call `_get_admin_college(request)` manually, but any new view
that omits this call silently returns cross-college data.

```
FUNCTION isBugCondition_issue3(request, view_func)
  INPUT: request — authenticated request from a college-scoped user
         view_func — any view function
  OUTPUT: boolean

  RETURN process_view(request, view_func, ...) IS None
         AND view_func DOES NOT call _get_admin_college(request)
         AND queryset IS NOT filtered by college
END FUNCTION
```

**Examples:**
- A new `admin_programs` view that omits `_get_admin_college` returns all
  programs from all colleges to College A's admin.
- College B's student records are visible to College A's admin if the view
  developer forgets the manual filter.

---

### Issue 4 — Email / Notifications Broken

#### Fault Condition

The bug manifests when any email-triggering event occurs (password reset,
low-attendance alert, fee reminder, notification creation). The default
`EMAIL_BACKEND` is `console.EmailBackend`. No Django signal is connected to
the `Notification` model's `post_save` to dispatch email.

```
FUNCTION isBugCondition_issue4(event)
  INPUT: event — any system event that should send an email
  OUTPUT: boolean

  RETURN EMAIL_BACKEND == 'console.EmailBackend'
         OR (Notification.post_save signal NOT connected
             AND no celery task dispatches email on Notification creation)
END FUNCTION
```

**Examples:**
- A student's attendance drops below 75%; a `Notification` record is created
  but no email reaches the student or parent.
- A fee reminder is due; the email body appears in the Django dev server
  terminal and nowhere else.
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` are
  all set in the environment but `EMAIL_BACKEND` is not overridden, so SMTP
  is never used.

---

### Issue 5 — Data Model Gaps

#### Fault Condition

Four distinct model-level defects exist:

```
FUNCTION isBugCondition_issue5(model_name, field_name)
  INPUT: model_name — Django model class name
         field_name — field being queried or created
  OUTPUT: boolean

  RETURN (model_name == 'Student'   AND 'program' FK NOT IN fields)
      OR (model_name == 'Program'   AND model DOES NOT EXIST)
      OR (model_name == 'Exam'      AND 'status' NOT IN fields)
      OR (model_name == 'Exam'      AND 'department' FK NOT IN fields)
      OR (model_name == 'Exam'      AND 'max_marks' NOT IN fields)
      OR (model_name == 'AcademicCalendar' AND model DOES NOT EXIST)
      OR (model_name == 'Holiday'   AND model DOES NOT EXIST)
END FUNCTION
```

**Examples:**
- Querying `Student.objects.filter(program__name='B.Tech')` raises
  `FieldError` because `program` does not exist on `Student`.
- Creating an `Exam` with `status='draft'` raises `TypeError` — no such field.
- An admin cannot record semester start/end dates or holidays because
  `AcademicCalendar` does not exist.
- `Subject.unique_together = ('department', 'code')` is already correct per
  the model comment; the remaining gap is that `Subject` has no `program` FK
  for program-level scoping when needed.

---

### Issue 6 — Attendance Rule Engine UI Incomplete

#### Fault Condition

The bug manifests when a student views their dashboard. The backend views
`student_exemption_apply` (URL: `student_exemption_apply`) and
`student_request_override` (URL: `student_request_override`) exist and are
wired in `students/urls.py`, but `templates/dashboards/student.html` contains
no link or card pointing to either view from the main dashboard sections.
The only existing link is a conditional "Apply Exemption" button inside the
eligibility banner — visible only when the student is already ineligible.

```
FUNCTION isBugCondition_issue6(template, section)
  INPUT: template — 'templates/dashboards/student.html'
         section  — any dashboard pane
  OUTPUT: boolean

  RETURN url('student_exemption_apply') NOT IN sidebar_links
         AND url('student_exemption_apply') NOT IN attendance_section_actions
         AND url('student_request_override') NOT IN attendance_section_actions
         AND no_standalone_attendance_requests_card EXISTS
END FUNCTION
```

**Examples:**
- A student with 74% attendance wants to apply for a medical exemption but
  cannot find the form — the only entry point is the ineligibility banner
  which only appears after eligibility is computed.
- A student wants to request an override before the exam but there is no
  link in the sidebar or attendance section.


---

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- All existing URL names in `students/urls.py` must resolve to the same views
  after the refactor — `from ._legacy import *` in `__init__.py` ensures this
  during the transition period.
- `SessionTimeoutMiddleware` idle-timeout and countdown modal behaviour must
  remain unchanged.
- All existing template rendering (dashboards, forms, PDFs, error pages) must
  continue to work without modification.
- The `_get_admin_college`, `_scope_departments`, `_scope_exams`, and
  `_scope_helpdesk_tickets` helpers in `_helpers.py` must remain available
  for backward compatibility with views not yet migrated to the new mixin.
- The `Notification` model schema must not change — only a `post_save` signal
  is added.
- The `Subject.unique_together = ('department', 'code')` constraint must not
  be removed or weakened.
- The `Exam` model's existing fields (`college`, `name`, `semester`,
  `start_date`, `end_date`, `created_by`) must remain unchanged; new fields
  are additive only.
- The `Student` model's existing fields must remain unchanged; `program` is
  an optional FK (`null=True, blank=True`) to avoid breaking existing records.

**Scope:**
All inputs that do NOT involve the six defective conditions should be
completely unaffected. This includes:
- All existing authenticated user sessions and role-based redirects.
- All existing admin panel CRUD operations.
- All existing faculty attendance marking and marks entry workflows.
- All existing exam controller workflows (hall tickets, results, revaluations).
- All existing student dashboard data (attendance, marks, fees, quizzes).
- All existing super admin college management operations.


---

## Hypothesized Root Cause

### Issue 1 — Monolithic Views File
1. **Organic growth without enforced structure**: The file started as a single
   `views.py` and was never split as the codebase grew. The `__init__.py`
   documents the intended structure but the migration was never executed.
2. **`from ._legacy import *` defers the split**: The wildcard re-export means
   the split can be done incrementally without breaking URLs, but no one has
   started the incremental migration.

### Issue 2 — No REST API
1. **DRF not installed**: `INSTALLED_APPS` contains only `'students'` and
   Django builtins — `rest_framework` is absent.
2. **No serializers directory**: There is no `students/serializers.py` or
   `students/api/` package.
3. **No API URL prefix**: `studentmanagementsystem/urls.py` only includes
   `students.urls` with no `/api/` prefix.

### Issue 3 — Multi-tenancy Not Enforced
1. **`process_view` returns `None` unconditionally**: The final line of
   `CollegeScopeMiddleware.process_view` is `return None` with a comment
   saying "Views handle their own scoping". This is the direct cause.
2. **No reusable enforcement primitive**: There is no mixin or decorator that
   views can inherit/apply to get automatic college scoping — each view must
   call `_get_admin_college` manually.

### Issue 4 — Email / Notifications Broken
1. **Default backend is console**: `settings.py` sets
   `EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'console.EmailBackend')`.
   The env var is documented in comments but not enforced.
2. **No signal on `Notification.post_save`**: `students/models.py` defines
   the `Notification` model but no `signals.py` file exists in the `students`
   app, and `students/apps.py` does not import any signals module.

### Issue 5 — Data Model Gaps
1. **`Program` never modelled**: The system distinguishes programs only by
   department name convention (e.g., "CSE B.Tech" vs "CSE M.Tech"), which is
   fragile and not queryable.
2. **`Exam` fields missing**: The `Exam` model was created early and never
   extended with workflow-state (`status`), department scoping, or a
   top-level `max_marks` field.
3. **`AcademicCalendar` never created**: Semester dates and holidays are
   managed outside the system (spreadsheets, manual configuration).

### Issue 6 — Attendance Rule Engine UI Incomplete
1. **Backend-first development**: The `student_exemption_apply` and
   `student_request_override` views were built and wired in `urls.py` but
   the corresponding UI entry points were never added to the student dashboard
   template.
2. **Conditional-only entry point**: The "Apply Exemption" button exists only
   inside the eligibility banner (`{% if not eligibility.eligible %}`), making
   it invisible to students who are still eligible but want to proactively
   apply for a medical exemption.


---

## Correctness Properties

Property 1: Fault Condition — Views File Decomposition

_For any_ developer action that opens, edits, or diffs a views domain module,
the fixed codebase SHALL present a file under 500 lines containing only
functions belonging to that domain, with all existing URL names continuing to
resolve correctly via `students/views/__init__.py`.

**Validates: Requirements 2.1, 2.2**

---

Property 2: Fault Condition — REST API Availability

_For any_ HTTP request to `/api/v1/{resource}/` where resource is one of
`students`, `attendance`, `marks`, or `fees`, the fixed system SHALL return a
JSON response with the correct DRF-serialized payload and an appropriate HTTP
status code (200, 201, 400, 401, 403, or 404).

**Validates: Requirements 2.3, 2.4**

---

Property 3: Fault Condition — Multi-tenancy Enforcement

_For any_ authenticated request from a college-scoped user (role=1) to any
view decorated with `@college_scoped` or inheriting `CollegeScopedMixin`, the
fixed system SHALL automatically filter all querysets to that user's college
and SHALL raise HTTP 403 if the requested resource belongs to a different
college, without requiring any manual `_get_admin_college` call in the view.

**Validates: Requirements 2.5, 2.6, 2.7**

---

Property 4: Fault Condition — Email Delivery

_For any_ `Notification` record created via `Notification.objects.create(...)`,
the fixed system SHALL dispatch an email to `notification.user.email` via the
configured `EMAIL_BACKEND` (SMTP in production, console in development), and
the `Notification` record SHALL be marked as sent.

**Validates: Requirements 2.8, 2.9, 2.10**

---

Property 5: Fault Condition — Data Model Completeness

_For any_ ORM query that references `Student.program`, `Exam.status`,
`Exam.department`, `Exam.max_marks`, `AcademicCalendar.semester_start`,
`AcademicCalendar.working_days`, or `Holiday.date`, the fixed system SHALL
resolve the field without raising `FieldError` or `AttributeError`.

**Validates: Requirements 2.11, 2.12, 2.13, 2.14**

---

Property 6: Fault Condition — Attendance Rule Engine UI

_For any_ authenticated student viewing their dashboard, the fixed template
SHALL display an "Attendance Requests" card in the attendance section
containing visible, always-accessible links to `student_exemption_apply` and
`student_request_override` (for an upcoming exam), regardless of the student's
current eligibility status.

**Validates: Requirements 2.15, 2.16**

---

Property 7: Preservation — Existing Behaviour Unchanged

_For any_ input where none of the six bug conditions hold (existing URL
resolution, existing template rendering, existing session timeout, existing
role-based dashboard redirect, existing admin/faculty/student CRUD), the fixed
system SHALL produce exactly the same response as the original system.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10**


---

## Fix Implementation

### Issue 1 — Views Decomposition

**Files to create:**

| Module | Functions to move from `_legacy.py` |
|--------|--------------------------------------|
| `students/views/auth.py` | `home`, `login_view`, `logout_view`, `super_admin_login_view`, `register_view` |
| `students/views/super_admin.py` | `super_admin_dashboard`, `super_admin_college_add`, `super_admin_college_admin_add`, `super_admin_college_edit`, `super_admin_college_toggle`, `super_admin_college_admin_delete`, `super_admin_college_detail`, `super_admin_platform_announcement`, `super_admin_platform_announcement_delete` |
| `students/views/admin_panel.py` | `admin_dashboard`, `admin_departments`, `admin_department_add/edit/delete`, `admin_students`, `admin_student_add/edit/delete`, `admin_students_export_csv`, `admin_students_bulk_promote`, `admin_bulk_import`, `admin_sample_csv`, `admin_faculty_list/add/edit/delete`, `admin_hods`, `admin_hod_add/delete`, `admin_subjects`, `admin_subject_add/delete`, `admin_academic_planner`, `admin_timetable_template_csv`, `admin_timetable_upload_csv`, `admin_helpdesk`, `admin_helpdesk_update`, `admin_fees`, `admin_fee_add/edit`, `admin_announcements`, `admin_announcement_add/delete`, `admin_save_colors`, `admin_exams`, `admin_exam_add/delete`, `admin_attendance_export_csv`, `admin_report_pdf`, `admin_registration_requests`, `admin_registration_request_update`, `admin_registration_invites`, `admin_attendance_rules`, `admin_attendance_rule_add`, `admin_attendance_rule_delete` |
| `students/views/principal.py` | `principal_dashboard` |
| `students/views/hod.py` | `hod_dashboard`, `hod_approve`, `hod_substitutions`, `hod_exemptions`, `hod_defaulters_report` |
| `students/views/faculty.py` | `faculty_dashboard`, `faculty_request_add`, `faculty_mark_attendance`, `faculty_enter_marks`, `faculty_assignment_create/publish`, `faculty_review_submission`, `faculty_quiz_list/create/edit/results`, `faculty_internal_marks`, `faculty_attendance_defaulters`, `faculty_lesson_plans`, `faculty_leave_apply` |
| `students/views/student.py` | `student_dashboard`, `student_profile_edit`, `student_submit_assignment`, `student_fee_payment`, `student_payment_receipt`, `student_payment_receipt_pdf`, `student_quiz_attempt`, `student_result_report_pdf`, `student_request_revaluation`, `student_exemption_apply`, `student_request_override` |
| `students/views/exam.py` | `exam_dashboard`, `exam_type_list/add/delete`, `exam_schedule`, `exam_schedule_delete`, `exam_hall_tickets`, `exam_marks_overview`, `exam_results`, `exam_revaluations`, `exam_reval_update`, `exam_staff_list/add/toggle`, `exam_scheme_list/add/delete`, `exam_valuation`, `exam_eligibility_overrides` |
| `students/views/attendance.py` | `attendance_correct` |
| `students/views/helpdesk.py` | `helpdesk_view`, `ticket_detail_view` |
| `students/views/lab.py` | `lab_staff_dashboard` |
| `students/views/errors.py` | `error_400`, `error_403`, `error_404`, `error_500`, `csrf_failure` |
| `students/views/dashboard.py` | `dashboard_redirect` |

**Changes to `students/views/__init__.py`:**
Replace `from ._legacy import *` with explicit imports from each new module,
keeping `_legacy.py` as a fallback shim during transition.

**Constraint:** Each new module must import shared utilities from
`students/views/_helpers.py` — no duplication of helper functions.

---

### Issue 2 — REST API

**New files:**

```
students/
  api/
    __init__.py
    serializers.py      # ModelSerializers for Student, Attendance, Marks, Fee
    views.py            # ModelViewSets for each resource
    urls.py             # DefaultRouter registration
```

**`settings.py` changes:**
```python
INSTALLED_APPS = [
    ...
    'students',
    'rest_framework',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}
```

**`studentmanagementsystem/urls.py` change:**
```python
path('api/v1/', include('students.api.urls')),
```

**Serializers to implement:**
- `StudentSerializer` — `id`, `roll_number`, `department`, `current_semester`, `status`
- `AttendanceSerializer` — `session`, `student`, `status`
- `MarksSerializer` — `student`, `subject`, `exam`, `marks_obtained`, `max_marks`, `grade`
- `FeeSerializer` — `student`, `semester`, `total_amount`, `paid_amount`, `status`

**ViewSets:** `ModelViewSet` for each, with college-scoped `get_queryset`
overrides using `request.user_college_id` (already set by
`SessionTimeoutMiddleware`).

---

### Issue 3 — Multi-tenancy Enforcement

**New file: `students/mixins.py`**

```python
class CollegeScopedMixin:
    """
    CBV mixin that auto-scopes get_queryset() to request.user_college_id.
    For function-based views, use the @college_scoped decorator instead.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        college_id = getattr(self.request, 'user_college_id', None)
        if college_id and not self.request.user.is_superuser:
            return qs.filter(college_id=college_id)
        return qs

def college_scoped(view_func):
    """
    Decorator for FBVs. Injects college-scoped queryset helper and raises
    PermissionDenied if a college-scoped user accesses a cross-college object.
    """
    ...
```

**`CollegeScopeMiddleware.process_view` change:**
Replace the final `return None` with actual enforcement logic that checks
URL kwargs (`college_id`, `department_id`, `pk`) against
`request.user_college_id` and returns `HttpResponseForbidden` on mismatch.

**Backward compatibility:** `_get_admin_college`, `_scope_departments`, and
`_scope_exams` in `_helpers.py` remain unchanged. New views use the mixin;
existing views continue using the helpers until migrated.

---

### Issue 4 — Email / Notifications

**New file: `students/signals.py`**

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

@receiver(post_save, sender=Notification)
def dispatch_notification_email(sender, instance, created, **kwargs):
    if not created:
        return
    if not instance.user.email:
        return
    send_mail(
        subject=instance.title,
        message=instance.message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[instance.user.email],
        fail_silently=True,
    )
    Notification.objects.filter(pk=instance.pk).update(is_read=False)
```

**`students/apps.py` change:**
```python
def ready(self):
    import students.signals  # noqa: F401
```

**`settings.py` — no code change required.** The env-var pattern is already
correct. Documentation of required env vars is already present in comments.
The fix is purely the signal wiring.

---

### Issue 5 — Data Model Additions

**`students/models.py` additions:**

```python
# New: Program model
class Program(models.Model):
    LEVEL_CHOICES = [
        ('UG', 'Undergraduate'),
        ('PG', 'Postgraduate'),
        ('DIPLOMA', 'Diploma'),
        ('PHD', 'Doctorate'),
    ]
    college = models.ForeignKey(College, on_delete=models.CASCADE,
                                related_name='programs')
    name    = models.CharField(max_length=100)   # e.g. "B.Tech", "M.Tech"
    code    = models.CharField(max_length=20)    # e.g. "BTECH", "MTECH"
    level   = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    duration_years = models.PositiveSmallIntegerField(default=4)

    class Meta:
        unique_together = ('college', 'code')

    def __str__(self):
        return f"{self.name} ({self.college.code})"
```

**`Student` model — additive FK:**
```python
program = models.ForeignKey(
    'Program', on_delete=models.SET_NULL,
    null=True, blank=True, related_name='students'
)
```

**`Exam` model — additive fields:**
```python
STATUS_CHOICES = [
    ('draft',     'Draft'),
    ('scheduled', 'Scheduled'),
    ('published', 'Published'),
]
status     = models.CharField(max_length=10, choices=STATUS_CHOICES,
                               default='draft')
department = models.ForeignKey('Department', on_delete=models.SET_NULL,
                                null=True, blank=True,
                                related_name='exams')
max_marks  = models.FloatField(null=True, blank=True)
```

**New: AcademicCalendar and Holiday models:**
```python
class AcademicCalendar(models.Model):
    college        = models.ForeignKey(College, on_delete=models.CASCADE,
                                       related_name='academic_calendars')
    semester_number = models.PositiveSmallIntegerField()
    academic_year  = models.CharField(max_length=9)   # e.g. "2024-2025"
    semester_start = models.DateField()
    semester_end   = models.DateField()

    class Meta:
        unique_together = ('college', 'semester_number', 'academic_year')

    @property
    def working_days(self):
        """Total weekdays (Mon–Sat) minus approved holidays."""
        from datetime import timedelta
        total = 0
        current = self.semester_start
        holiday_dates = set(
            self.holidays.values_list('date', flat=True)
        )
        while current <= self.semester_end:
            if current.weekday() < 6 and current not in holiday_dates:
                total += 1
            current += timedelta(days=1)
        return total

    def __str__(self):
        return f"{self.college.code} Sem {self.semester_number} {self.academic_year}"


class Holiday(models.Model):
    calendar    = models.ForeignKey(AcademicCalendar, on_delete=models.CASCADE,
                                    related_name='holidays')
    date        = models.DateField()
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('calendar', 'date')

    def __str__(self):
        return f"{self.date} — {self.description}"
```

**Migration strategy:** All new fields use `null=True, blank=True` or have
defaults, so the migration is non-destructive and requires no data backfill.

---

### Issue 6 — Attendance Rule Engine UI

**File: `templates/dashboards/student.html`**

**Change 1 — Sidebar link** (add after the `#attendance` link):
```html
<a href="#attendance-requests" data-section-target="attendance-requests"
   class="sb-link">
  <i class="fas fa-file-medical"></i> Attendance Requests
</a>
```

**Change 2 — New dashboard pane** (add after the `#attendance` section):
```html
<section data-dashboard-pane="attendance-requests" class="dashboard-pane">
  <div class="d-card">
    <div class="d-title">
      <i class="fas fa-file-medical"></i> Attendance Requests
    </div>
    <div class="section-meta">
      Submit exemption requests, corrections, or exam eligibility overrides.
    </div>
    <div class="action-row">
      <a href="{% url 'student_exemption_apply' %}"
         class="mini-btn mini-btn-teal">
        <i class="fas fa-file-medical"></i> Apply for Exemption
      </a>
      {% if upcoming_exams %}
        {% for exam in upcoming_exams %}
        <a href="{% url 'student_request_override' exam.pk %}"
           class="mini-btn mini-btn-deep">
          <i class="fas fa-shield-halved"></i>
          Request Override — {{ exam.name }}
        </a>
        {% endfor %}
      {% endif %}
    </div>
    <!-- Existing exemptions status table -->
    {% if exemption_requests %}
    <div class="table-scroll" style="margin-top:16px">
      <table class="dtable">
        <thead>
          <tr>
            <th>Type</th><th>Period</th><th>Status</th><th>Submitted</th>
          </tr>
        </thead>
        <tbody>
          {% for ex in exemption_requests %}
          <tr>
            <td>{{ ex.get_reason_type_display }}</td>
            <td>{{ ex.from_date|date:"d M" }} – {{ ex.to_date|date:"d M Y" }}</td>
            <td>
              <span class="dbadge
                {% if ex.status == 'APPROVED' %}dbadge-active
                {% elif ex.status == 'REJECTED' %}dbadge-red
                {% else %}dbadge-warning{% endif %}">
                {{ ex.status }}
              </span>
            </td>
            <td style="font-size:11px;color:var(--muted)">
              {{ ex.created_at|date:"d M Y" }}
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div class="empty" style="margin-top:12px">
      <i class="fas fa-inbox"></i> No exemption requests submitted yet.
    </div>
    {% endif %}
  </div>
</section>
```

**Change 3 — `student_dashboard` view** (`students/views/_legacy.py` or
`students/views/student.py` after split): add to context:
```python
'exemption_requests': AttendanceExemption.objects.filter(
    student=student
).order_by('-created_at')[:10],
'upcoming_exams': Exam.objects.filter(
    college=student.department.college,
    semester=student.current_semester,
    start_date__gte=timezone.now().date(),
).order_by('start_date')[:3],
```


---

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface
counterexamples that demonstrate each bug on the unfixed code, then verify
the fix works correctly and preserves existing behaviour.

---

### Exploratory Fault Condition Checking

**Goal**: Surface counterexamples that demonstrate each bug BEFORE implementing
the fix. Confirm or refute the root cause analysis.

**Test Plan**: Write tests that directly exercise each defective condition
against the unfixed codebase. Run these tests on UNFIXED code to observe
failures and understand the root cause.

**Test Cases:**

1. **Issue 1 — Line count check** (will fail on unfixed code):
   Assert `len(open('students/views/_legacy.py').readlines()) < 500`.
   Expected failure: file has 5200+ lines.

2. **Issue 2 — API endpoint availability** (will fail on unfixed code):
   `GET /api/v1/students/` — assert response status is 200 and
   `Content-Type` is `application/json`.
   Expected failure: 404 response.

3. **Issue 3 — Cross-college data leak** (will fail on unfixed code):
   Create two colleges, two admins. Log in as College A admin, request
   College B's student list. Assert response is 403.
   Expected failure: 200 response with College B's data.

4. **Issue 4 — Email dispatch on Notification creation** (will fail on unfixed code):
   Create a `Notification` record. Assert `len(mail.outbox) == 1` (using
   Django's `locmem` backend in tests).
   Expected failure: `mail.outbox` is empty.

5. **Issue 5 — Program FK on Student** (will fail on unfixed code):
   `Student.objects.filter(program__name='B.Tech')` — assert no `FieldError`.
   Expected failure: `FieldError: Cannot resolve keyword 'program'`.

6. **Issue 6 — Exemption link in dashboard** (will fail on unfixed code):
   Render `student_dashboard` and assert the attendance-requests section
   contains a link to `student_exemption_apply` outside the eligibility banner.
   Expected failure: link not found outside the conditional banner.

**Expected Counterexamples:**
- Issues 1–6 all produce clear, deterministic failures on unfixed code.
- No probabilistic or timing-dependent failures expected.

---

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed
system produces the expected behaviour.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := fixedSystem(input)
  ASSERT expectedBehavior(result)
END FOR
```

**Per-issue fix checks:**

- **Issue 1**: Each new domain module has < 500 lines. All URL names resolve.
  `from students.views import student_dashboard` succeeds.
- **Issue 2**: `GET /api/v1/students/` returns 200 JSON. `POST /api/v1/` with
  invalid data returns 400. Unauthenticated request returns 401.
- **Issue 3**: College A admin requesting College B resource returns 403.
  College A admin requesting College A resource returns 200.
- **Issue 4**: Creating a `Notification` triggers exactly one email to
  `notification.user.email` in `mail.outbox`.
- **Issue 5**: `Student.objects.filter(program__name='B.Tech')` returns a
  queryset. `Exam.objects.filter(status='draft')` returns a queryset.
  `AcademicCalendar.working_days` returns an integer.
- **Issue 6**: Student dashboard HTML contains a link to
  `student_exemption_apply` outside the eligibility banner.

---

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold,
the fixed system produces the same result as the original system.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalSystem(input) == fixedSystem(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation
checking because it generates many test cases automatically across the input
domain, catches edge cases that manual unit tests might miss, and provides
strong guarantees that behaviour is unchanged for all non-buggy inputs.

**Test Plan**: Observe behaviour on UNFIXED code first for all existing
workflows, then write property-based tests capturing that behaviour.

**Test Cases:**

1. **Role-based redirect preservation**: For any authenticated user with a
   valid role (1–7), `dashboard_redirect` must return the same URL before
   and after the refactor.
2. **Session timeout preservation**: For any request with an idle session
   exceeding 30 minutes, `SessionTimeoutMiddleware` must redirect to
   `/login/?timeout=1` — unchanged by any of the six fixes.
3. **Admin CRUD preservation**: For any valid POST to `admin_student_add`,
   `admin_faculty_add`, `admin_subject_add`, the response must be a redirect
   to the list view — unchanged after the views split.
4. **Attendance marking preservation**: For any valid POST to
   `faculty_mark_attendance`, an `AttendanceSession` and `Attendance` records
   must be created — unchanged after the views split.
5. **Exam controller preservation**: For any valid POST to `exam_results`,
   `ExamResult` records must be created and the response must redirect —
   unchanged after the views split.
6. **Student dashboard data preservation**: For any authenticated student,
   `student_dashboard` must return attendance data, marks, fee status, and
   quiz history — unchanged after adding the new attendance-requests pane.
7. **`Subject.unique_together` preservation**: Attempting to create two
   subjects with the same `(department, code)` must raise `IntegrityError` —
   unchanged after adding the `Program` model.

---

### Unit Tests

- Test each new domain view module imports cleanly and all functions are
  callable.
- Test `CollegeScopedMixin.get_queryset` filters by `college_id` for
  college-scoped users and returns all records for superusers.
- Test `dispatch_notification_email` signal sends exactly one email per
  `Notification` creation and zero emails on update.
- Test `Program.__str__`, `AcademicCalendar.working_days` (with and without
  holidays), `Holiday.__str__`.
- Test `Exam` with `status='draft'` saves and retrieves correctly.
- Test `Student` with `program=None` saves correctly (backward compatibility).
- Test student dashboard view context includes `exemption_requests` and
  `upcoming_exams` keys.

---

### Property-Based Tests

- **Property 1 (Fix)**: For any `Notification` created with a valid user
  email, exactly one email is dispatched. Generate random user/notification
  combinations.
- **Property 2 (Fix)**: For any college-scoped user and any queryset model
  with a `college` FK, `CollegeScopedMixin.get_queryset` returns only records
  where `college_id == request.user_college_id`. Generate random college
  assignments.
- **Property 7 (Preservation)**: For any valid student record (with or without
  `program`), `Student.objects.get(pk=student.pk)` succeeds. Generate random
  student records with and without program FK.
- **Property 7 (Preservation)**: For any `AcademicCalendar` with random
  `semester_start`, `semester_end`, and holiday set, `working_days` is always
  `>= 0` and `<= total_weekdays_in_range`.

---

### Integration Tests

- Full login → dashboard → attendance section → click "Apply for Exemption"
  → form submission → redirect back to dashboard with success message.
- Full login → dashboard → attendance section → click "Request Override" for
  an upcoming exam → form submission → `EligibilityOverride` record created.
- API: authenticate with token → `GET /api/v1/students/` → verify paginated
  JSON response scoped to the authenticated user's college.
- Views split: after moving `student_dashboard` to `views/student.py`, verify
  `reverse('student_dashboard')` still resolves and the view renders the
  full dashboard template without errors.
- Email: set `EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend` in
  test settings → create `Notification` → assert `mail.outbox[0].to` matches
  the notification user's email.