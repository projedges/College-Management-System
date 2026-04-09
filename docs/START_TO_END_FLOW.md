# EduTrack Start-to-End Flow

This document explains the full functional flow of the project from starting point to ending point.

Each start point is written separately so the system can be understood role by role.

---

## 1. System Entry Flow

### Start Point
- Home: `/`
- Login: `/login/`
- Register: `/register/`
- Help Desk: `/helpdesk/`
- Super Admin Login: `/sys/platform-access/`

### Flow
1. A user lands on the home page.
2. From there, the user chooses one of the available entry paths:
   - normal login
   - registration
   - public help desk
   - super admin platform login
3. Normal users log in through `/login/`.
4. The system checks credentials, role, and access status.
5. The `/dashboard/` redirect sends the user to the correct dashboard based on role.

### End Point
- The user reaches the correct working dashboard.
- Or the user submits a support ticket.
- Or the user finishes registration and can log in.

---

## 2. Super Admin Start-to-End Flow

### Start Point
- `/sys/platform-access/`

### Purpose
- Manage the platform itself.
- Create and control colleges.
- Create college admins.

### Flow
1. Super Admin logs in through the platform login page.
2. Super Admin enters the dashboard at `/superadmin1/`.
3. Super Admin creates a college at `/superadmin1/colleges/add/`.
4. Super Admin reviews the created college in `/superadmin1/colleges/<id>/`.
5. Super Admin edits college information if needed in `/superadmin1/colleges/<id>/edit/`.
6. Super Admin can enable or disable a college in `/superadmin1/colleges/<id>/toggle/`.
7. Super Admin creates the college admin in `/superadmin1/college-admins/add/`.
8. Super Admin can remove a college admin through `/superadmin1/college-admins/<id>/delete/`.
9. Super Admin publishes platform-wide notices at `/superadmin1/announcements/`.

### End Point
- A college exists on the platform.
- A college admin is ready to configure that college.
- Platform announcements are available to target users.

---

## 3. College Admin Start-to-End Flow

### Start Point
- Login: `/login/`
- Dashboard: `/dashboard/admin/`

### Purpose
- Build and operate the college inside the platform.

### Flow A: Core College Setup
1. College Admin logs in and reaches the admin dashboard.
2. Creates departments in `/dashboard/admin/departments/`.
3. Creates subjects in `/dashboard/admin/subjects/`.
4. Creates regulations in `/dashboard/admin/regulations/`.
5. Maps curriculum entries in `/dashboard/admin/regulations/<regulation_id>/curriculum/`.
6. Creates and manages sections in `/dashboard/admin/sections/`.
7. Maps subject-section-faculty records in `/dashboard/admin/ssf-map/`.
8. Uses `/dashboard/admin/academic-planner/` for timetable planning.

### Flow B: Staff and Student Setup
1. Adds faculty in `/dashboard/admin/faculty/` and `/dashboard/admin/faculty/add/`.
2. Adds HODs in `/dashboard/admin/hods/` and `/dashboard/admin/hods/add/`.
3. Adds students directly in `/dashboard/admin/students/add/`.
4. Sends invite-based onboarding links from `/dashboard/admin/student-invites/`.
5. Imports users in bulk through `/dashboard/admin/bulk-import/`.
6. Reviews registration requests in `/dashboard/admin/registration-requests/`.

### Flow C: Academic and Policy Setup
1. Configures attendance rules in `/dashboard/admin/attendance/rules/`.
2. Configures fees in `/dashboard/admin/fees/`.
3. Creates exams in `/dashboard/admin/exams/`.
4. Creates elective pools in `/dashboard/admin/electives/`.
5. Reviews elective selections in `/dashboard/admin/electives/<id>/selections/`.
6. Publishes announcements in `/dashboard/admin/announcements/`.

### Flow D: Operational Monitoring
1. Reviews help desk tickets in `/dashboard/admin/helpdesk/`.
2. Exports attendance through `/dashboard/admin/attendance/export/`.
3. Generates reports through `/dashboard/admin/reports/<report_type>/pdf/`.
4. Contacts platform support through `/dashboard/admin/contact-support/`.

### End Point
- College structure is ready.
- Staff and students are onboarded.
- Academic, fee, timetable, and attendance systems are active.
- The college is operational for daily use.

---

## 4. HOD Start-to-End Flow

### Start Point
- Login: `/login/`
- Dashboard: `/dashboard/hod/`

### Purpose
- Supervise a department.
- Review requests and attendance-related issues.

### Flow
1. HOD logs in and reaches the HOD dashboard.
2. Reviews department overview, faculty, students, and timetable.
3. Reviews pending approvals through `/dashboard/hod/approve/<id>/`.
4. Reviews leave decisions through `/dashboard/hod/leave/<id>/review/`.
5. Manages substitutions through `/dashboard/hod/substitutions/`.
6. Reviews student profiles through `/dashboard/hod/student/<id>/`.
7. Reviews faculty profiles through `/dashboard/hod/faculty/<id>/`.
8. Reviews exemption requests through `/dashboard/hod/exemptions/`.
9. Reviews attendance risk through `/dashboard/hod/defaulters/`.

