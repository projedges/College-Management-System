# EduTrack Future Enhancements

This file lists the next recommended improvements after the current internship delivery.
Each item includes what to replace or add, where it goes, and exactly how to do it.

---

## 1. Database — Migrate from SQLite3 to PostgreSQL

**Current state:** `db.sqlite3` — single file, no concurrent writes, no network access.

**When to do this:**
- Before deploying to any server where multiple processes run Django
- When more than one college is actively using the system simultaneously
- When you move to a cloud host (Railway, Render, AWS RDS, Supabase, etc.)

**What to change:**

`studentmanagementsystem/settings.py` — replace the DATABASES block:

```python
# Remove this:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Add this:
import os
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'edutrack'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

**Install the driver:**
```
pip install psycopg2-binary
```

**Migrate:**
```
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata seed_data  # if you have fixtures
```

**Nothing else changes** — models, views, templates, and URLs are all database-agnostic.

---

## 2. Move Secrets to Environment Variables

**Current state:** `SECRET_KEY`, `DB_PASSWORD`, `EMAIL_HOST_PASSWORD` are hardcoded in `settings.py`.

**What to add:**

Install `python-decouple`:
```
pip install python-decouple
```

Create a `.env` file at project root (add to `.gitignore`):
```
SECRET_KEY=your-real-secret-key-here
DEBUG=False
DB_NAME=edutrack
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=yourapppassword
```

Update `settings.py` top:
```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
```

---

## 3. Real Email Delivery for Password Reset and Notifications

**Current state:** `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` — emails print to terminal only.

**What to change in `settings.py`:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER')
```

**For Gmail:** create an App Password at myaccount.google.com → Security → App Passwords.
**For production:** use SendGrid, Mailgun, or AWS SES instead of Gmail.

---

## 4. Controlled Onboarding Improvements

- Add document upload and verification to the student access request flow
- Add college-admin approval notes and internal review comments
- Add request priority, follow-up status, and audit trail for each applicant
- Add bulk approval, rejection, and conversion for student requests
- Add email notifications when a request moves from submitted to approved or rejected
- Add invite resend, expiry extension, and invite revocation controls

---

## 5. College Admin Productivity

- Add batch semester promotion and status update tools
- Add a smoother custom UI for subject allocation and faculty-subject mapping
- Add dashboard filters for department, semester, activity date, and fee state
- Add downloadable CSV/Excel bundles for attendance, fee, and subject allocation views

---

## 6. Role Workflow Completion

- Add faculty-side approval request submission for leave, events, and academic requests (UI exists, needs HOD notification)
- Replace principal creation/editing through Django admin with a full custom workflow
- Add more college-admin controls for principal-level delegation and review
- Expand help desk with assignee ownership, comments, and response timeline

---

## 7. Academic Growth

- Expand assignments into a full lifecycle with comments, rubrics, and multiple file support
- Add result publishing controls with review checkpoints before students can see results
- Add course-wise and semester-wise report cards
- Wire new timetable flexibility fields into `_auto_generate_timetable`:
  - Respect `Subject.slot_type` and `slot_duration_mins` when picking slots
  - Match `Classroom.room_type` to `Subject.slot_type` (lab subject → lab room)
  - Respect `Subject.scheduling_constraint` (prefer_morning, no_consecutive, etc.)
  - Skip `Timetable` entries where `is_locked=True`
  - Read `SchedulingConstraint` table for hard/soft priority
  - Populate `StudentGroupConflict` after generation
- Wire `ElectiveGroup.sync_students()` call after admin confirms elective selections
- Surface `TimetableVersion` in the planner UI (create version, activate, switch)
- Wire `PromotionRule` and `StudentSemesterHistory` into the bulk promote view
- Add `LateralEntryProfile` display in student profile UI
- Surface `AdmissionCycle` and `Admission` in admin UI
- Wire `BacklogRegistration` into the supply exam registration flow

---

## 8. Student Experience

- Add profile completeness tracking and document upload support
- Add fee reminders and a clearer payment history timeline
- Add consolidated downloadable student profile and semester report card PDFs
- Add better mobile quick actions for assignments, fees, and receipts

---

## 9. Reporting and Analytics

- Improve PDF layout quality with signatures, branding, and visual summaries (current PDF uses raw PostScript — consider `reportlab` or `weasyprint`)
- Add report filters by department, semester, date range, and fee status
- Add analytics for attendance risk, fee recovery, and result trends
- Add CSV and Excel export alongside PDF

---

## 10. Security and Reliability

- Expand automated tests for routing, forms, request conversion, and dashboard flows
- Add stronger login protection — temporary lockout after N failed attempts (model exists: `UserSecurity.login_attempts`, just needs the lockout check in `login_view`)
- Add production HTTPS settings (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`) — currently suppressed because `DEBUG=True`

---

## 11. Scalability

- Make `department.code` and `subject.code` college-scoped (currently globally unique — two colleges can't have a CSE department)
- Add separate branding, settings, and report templates per college
- Add archive or soft-delete workflows instead of only hard delete behavior
- Add pagination to student/faculty list pages — currently loads all records into memory

---

## Suggested Next Milestone

If this project continues after the internship, the strongest next milestone is:

1. Move secrets to `.env` (30 minutes, zero risk)
2. Switch to PostgreSQL on a free-tier host like Supabase or Railway (1–2 hours)
3. Enable real email delivery for password reset (1 hour)
4. Wire `_check_timetable_conflict()` into auto-generation (30 minutes)
5. Add login lockout using the existing `UserSecurity` model (1 hour)

That milestone makes the system production-ready without rewriting anything.
