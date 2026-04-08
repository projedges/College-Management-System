# EduTrack — Complete System Workflow

## Platform Roles

| Role | Access |
|---|---|
| Super Admin | Manages colleges on the platform |
| College Admin | Manages everything within their college |
| HOD | Department-level oversight, approvals |
| Faculty | Marks attendance, enters marks, manages assignments |
| Student | Views dashboard, pays fees, selects electives, submits assignments |
| Principal | Read-only overview of college performance |
| Exam Controller | Manages exams, hall tickets, results, revaluation |

---

## Phase 1 — College Setup (Super Admin)

1. Super Admin logs in at `/sys/platform-access/`
2. Creates a College (name, code, city, logo)
3. Creates a College Admin user for that college
4. College is now active and ready

---

## Phase 2 — Academic Structure (College Admin)

### 2.1 Departments
`/dashboard/admin/departments/`
- Add departments (CSE, ISE, ECE, MECH…)
- Set `section_capacity` (default 60 students per section)

### 2.2 Regulations
`/dashboard/admin/regulations/`
- Define the university scheme (e.g. "VTU 2021 Scheme", "Anna Univ R2019")
- Set `effective_from_year` — which admission batch this applies to
- Each college can have multiple regulations for different batches

### 2.3 Subjects
`/dashboard/admin/subjects/`
- Add subjects per department per semester
- Fields: Name, Code, L-T-P-C (Lecture-Tutorial-Practical-Credits), Category
- Categories: PC (Program Core), PE (Program Elective), OE (Open Elective), BS, MC, HS, ES, PW, AC

### 2.4 Curriculum Mapping
`/dashboard/admin/regulations/<id>/curriculum/`
- Map subjects into the regulation's curriculum
- Per department, per semester
- Mark each subject as: Fixed / PE (Program Elective) / OE (Open Elective)
- Set prerequisites (informational + enforced at elective selection)

### 2.5 Evaluation Scheme
`/dashboard/exam/schemes/`
- Define CIE + SEE weightage (e.g. CIE 40 + SEE 60)
- Configure: number of CIE tests, best-of rule, passing marks
- Optional: Practical/Viva components
- Grading type: Absolute / Relative / Credit-based

---

## Phase 3 — Student Onboarding

### 3.1 Registration
- Admin sends invite links: `/dashboard/admin/student-invites/`
- Students register via invite or admin bulk-imports via CSV: `/dashboard/admin/bulk-import/`
- Each student gets: roll number (auto-generated from college ID rule), department, semester

### 3.2 Section Auto-Assignment
`/dashboard/admin/sections/`
- Admin clicks "Auto-Generate Sections" for a department + semester
- System divides students by `section_capacity` in roll-number order
- Sections created: A, B, C… (e.g. 240 students ÷ 60 = 4 sections)
- Students' `section` field updated automatically
- Manual override: admin can add/delete sections and reassign students

---

## Phase 4 — Elective Selection

### 4.1 Admin Opens Elective Pool
`/dashboard/admin/electives/`
- Admin creates an ElectivePool for a regulation + department + semester
- Sets: slot name (PE-1, OE-1), subjects in the pool, min students, max (quota) per subject, deadline
- Toggles pool status: Draft → Open → Closed

### 4.2 Student Selects Elective
`/dashboard/student/electives/`
- Student sees open pools for their semester
- Picks one subject per pool slot
- Status: Pending → Confirmed (by admin) / Rejected (quota full)

### 4.3 Admin Confirms Selections
`/dashboard/admin/electives/<id>/selections/`
- View all student choices per pool
- Confirm / Reject / Change per student
- Seat counts shown per subject (confirmed vs pending vs quota)

---

## Phase 5 — Faculty Assignment & Section Mapping

### 5.1 Faculty–Subject Assignment
`/dashboard/admin/academic-planner/`
- Assign faculty to subjects (multiple faculty per subject = parallel sections)
- Example: DSA → Dr. Dinesh (Section A), DSA → Dr. Ravi (Section B)
- Cross-department faculty assignment supported

### 5.2 Subject–Section–Faculty Mapping (SSF Map)
`/dashboard/admin/ssf-map/`
- The core mapping table: Subject + Section + Faculty + Classroom
- One record = "Dr. Ananya teaches ML to Section A in ISE-101"
- This drives timetable generation and attendance session creation
- If SSF maps exist, timetable generator uses them; otherwise falls back to FacultySubject

---

## Phase 6 — Timetable Generation

`/dashboard/admin/academic-planner/` → "Auto Update Timetable"