### End Point
- Department requests are resolved.
- Exemptions are approved or rejected.
- Student and faculty issues are monitored.
- Department operations remain under control.

---

## 5. Faculty Start-to-End Flow

### Start Point
- Login: `/login/`
- Dashboard: `/dashboard/faculty/`

### Purpose
- Conduct classes and manage classroom academics.

### Flow A: Attendance Flow
1. Faculty logs in and opens the faculty dashboard.
2. Opens attendance for a subject in `/dashboard/faculty/attendance/<subject_id>/`.
3. Marks attendance for the class.
4. If needed, makes corrections in `/dashboard/attendance/correct/<attendance_id>/`.
5. Reviews defaulters in `/dashboard/faculty/attendance/<subject_id>/defaulters/`.

### Flow B: Marks Flow
1. Opens marks entry in `/dashboard/faculty/marks/<subject_id>/<exam_id>/`.
2. Enters examination marks.
3. Opens internal marks in `/dashboard/faculty/internal-marks/<subject_id>/`.
4. Saves internal assessment records.

### Flow C: Assignment and Quiz Flow
1. Creates assignments in `/dashboard/faculty/assignments/create/`.
2. Publishes assignments through `/dashboard/faculty/assignments/<id>/publish/`.
3. Reviews submissions through `/dashboard/faculty/submissions/<id>/review/`.
4. Creates quizzes through `/dashboard/faculty/quiz/create/`.
5. Edits quizzes through `/dashboard/faculty/quiz/<id>/edit/`.
6. Reviews quiz performance through `/dashboard/faculty/quiz/<id>/results/`.

### Flow D: Faculty Administration Flow
1. Submits requests through `/dashboard/faculty/requests/add/`.
2. Maintains lesson plans through `/dashboard/faculty/lesson-plans/<subject_id>/`.
3. Applies for leave through `/dashboard/faculty/leave/`.
4. Manages availability through:
   - `/dashboard/faculty/availability/add/`
   - `/dashboard/faculty/availability/<id>/delete/`

### End Point
- Attendance is recorded.
- Marks are stored.
- Assignments and quizzes reach students.
- Faculty requests move upward for approval.

---

## 6. Student Start-to-End Flow

### Start Point
- Login: `/login/`
- Dashboard: `/dashboard/student/`

### Purpose
- Use academic, fee, and support features as an enrolled student.

### Flow A: Onboarding and Profile
1. Student is created by admin or invited by registration flow.
2. Student registers through `/register/` when invite-based registration is used.
3. Student logs in and reaches `/dashboard/student/`.
4. Student updates personal information in `/dashboard/student/profile/edit/`.

### Flow B: Daily Academic Use
1. Student checks attendance, timetable, assignments, quizzes, notices, and results from the dashboard.
2. Student chooses electives in `/dashboard/student/electives/`.
3. Student submits assignments in `/dashboard/student/assignments/<id>/submit/`.
4. Student attempts quizzes in `/dashboard/student/quiz/<quiz_id>/attempt/`.
5. Student downloads the result PDF from `/dashboard/student/results/report/pdf/`.

### Flow C: Fee and Payment Flow
1. Student opens `/dashboard/student/fees/pay/`.
2. System creates payment orders in `/dashboard/student/fees/razorpay/create-order/`.
3. Payment verification runs in `/dashboard/student/fees/razorpay/verify/`.
4. Failed payments return through `/dashboard/student/fees/razorpay/failed/`.
5. Student downloads receipts from:
   - `/dashboard/student/payments/<id>/receipt/`
   - `/dashboard/student/payments/<id>/receipt/pdf/`

### Flow D: Special Request Flow
1. Student registers for supply exams in `/dashboard/student/supply-exam/register/`.
2. Student pays supply exam fees in `/dashboard/student/supply-exam/<reg_id>/pay/`.
3. Student requests revaluation in `/dashboard/student/revaluation/<marks_id>/`.
4. Student pays revaluation fee in `/dashboard/student/revaluation/<marks_id>/pay/`.
5. Student applies for attendance exemption in `/dashboard/student/exemption/`.
6. Student requests exam eligibility override in `/dashboard/student/exam/<exam_id>/override/`.

### Flow E: Support and Notifications
1. Student marks notifications as read in `/dashboard/student/notifications/mark-read/`.
2. Student raises issues through `/helpdesk/`.

### End Point
- Student completes academic tasks.
- Student completes payment tasks.
- Student raises requests where needed.
- Student receives results, receipts, and support updates.

---

## 7. Principal Start-to-End Flow

