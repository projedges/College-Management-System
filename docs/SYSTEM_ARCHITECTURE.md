# EduTrack — System Architecture & Complete Workflow

## Overview

EduTrack is a full-stack College Management ERP built on Django. It covers the complete lifecycle of a college — from student onboarding to result publication — across multiple roles, with configurable rules and exception handling at every layer.

**Tech Stack:** Django 5.1 · SQLite (dev) / MySQL (prod) · Razorpay · ReportLab PDF · Bootstrap-free custom CSS

---

## Role Hierarchy

| Role | Access Level |
|---|---|
| Super Admin | Platform-level — manages colleges |
| College Admin | College-level — manages everything within their college |
| Principal | Read-only overview of college performance |
| HOD | Department-level — approvals, attendance oversight, substitutions |
| Faculty | Subject-level — attendance, marks, assignments, quizzes |
| Exam Controller | Exam department — schedules, hall tickets, results, revaluation |
| Student | Self-service — dashboard, fees, electives, assignments, quizzes |
| Lab Staff | Lab room monitoring |

---

## Layer 1 — Core Structure (Fixed)

### 1.1 College & Department Setup
- Super Admin creates a College with a unique code, logo, and ID generation rules
- College Admin creates Departments with section capacity
- Each college has its own branding (colors, tagline, sidebar theme)

### 1.2 User Management
- All users have a `UserRole` linking them to a college and role
- Passwords are hashed (Argon2 primary, PBKDF2 fallback)
- Login has math CAPTCHA + 5-attempt lockout (15-minute window)
- Session idle timeout (30 min) with warning modal

### 1.3 Student Onboarding
```
Admin sends invite link (RegistrationInvite)
    ↓
Student fills registration form (RegistrationRequest)
    ↓
Admin reviews: SUBMITTED → UNDER_REVIEW → APPROVED → CONVERTED
    ↓
Student account created with auto-generated roll number
    ↓
Default fee record created for current semester
    ↓
Section auto-assigned based on department capacity
```

### 1.4 Faculty Onboarding
- Admin adds faculty manually or via CSV bulk import
- Employee ID auto-generated from college rule
- Faculty assigned to department; cross-department teaching supported

---

## Layer 2 — Configurable System

### 2.1 Academic Regulations
**Model:** `Regulation`
- Admin defines a university scheme (e.g. "VTU 2021", "Anna Univ R2019")
- Linked to an admission year batch
- All curriculum entries and evaluation schemes tie to a regulation

### 2.2 Curriculum Mapping
**Model:** `CurriculumEntry`
- Maps subjects into a regulation's curriculum per department per semester
- Each subject tagged as: Fixed / Program Elective (PE) / Open Elective (OE)
- Prerequisites can be set per subject

### 2.3 Subjects
**Model:** `Subject`
- L-T-P-C format (Lecture, Tutorial, Practical, Credits)
- Categories: PC, PE, OE, BS, MC, PW, AC, HS, ES
- Unique per department+code

### 2.4 Evaluation Scheme
**Model:** `EvaluationScheme`
- CIE: count, best-of logic, max per test, total contribution
- SEE: max marks, scaled contribution, passing minimum
- Practical/Viva: optional internal + external components
- Grading: Absolute / Relative / Credit-based
- **Grace Marks:** `GraceMarksRule` — configurable per scheme (max per subject, total cap, approval required)

### 2.5 Attendance Rules
**Model:** `AttendanceRule`
- Per college / department / semester (most specific wins)
- Configurable: min overall %, min per-subject %, grace condonation %
- Alert thresholds (warn at X%, critical at Y%)
- Exemption types: Medical, Sports, OD — with max days cap

### 2.6 Fee Structure
**Model:** `FeeStructure` + `FeeBreakdown`
- Per college / department / semester
- Categories: Tuition, Exam, Lab, Library, Sports, Misc, Supply, Reval
- **Installment Plans:** `FeeInstallmentPlan` + `FeeInstallment` — split fee into N installments with due dates
- **Late Fee:** `LateFeeRule` — Rs/day penalty after grace period, with cap
- **Waivers:** `FeeWaiver` — merit/need/sports/management discretion

### 2.7 Timetable Configuration
**Models:** `TimetableBreak` · `TimetableVersion` · `SchedulingConstraint`

