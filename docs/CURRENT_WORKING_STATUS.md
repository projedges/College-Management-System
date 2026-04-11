# EduTrack Current Working Status

Last updated: April 2026 — Phase 4 (Planner Flexibility + Model Hardening)

---

## 1. Core Working Model

- `Super Admin` works from a dedicated hidden workspace at `/superadmin1/`
- `Super Admin` creates colleges and college-admin accounts
- `College Admin` is scoped to one college and manages that college's records
- `Principal`, `HOD`, `Faculty`, and `Student` have separate dashboards
- Public `/register/` works only through a one-time invite link shared by college admin
- Student accounts are created by the college admin after review and conversion

---

## 2. What Changed In This Build (Phase 4)

### UI Fixes
- Removed duplicate "Today's Classes" table from timetable section — Full Week Timetable is the only timetable shown
- Removed duplicate college name label from sidebar (was showing twice)
- Fixed sidebar college name truncation — full name now displays
- Fixed mobile topbar — no longer shows EduTrack fallback logo, shows college name instead
- Fixed top padding on main content area (was cutting off page title)
- Fixed 420 corrupted byte sequences (BOMs, `&mdash;`, `&ndash;`, box-drawing chars) across 86 template files
- Subject names in student attendance table are now clickable links to subject detail page

### Subject Board (subject_board.html)
- Full FullCalendar attendance calendar per subject
- Month/year navigation with stats panel (rate, total, present, absent, late)
- Day-click popup showing time, status, faculty
- Sidebar matches full student dashboard sidebar

### Model Enhancements — Migrations 0034, 0035, 0036

**FacultyAvailability** — added `availability_type` (available/preferred/blocked), `valid_from`, `valid_to`, `priority_score` (1–10), `notes`

**Subject** — added `slot_type`, `slot_duration_mins`, `frequency_per_week`, `scheduling_constraint`

**Classroom** — added `room_type` (lecture/lab/seminar/tutorial/other), `features` (comma-separated)

**Timetable** — added `is_locked`, `elective_group` FK, `version` FK, `generation_mode`

**TimetableBreak** — added `break_type`, `applies_to`, `department` FK, `section`, `valid_from`, `valid_to`

**Section** — added `criteria` (auto/manual/merit_based/gender/specialization) + `auto_create_sections()` classmethod

**Student** — added `admission_type` (regular/lateral_entry/transfer), `entry_semester`

**New models:**
- `ElectiveGroup` — groups students who chose the same elective; has `sync_students()` method
- `StudentGroupConflict` — tracks (group_type, group_id, day, start_time) for student-level conflict detection
- `SchedulingConstraint` — per-college hard/soft constraint registry with weight (1–100)
- `TimetableVersion` — regular/exam/backup/draft versions with `activate()` method
- `PromotionRule` — per college/dept/semester promotion criteria
- `StudentSemesterHistory` — tracks promotion status, credits earned, backlogs per semester
- `LateralEntryProfile` — entry semester, previous qualification, bridge courses
- `AdmissionCycle` — year + round + name + dates
- `Admission` — student admission record with type, cycle, status, category
- `BacklogRegistration` — tracks re-registration for failed subjects with timetable slot link

### View / Form Fixes
- `admin_student_add` and `admin_student_edit` now save `admission_type` and `entry_semester`
- `admin_timetable_upload_csv` now parses `section` from CSV and sets `generation_mode='manual'`
- `add_classroom` action now reads and saves `room_type` and `features`
- Student form now shows all 6 status options (was missing Detained, Suspended, Transferred)
- Student form now has Admission Type and Entry Semester fields
- Classroom form in academic planner now has Room Type dropdown and Features input
- Classroom table now shows Type and Features columns

---

## 3. Public Portal Status

- Home page is public-facing and cleaner for demo use
- Super admin entry is not shown in the public UI
- Login page is the normal entry for existing users
- Register page is locked behind one-time invite links
- Public help desk is available for access issues and support escalation

---

## 4. Super Admin Features

- View colleges, create colleges, create college-admin accounts
- Broadcast platform-wide notices
- Enable/disable colleges

---

## 5. College Admin Features

- Guided dashboard with workflow-oriented sections
- Manage departments, students, faculty, HODs, subjects
- Manage fee records, announcements, exams
- Review student access requests, generate invite links
- Convert approved requests into student accounts
- Export filtered student data as CSV
- Semester planner: subjects, faculty assignment, availability, timetable generation
- Classroom management with room type and features
- Break management with type, scope, and date range
- Review and manage help desk tickets
- Export attendance, payment, and result PDF reports

---

## 6. Principal Features

- College-wide overview dashboard
- View departments, students, faculty, HODs, notices

---

## 7. HOD Features

- Department-specific dashboard
- Faculty list, student count, attendance overview
- Approval queue and history
- Substitution management

---

## 8. Faculty Features

- Faculty dashboard with dynamic sections
- Mark attendance (section-aware, time-locked)
- Enter marks, create assignments, review submissions
- Create and manage quizzes

---

## 9. Student Features

- Student dashboard with dynamic sections
- Profile edit page
- Attendance overview with course-wise % and predictor
- Subject detail page with FullCalendar attendance calendar
- Result viewing with SGPA/CGPA
- Result PDF download
- Assignment submission
- Fee payment flow with Razorpay
- Payment receipt PDF download
- Elective selection
- Quiz attempts
- Supply exam registration and payment
- Revaluation request and payment

---

## 10. Security, Reliability, and UX

- CSRF support improved for localhost and ngrok-style access
- Custom 400, 403, 404, and 500 pages
- Password reset flow
- Login attempt tracking and math CAPTCHA
- Session idle timeout (30 min) with warning modal
- Roll numbers auto-generated in `year-collegecode-branch-serial` format

---

## 11. Demo Data Available

- One demo college seeded (Annamacharya University)
- Demo users for all roles
- Attendance, marks, results, fees, timetable, announcements seeded
- Student profile data and assignments available

---

## 12. Current Gaps

- Timetable generator does not yet use the new flexibility fields (slot_type, scheduling_constraint, room_type matching, is_locked, SchedulingConstraint) — fields are in DB, generator wiring is next
- ElectiveGroup.sync_students() is not yet called automatically after admin confirms selections
- StudentGroupConflict table is not yet populated by the generator
- TimetableVersion is not yet surfaced in the planner UI
- PromotionRule / StudentSemesterHistory not yet wired into bulk_promote view
- LateralEntryProfile not yet shown in student profile UI
- AdmissionCycle / Admission not yet surfaced in admin UI
- BacklogRegistration not yet wired into supply exam flow
- Lab Staff still does not have a dedicated dashboard
- Automated tests still limited

---

## 13. Recommended Demo Flow

1. Show home page and controlled login/request entry
2. Show super admin creating college-level control
3. Show college-admin guided workspace
4. Show invite-link onboarding and request conversion
5. Show semester planner with classroom types and faculty availability
6. Show faculty attendance and assignment workflow
7. Show student dashboard, subject attendance calendar, results, payment, help desk
8. Show custom error pages and password reset briefly