### Start Point
- Login: `/login/`
- Dashboard: `/dashboard/principal/`

### Purpose
- Monitor college performance in a read-only role.

### Flow
1. Principal logs in and reaches the principal dashboard.
2. Reviews overall student, faculty, fee, and announcement data.
3. Uses the dashboard only for observation and institutional monitoring.

### End Point
- Principal gets a complete high-level view of the college.

---

## 8. Lab Staff Start-to-End Flow

### Start Point
- Login: `/login/`
- Dashboard: `/dashboard/lab/`

### Purpose
- Support lab and classroom operational visibility.

### Flow
1. Lab Staff logs in and reaches the lab dashboard.
2. Reviews active sessions, classrooms, and schedule visibility.
3. Uses the dashboard to support lab-related day-to-day coordination.

### End Point
- Lab schedule awareness and room coordination are maintained.

---

## 9. Examination Department Start-to-End Flow

### Start Point
- Login: `/login/`
- Dashboard: `/dashboard/exam/`

### Purpose
- Run examination management from schedule to result publication.

### Flow A: Setup Flow
1. Exam staff logs in and reaches `/dashboard/exam/`.
2. Manages exam staff through `/dashboard/exam/staff/`.
3. Adds exam staff through `/dashboard/exam/staff/add/`.
4. Manages exam types through `/dashboard/exam/types/`.
5. Manages schemes through `/dashboard/exam/schemes/`.

### Flow B: Schedule and Valuation Flow
1. Opens exam schedule through `/dashboard/exam/<exam_id>/schedule/`.
2. Creates or updates schedule entries.
3. Deletes wrong schedule entries through `/dashboard/exam/<exam_id>/schedule/<id>/delete/`.
4. Creates valuation assignments through `/dashboard/exam/<exam_id>/valuation/`.

### Flow C: Eligibility and Hall Ticket Flow
1. Opens hall ticket processing through `/dashboard/exam/<exam_id>/hall-tickets/`.
2. Checks eligibility using attendance and related conditions.
3. Reviews overrides through `/dashboard/exam/<exam_id>/overrides/`.
4. Proceeds with hall ticket issue or withholding.

### Flow D: Marks and Result Flow
1. Opens marks overview through `/dashboard/exam/<exam_id>/marks/`.
2. Processes results through `/dashboard/exam/<exam_id>/results/`.
3. Reviews revaluation requests through `/dashboard/exam/revaluations/`.
4. Updates revaluation decisions through `/dashboard/exam/revaluations/<id>/update/`.

### End Point
- Exam schedules are ready.
- Hall tickets are controlled by eligibility.
- Results are processed and published.
- Revaluation requests are closed.

---

## 10. Public Help Desk Start-to-End Flow

### Start Point
- `/helpdesk/`

### Purpose
- Allow users or visitors to raise support issues.

### Flow
1. User opens the help desk form.
2. Fills in issue details and submits the ticket.
3. Ticket is stored in the system.
4. Admin reviews the ticket in `/dashboard/admin/helpdesk/`.
5. Ticket progress can be reviewed in `/dashboard/helpdesk/ticket/<id>/`.

### End Point
- Support request enters the internal review workflow.

---

## 11. Full Platform End-to-End Flow

This is the complete top-level system sequence.

1. Super Admin creates a college and its college admin.
2. College Admin configures departments, regulations, subjects, sections, staff, students, fees, and exams.
3. Faculty starts teaching operations and updates attendance, marks, assignments, and quizzes.
4. HOD monitors approvals, substitutions, exemptions, and department health.
5. Students use the system for academics, payments, assignments, quizzes, and requests.
6. Principal monitors institution-wide information.
7. Lab Staff monitors supporting schedules and room usage.
8. Examination Department runs exam scheduling, hall tickets, marks, results, and revaluation.
9. Help desk and announcements support the full platform during all stages.

### Final End Point
- The platform completes the full educational lifecycle:
  - college setup
  - academic management
  - attendance and evaluation
  - fee handling
  - exams and results
  - support workflow

---

## 12. Quick Start Map

| Role / Entry | Start URL | Final Outcome |
|---|---|---|
| Public User | `/` | Chooses login, register, or support path |
| Super Admin | `/sys/platform-access/` | Creates and controls colleges |
| College Admin | `/dashboard/admin/` | Makes the college operational |
| HOD | `/dashboard/hod/` | Supervises department workflow |
| Faculty | `/dashboard/faculty/` | Runs classroom and evaluation tasks |
| Student | `/dashboard/student/` | Uses academic and payment services |
| Principal | `/dashboard/principal/` | Monitors college performance |
| Lab Staff | `/dashboard/lab/` | Supports operational visibility |
| Exam Department | `/dashboard/exam/` | Runs exam lifecycle |
| Help Desk User | `/helpdesk/` | Creates support ticket |