- Named breaks (Lunch, Tea, Exam, Event, Holiday) per college — college-wide, department, or section scope
- Break date range support (`valid_from`, `valid_to`) for temporary breaks (fests, exams)
- Working days: Mon–Sat
- **TimetableVersion** — multiple parallel timetables (regular/exam/backup/draft), one active per type, `activate()` auto-deactivates others
- **SchedulingConstraint** — per-college hard/soft constraint registry with weight (1–100); hard = must satisfy, soft = preference for optimizer

### 2.8 Classroom Configuration
**Model:** `Classroom`

- `room_type`: lecture / lab / seminar / tutorial / other — used by generator to match subject slot type
- `features`: comma-separated list (projector, computers, ac, smartboard)
- `features_list()` helper method for template use

### 2.9 Subject Scheduling Patterns
**Model:** `Subject` (extended)

- `slot_type`: lecture / lab / tutorial / seminar
- `slot_duration_mins`: duration per slot (60 for lecture, 120 for lab)
- `frequency_per_week`: how many times per week
- `scheduling_constraint`: no_consecutive / prefer_morning / prefer_afternoon / continuous_block / alternate_days

### 2.10 Faculty Availability (Extended)
**Model:** `FacultyAvailability`

- `availability_type`: available / preferred / blocked
- `valid_from` / `valid_to`: for temporary slots (leave periods, exam weeks)
- `priority_score` (1–10): generator prefers higher scores when multiple slots are valid
- `notes`: free text (e.g. "Can take labs only")

---

## Layer 3 — Exception System

### 3.1 Attendance Exceptions
- `AttendanceExemption` — student applies, HOD approves/rejects
- `AttendanceCorrection` — faculty/HOD corrects a record with reason (full audit trail)
- `EligibilityOverride` — exam cell manually overrides ineligibility

### 3.2 Marks Exceptions
- `RevaluationRequest` — student pays fee → exam controller reviews → marks updated → SGPA recalculated
- `GraceMarksApplication` — exam controller applies grace marks with approval trail

### 3.3 Timetable Exceptions
- `Substitution` — HOD assigns substitute faculty for a specific date
- `LeaveApplication` — faculty applies, HOD approves/rejects with notification

### 3.4 Fee Exceptions
- `FeeWaiver` — admin grants partial/full waiver with reason
- Manual payment fallback when Razorpay not configured

---

## Complete Workflow — Semester Lifecycle

### Phase 1: Academic Setup
```
College Admin
    → Create Regulation (e.g. ANU2021)
    → Add Subjects (with L-T-P-C)
    → Map Curriculum (Regulation → Dept → Sem → Subjects, mark Fixed/PE/OE)
    → Configure EvaluationScheme (CIE/SEE weightage)
    → Configure AttendanceRule (75% default, configurable)
    → Configure FeeStructure (category-wise amounts)
```

### Phase 2: Student Intake
```
Admin sends invite links
    → Students register (RegistrationRequest)
    → Admin reviews and approves
    → Student accounts created with roll numbers
    → Sections auto-generated (based on section_capacity)
    → Students assigned to sections in roll-number order
    → Default fee records created
```

### Phase 3: Elective Selection
```
Admin creates ElectivePool (PE-1, OE-1)
    → Sets subjects in pool, min/max seats, deadline
    → Opens pool (status: OPEN)
    ↓
Student selects elective from open pools
    → Status: PENDING
    ↓
Admin confirms/rejects selections
    → Status: CONFIRMED / REJECTED
    → Quota enforced (max seats per subject)
    → Min students check (below min → subject may be cancelled)
```

### Phase 4: Faculty Assignment & Timetable
```
Admin assigns faculty to subjects (FacultySubject)
    → Multiple faculty per subject = parallel sections
    ↓
Admin creates Sections (or auto-generates from student count)
    ↓
Admin creates SSF Mapping (Subject + Section + Faculty + Classroom)
    → This is the core mapping table
    ↓
Admin generates timetable (auto or CSV upload)
    → Conflict detection: faculty can't be in 2 places, rooms can't double-book
    → College-wide conflict check
    → Lab subjects get 2 consecutive 50-min slots
    → Free slots shown in faculty timetable
    ↓
Faculty sets availability slots (free periods)
    → Used by admin for scheduling and substitutions
```

