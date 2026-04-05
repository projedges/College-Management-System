# Bugfix Requirements Document

## Introduction

This document captures the six Tier 1 architectural defects in the Django-based
Student Management System (EduTrack). These issues range from structural problems
(a 5200+ line monolithic views file, no REST API) to data integrity risks
(multi-tenancy not enforced at the framework level), broken external integrations
(email always printing to console), data model gaps (no Program model,
globally-scoped subject codes, incomplete Exam model, no AcademicCalendar), and
an incomplete attendance rule engine UI. Left unaddressed, these defects block
mobile/API integrations, create cross-college data leakage risk, prevent any
email from reaching users, and make the codebase unmaintainable.

---

## Bug Analysis

### Current Behavior (Defect)

**Issue 1 — Monolithic Views File**

1.1 WHEN any developer opens `students/views/_legacy.py` THEN the system presents
a single 5200+ line file containing 130+ functions covering authentication,
dashboards, admin, faculty, student, exam, attendance, fees, and quiz domains
with no separation of concerns.

1.2 WHEN a new view needs to be added to any domain THEN the system requires
editing the single monolithic file, causing merge conflicts and making feature
isolation impossible.

**Issue 2 — No REST API**

1.3 WHEN a mobile application or third-party service attempts to consume
application data THEN the system returns only server-rendered HTML with no JSON
endpoints available.

1.4 WHEN `students/urls.py` is inspected THEN the system exposes zero API routes
— there is no `/api/` prefix, no DRF ViewSets, and no serializers anywhere in
the codebase.

**Issue 3 — Multi-tenancy Not Enforced at Framework Level**

1.5 WHEN a view function queries students, departments, exams, or fees THEN the
system relies on each individual view manually calling `_get_admin_college` or
`_scope_departments` — there is no automatic enforcement layer.

1.6 WHEN `CollegeScopeMiddleware.process_view` is called THEN the system returns
`None` unconditionally, performing no cross-college access check and providing
no actual enforcement.

1.7 WHEN a developer writes a new view and omits the college filter THEN the
system silently returns data from all colleges, exposing College A's records to
College B's admin.

**Issue 4 — Email / Notifications Broken**

1.8 WHEN `EMAIL_BACKEND` is not overridden via environment variable THEN the
system defaults to `django.core.mail.backends.console.EmailBackend`, printing
all emails to the terminal instead of delivering them.

1.9 WHEN a password reset email, low-attendance alert, or fee reminder is
triggered THEN the system writes the email body to stdout and no message reaches
the recipient's inbox.

1.10 WHEN a `Notification` record is created in the database THEN the system
stores it but has no delivery mechanism — no signal, no task queue, and no
push/email dispatch is wired to the `Notification` model.

**Issue 5 — Data Model Gaps**

1.11 WHEN a student is enrolled in B.Tech CSE and another in M.Tech CSE THEN the
system stores both with only a `department` FK on `Student`, making the two
programs indistinguishable at the data level.

1.12 WHEN two departments attempt to create a subject with the same code THEN the
system raises an `IntegrityError` because `Subject` has no program-level scoping,
and the existing `unique_together ('department', 'code')` constraint does not
account for program differentiation.

1.13 WHEN an `Exam` record is created THEN the system stores only `name`,
`semester`, `start_date`, `end_date`, and `created_by` — there is no `status`
field (draft/scheduled/published), no `department` FK, and no `max_marks` at
the exam level.

1.14 WHEN an admin needs to track semester start/end dates, holidays, or working
days THEN the system has no `AcademicCalendar` model and no mechanism to record
or query this information.

**Issue 6 — Attendance Rule Engine UI Incomplete**

1.15 WHEN a student navigates to their dashboard THEN the system shows no UI
element to submit an attendance exemption request, despite
`student_exemption_apply` view and the exemption model existing in the backend.

1.16 WHEN a student attempts to request an attendance correction or exam
eligibility override THEN the system provides no accessible form or link on the
student dashboard to initiate these workflows.

---

### Expected Behavior (Correct)

**Issue 1 — Monolithic Views File**

2.1 WHEN any developer opens the views directory THEN the system SHALL present
domain-separated modules (e.g., `views/auth.py`, `views/student.py`,
`views/faculty.py`, `views/admin_panel.py`, `views/exam.py`,
`views/attendance.py`) each under 500 lines.

2.2 WHEN a new view needs to be added to a domain THEN the system SHALL allow
editing only the relevant domain module without touching unrelated code.

**Issue 2 — No REST API**