### Time Structure (50-min periods)
```
09:00 – 09:50   Period 1
09:50 – 10:00   Break (10 min)
10:00 – 10:50   Period 2
10:50 – 11:00   Break (10 min)
11:00 – 11:50   Period 3
11:50 – 12:00   Break (10 min)
12:00 – 12:50   Period 4
12:50 – 13:00   Break (10 min)
13:00 – 14:00   LUNCH BREAK
14:00 – 14:50   Period 5
14:50 – 15:00   Break (10 min)
15:00 – 15:50   Period 6
```

### Lab Periods
- Lab = **2 consecutive 50-min periods** (two separate Timetable rows)
- Scheduled at 14:00–14:50 and 14:50–15:40 on the same day
- No break between the two lab periods

### Constraints Enforced
- ❌ Faculty cannot be in two places at the same time (college-wide check)
- ❌ Room cannot be double-booked at the same slot
- ✅ Subject weekly hours (L-T-P) are satisfied
- ✅ Lab subjects get 2 consecutive slots
- ✅ Section-aware: Section A and B get separate slots

### Manual Override
- CSV upload: `/dashboard/admin/academic-planner/timetable/upload/`
- Download template: `/dashboard/admin/academic-planner/timetable/template/`

---

## Phase 7 — Attendance Tracking

### Faculty Marks Attendance
`/dashboard/faculty/attendance/<subject_id>/`
- Faculty selects their subject → sees today's students for their section
- Marks each student: Present / Absent / Late
- AttendanceSession auto-created on first mark (linked to subject + section + date)
- Time-locked: can mark within 10 min before class + 60 min edit window

### Attendance Rules Engine
`/dashboard/admin/attendance/rules/`
- Admin configures per college/department/semester:
  - Min overall attendance % (default 75%)
  - Min per-subject attendance % (default 75%)
  - Grace/condonation % (e.g. 5% grace → 70% accepted)
  - Alert thresholds (warn at 75%, critical at 65%)
  - Max exemption days (medical, sports, OD)

### Student View
`/dashboard/student/` → Attendance tab
- Course-wise percentage with progress bars
- Predictor: "Can miss X more" or "Need Y more classes to reach 75%"
- Calendar view: full attendance log by date with faculty name
- Eligibility status: Eligible / Ineligible for exams

### Exemptions
`/dashboard/student/exemption/` — Student applies
`/dashboard/hod/exemptions/` — HOD approves/rejects

---

## Phase 8 — Marks & Evaluation

### Internal Marks (Faculty)
`/dashboard/faculty/internal-marks/<subject_id>/`
- Enter IA1, IA2, Assignment marks, Attendance component per student

### External Marks (Exam Controller)
`/dashboard/exam/<exam_id>/marks/`
- Enter SEE (Semester End Exam) marks per student per subject

### Results
`/dashboard/exam/<exam_id>/results/`
- Exam Controller publishes results
- Auto-computes GPA, percentage, grade per subject
- Student views at `/dashboard/student/` → Results tab

### Revaluation
`/dashboard/student/revaluation/<marks_id>/` — Student requests
`/dashboard/exam/revaluations/` — Exam Controller processes
- Fee payment via Razorpay before request is accepted

### Supply Exam (Backlog)
`/dashboard/student/supply-exam/register/` — Student registers for failed subjects
`/dashboard/student/supply-exam/<id>/pay/` — Pays supply exam fee

---

## Phase 9 — Fee Management

### Fee Structure
`/dashboard/admin/fees/`
- Admin sets total semester fee per student
- Optional breakdown: Tuition, Exam, Library, Sports, Misc

### Student Payment
`/dashboard/student/fees/pay/`
- Razorpay integration (UPI, Cards, Net Banking)
- Fee components: Tuition (partial allowed), Exam (fixed), Library (editable + reason dropdown), Sports, Miscellaneous (custom + description)
- Supply exam fee and Revaluation fee handled separately
- Email confirmation sent to student + admin on successful payment
- Receipt download: `/dashboard/student/payments/<id>/receipt/`

---

## Phase 10 — Communication & Support

### Announcements
`/dashboard/admin/announcements/` — Admin posts
Students see in dashboard → Notices tab

### Help Desk
`/dashboard/helpdesk/` — Student raises ticket
`/dashboard/admin/helpdesk/` — Admin responds

### Notifications
Auto-generated for: low attendance alerts, fee reminders, new assignments, new quizzes

---

## Demo Credentials (seed_full_demo)

```
Super Admin  : admin / (Django superuser)
College Admin: anu_admin     / ANU@Admin2026
HOD (ISE)    : anu_hod_ise   / ANU@HOD2026
Faculty (ML) : fac_ml        / Faculty@123
Faculty (BD) : fac_bd        / Faculty@123
Student Sec A: ise5_a01      / Student@123
Student Sec B: ise5_b01      / Student@123
```

## Key URLs Quick Reference

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
| Faculty Dashboard | `/dashboard/faculty/` |
| Student Dashboard | `/dashboard/student/` |