### Phase 5: Teaching & Attendance
```
Faculty marks attendance (faculty_mark_attendance)
    → Time-locked: within class time + 10 min grace + 60 min edit window
    → AttendanceSession auto-created on first mark
    → Section-aware (each section tracked separately)
    ↓
System calculates per-student attendance %
    → Alerts sent when below threshold
    → Eligibility computed using AttendanceRule
    ↓
Student views attendance dashboard
    → Course-wise % with progress bars
    → Predictor: "Can miss X more" or "Need Y more classes"
    → Calendar view: full log by date with faculty name
    → Today/Yesterday filter
    ↓
Exceptions:
    Student applies exemption → HOD approves
    Faculty corrects attendance → AuditLog created
    Exam cell overrides eligibility → EligibilityOverride
```

### Phase 6: Internal Marks
```
Faculty enters internal marks (faculty_internal_marks)
    → IA1 (0-30), IA2 (0-30), Assignment (0-20), Attendance (0-5)
    → Total: max 85 marks
    ↓
Faculty enters external marks (faculty_enter_marks)
    → Per subject per exam
    → Grade auto-calculated: O/A+/A/B+/B/C/F
    → Grade point stored: 10/9/8/7/6/5/0
    → AuditLog: MARKS_ENTERED / MARKS_UPDATED
```

### Phase 7: Exam Management
```
Exam Controller creates Exam
    → Sets semester, start/end dates
    ↓
Creates ExamSchedule (per subject)
    → Date, time, venue, invigilator, max/passing marks
    ↓
Generates Hall Tickets
    → Checks attendance eligibility (AttendanceRule)
    → Checks fee dues
    → Status: ISSUED / DETAINED / WITHHELD
    → Override: EligibilityOverride
    ↓
Marks entry (faculty or exam staff)
    → Marks.objects.update_or_create per student per subject
    ↓
Result computation (exam_results)
    → Compute: total marks, percentage, grade, SGPA
    → SGPA = Σ(credit × grade_point) / Σ(credits)
    → Verify → Publish
    → Student notified
    ↓
Student views results
    → Subject-wise table: marks, grade, credits
    → SGPA per semester, CGPA overall
    → PDF download (ReportLab)
```

### Phase 8: Revaluation & Supply Exam
```
Revaluation:
    Student requests revaluation (after result published)
        → Pays fee via Razorpay
        → RevaluationRequest created (PENDING)
        ↓
    Exam Controller reviews
        → Accepts: revised marks entered → grade recalculated → SGPA updated → AuditLog: MARKS_REVAL
        → Rejects: status = REJECTED

Supply Exam (Backlog):
    Student selects failed subjects
        → Pays supply fee (Rs/subject, configurable)
        → SupplyExamRegistration created
        ↓
    Exam conducted separately
    Marks entered as new exam
```

### Phase 9: Fee Management
```
Fee record created at student onboarding
    → total_amount from FeeStructure
    ↓
Student pays via Razorpay
    → Fee components: Tuition (partial allowed), Exam (fixed), Library (editable + reason), Sports, Misc (custom + desc)
    → Supply exam fee and Reval fee handled separately
    → Payment verified server-side (HMAC signature)
    → AuditLog: FEE_PAYMENT
    → Email to student + admin on success
    ↓
Admin can:
    → Create installment plan (FeeInstallmentPlan)
    → Grant waiver (FeeWaiver)
    → Configure late fee penalty (LateFeeRule)
    ↓
Student downloads receipt (PDF, ReportLab)
```

---

## Audit & Logging System

### AuditLog (unified)
Every critical action creates an `AuditLog` record:

| Action | Trigger |
|---|---|
| MARKS_ENTERED | Faculty enters marks for first time |
| MARKS_UPDATED | Faculty updates existing marks |
| MARKS_REVAL | Exam controller accepts revaluation |
| ATT_CORRECTED | Faculty/HOD corrects attendance |
| ATT_EXEMPTION | HOD approves exemption |
| ATT_OVERRIDE | Exam cell overrides eligibility |
| FEE_PAYMENT | Razorpay payment verified |
| FEE_WAIVER | Admin grants waiver |
| FEE_PENALTY | Late fee penalty added |
| ELECTIVE_SELECTED | Student selects elective |
| ELECTIVE_CHANGED | Admin changes student's elective |
| TT_GENERATED | Timetable auto-generated |
| TT_SUBSTITUTION | HOD assigns substitution |
| RESULT_PUBLISHED | Exam controller publishes results |