2.3 WHEN a mobile application or third-party service sends a request to `/api/`
THEN the system SHALL return JSON responses via Django REST Framework ViewSets
with token or session authentication.

2.4 WHEN the URL configuration is inspected THEN the system SHALL expose a
versioned `/api/v1/` prefix with routers for at minimum students, attendance,
marks, and fees resources.

**Issue 3 — Multi-tenancy Not Enforced at Framework Level**

2.5 WHEN any authenticated college-scoped user makes a request THEN the system
SHALL automatically scope all querysets to that user's college via a reusable
decorator or mixin, without requiring each view to call a manual scoping helper.

2.6 WHEN a `CollegeScopedMixin` or equivalent decorator is active THEN the system
SHALL raise `PermissionDenied` (HTTP 403) if a college-scoped user attempts to
access a resource belonging to a different college.

2.7 WHEN a developer writes a new view using the provided mixin/decorator THEN
the system SHALL enforce the college filter automatically, making cross-college
data leakage impossible by default.

**Issue 4 — Email / Notifications Broken**

2.8 WHEN `EMAIL_BACKEND` is set to SMTP via environment variable THEN the system
SHALL deliver password reset, low-attendance alert, and fee reminder emails to
recipients' inboxes.

2.9 WHEN a `Notification` record is created THEN the system SHALL dispatch the
notification via at least one delivery channel (email or in-app) using Django
signals or a task queue integration.

2.10 WHEN the application runs in development THEN the system SHALL default to
console backend, and settings SHALL clearly document the environment variables
required to switch to SMTP.

**Issue 5 — Data Model Gaps**

2.11 WHEN a student is enrolled THEN the system SHALL link the student to a
`Program` model (e.g., B.Tech, M.Tech, Diploma) in addition to a `Department`,
making program-level distinctions queryable.

2.12 WHEN two departments create subjects with the same code THEN the system
SHALL allow it, with uniqueness enforced only within `(department, code)`, and
subject scoping SHALL optionally extend to `(program, department, code)`.

2.13 WHEN an `Exam` record is created THEN the system SHALL require a `status`
field with choices `draft`, `scheduled`, `published`; a `department` FK; and a
`max_marks` field at the exam level.

2.14 WHEN an admin manages the academic calendar THEN the system SHALL provide an
`AcademicCalendar` model with `semester_start`, `semester_end`, a related
`Holiday` set, and a `working_days` property derivable from those dates.

**Issue 6 — Attendance Rule Engine UI Incomplete**

2.15 WHEN a student views their dashboard THEN the system SHALL display a clearly
accessible link or button to submit an attendance exemption request that posts
to `student_exemption_apply`.

2.16 WHEN a student needs to request an attendance correction or exam eligibility
override THEN the system SHALL provide the corresponding forms on the student
dashboard, wired to the existing backend views.

---

### Unchanged Behavior (Regression Prevention)

3.1 WHEN an authenticated user logs in with valid credentials THEN the system
SHALL CONTINUE TO redirect them to the correct role-based dashboard (student,
faculty, HOD, admin, principal, exam controller, lab staff).

3.2 WHEN `SessionTimeoutMiddleware` is active THEN the system SHALL CONTINUE TO
enforce the 30-minute idle timeout and display the countdown warning modal.

3.3 WHEN a college admin manages students, faculty, departments, subjects, fees,
and announcements THEN the system SHALL CONTINUE TO support all existing CRUD
operations through the admin panel.

3.4 WHEN a faculty member marks attendance for a subject THEN the system SHALL
CONTINUE TO record `AttendanceSession` and `Attendance` records correctly.

3.5 WHEN an exam controller manages exams, hall tickets, marks, and revaluations
THEN the system SHALL CONTINUE TO support all existing exam controller workflows.

3.6 WHEN a student views their dashboard THEN the system SHALL CONTINUE TO
display attendance percentage, marks, fee status, assignments, quiz attempts,
and notifications.

3.7 WHEN the super admin manages colleges and college admins THEN the system
SHALL CONTINUE TO support all existing super admin operations.

3.8 WHEN a user submits a helpdesk ticket THEN the system SHALL CONTINUE TO
create the ticket and allow admin/HOD to respond via ticket comments.

3.9 WHEN the attendance rule engine evaluates a student's eligibility THEN the
system SHALL CONTINUE TO apply the configured minimum attendance percentage and
produce the correct eligible/ineligible result.

3.10 WHEN existing HTML templates render dashboards, forms, and reports THEN the
system SHALL CONTINUE TO serve them correctly — the refactor SHALL NOT break any
existing template rendering.