Each log stores: action type, performed_by, student/faculty/college FK, description, old_value, new_value, IP address, timestamp.

### ActivityLog (legacy)
Login/logout events per user.

---

## Key URLs Reference

| Area | URL |
|---|---|
| Login | `/login/` |
| Admin Dashboard | `/dashboard/admin/` |
| Regulations | `/dashboard/admin/regulations/` |
| Curriculum | `/dashboard/admin/regulations/<id>/curriculum/` |
| Sections | `/dashboard/admin/sections/` |
| SSF Mapping | `/dashboard/admin/ssf-map/` |
| Academic Planner | `/dashboard/admin/academic-planner/` |
| Elective Pools | `/dashboard/admin/electives/` |
| Student Electives | `/dashboard/student/electives/` |
| Fee Payment | `/dashboard/student/fees/pay/` |
| Exam Dashboard | `/dashboard/exam/` |
| Exam Results | `/dashboard/exam/<id>/results/` |
| HOD Dashboard | `/dashboard/hod/` |
| HOD Faculty Profile | `/dashboard/hod/faculty/<pk>/` |
| Faculty Dashboard | `/dashboard/faculty/` |
| Faculty Availability | `/dashboard/faculty/availability/add/` |
| Student Dashboard | `/dashboard/student/` |
| Supply Exam | `/dashboard/student/supply-exam/register/` |
| Revaluation | `/dashboard/student/revaluation/<marks_id>/` |

---

## Database Models Summary

### Core
`College` · `Department` · `Student` · `Faculty` · `HOD` · `Principal` · `UserRole` · `Section`

### Academic
`Regulation` · `CurriculumEntry` · `Subject` · `FacultySubject` · `SectionSubjectFacultyMap`

### Timetable
`Timetable` · `TimetableBreak` · `Classroom` · `FacultyAvailability` · `Substitution` · `TimetableVersion` · `SchedulingConstraint`

### Attendance
`AttendanceSession` · `Attendance` · `AttendanceRule` · `AttendanceExemption` · `AttendanceCorrection` · `EligibilityOverride`

### Electives
`ElectivePool` · `ElectiveSelection` · `ElectiveGroup` · `StudentGroupConflict`

### Exam & Results
`Exam` · `ExamType` · `ExamSchedule` · `HallTicket` · `Marks` · `InternalMark` · `Result` · `ExamResult` · `RevaluationRequest` · `SupplyExamRegistration` · `EvaluationScheme` · `GraceMarksRule` · `GraceMarksApplication`

### Fees
`Fee` · `FeeStructure` · `FeeBreakdown` · `Payment` · `FeeInstallmentPlan` · `FeeInstallment` · `LateFeeRule` · `FeeWaiver`

### Student Lifecycle
`PromotionRule` · `StudentSemesterHistory` · `LateralEntryProfile` · `AdmissionCycle` · `Admission` · `BacklogRegistration`

### Communication
`Announcement` · `Notification` · `HelpDeskTicket` · `TicketComment`

### Audit
`AuditLog` · `ActivityLog` · `AttendanceCorrection` · `ExamStaffLog`

### Other
`Assignment` · `AssignmentSubmission` · `Quiz` · `QuizQuestion` · `QuizOption` · `QuizAttempt` · `QuizAnswer` · `LessonPlan` · `LeaveApplication` · `CollegeBranding` · `RegistrationRequest` · `RegistrationInvite`

---

## Demo Credentials (seed_full_demo)

```
Super Admin  : admin / (Django superuser)
College Admin: anu_admin     / ANU@Admin2026
HOD (ISE)    : anu_hod_ise   / ANU@HOD2026
Faculty (ML) : fac_ml        / Faculty@123
Student Sec A: ise5_a01      / Student@123
Student Sec B: ise5_b01      / Student@123
```

Run `python manage.py seed_annamacharya` then `python manage.py seed_full_demo` to populate demo data.
