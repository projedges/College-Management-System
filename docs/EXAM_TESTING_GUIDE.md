# Examination System — Testing Guide

This guide walks through the complete exam workflow end-to-end.
Follow the phases in order. Each phase lists the role, the exact URL, and what to verify.

---

## Prerequisites — Accounts You Need

Before testing, make sure these accounts exist in the system:

| Role | How to create |
|---|---|
| College Admin (role=1) | Django admin or super admin panel |
| Exam Staff / COE (role=7) | Admin creates via `/dashboard/exam/staff/add/` |
| Faculty (role=3) | Admin creates via `/dashboard/admin/faculty/add/` |
| Student (role=4) | Admin creates via `/dashboard/admin/students/add/` |

Login URL: `/login/`
After login, `/dashboard/` auto-redirects each role to their dashboard.

---

## Phase 1 — Admin Setup

**Login as: College Admin (role=1)**
Dashboard: `/dashboard/admin/`

### 1.1 Create a Department
- Go to `/dashboard/admin/departments/`
- Click Add → fill name (e.g. `Computer Science`), code (e.g. `CSE`)
- Save

### 1.2 Create Subjects
- Go to `/dashboard/admin/subjects/`
- Add at least 3 subjects for the department, semester 1
- Set credits (e.g. 3, 4, 3), category (PC), lecture hours
- Save each

### 1.3 Add Faculty
- Go to `/dashboard/admin/faculty/add/`
- Create a faculty user, assign to the department
- Note the username/password

### 1.4 Assign Faculty to Subjects
- Go to `/dashboard/admin/academic-planner/`
- Under SSF Map (`/dashboard/admin/ssf-map/`), map faculty → subject → section

### 1.5 Add Students
- Go to `/dashboard/admin/students/add/`
- Create 2–3 students in the same department, semester 1
- Note their roll numbers

### 1.6 Create an Exam
- Go to `/dashboard/admin/exams/`
- Click Add → name it (e.g. `Sem 1 Nov 2025`), set semester=1, start/end dates
- Save — note the exam ID from the URL

**Expected:** Exam appears in the list. No errors.

---

## Phase 2 — Exam Department Setup

**Login as: Exam Staff / COE (role=7)**
Dashboard: `/dashboard/exam/`

### 2.1 Create Exam Types
- Go to `/dashboard/exam/types/`
- Add `CIE-1` (category=CIE, max=30, passing=12, weightage=30%)
- Add `SEE Nov 2025` (category=SEE, max=100, passing=35, weightage=70%)

### 2.2 Create Evaluation Scheme
- Go to `/dashboard/exam/schemes/`
- Click Add → name it (e.g. `Standard Sem 1`)
- Set: CIE count=2, best of=2, CIE max per test=30, CIE total=50
- SEE max=100, SEE scaled to=50, SEE passing min=35
- Overall passing min=40, grading type=Absolute
- Save

### 2.3 Create Exam Schedule
- Go to `/dashboard/exam/<exam_id>/schedule/`
- Add a slot for each subject: date, start/end time, venue, max marks=100, passing=40
- Optionally assign an invigilator

### 2.4 Assign Valuators (optional)
- Go to `/dashboard/exam/<exam_id>/valuation/`
- For each subject, assign First Valuation (internal faculty or external examiner)
- Optionally assign Second Valuation for double-valuation subjects

### 2.5 Generate Hall Tickets
- Go to `/dashboard/exam/<exam_id>/hall-tickets/`
- Click "Generate Hall Tickets" for all eligible students
- Verify: students with attendance >= 75% and no fee dues get status=ELIGIBLE
- Students below threshold get DETAINED

**Expected:** Hall ticket list shows each student's eligibility status.

---

## Phase 3 — Faculty Marks Entry

**Login as: Faculty (role=3)**
Dashboard: `/dashboard/faculty/`

### 3.1 Enter Internal Marks
- Go to `/dashboard/faculty/internal-marks/<subject_id>/`
- For each student enter: IA1, IA2, assignment marks, attendance marks
- Click Save

### 3.2 Enter Exam Marks
- Go to `/dashboard/faculty/marks/<subject_id>/<exam_id>/`
- For each student enter marks obtained (out of max marks)
- The grade is auto-calculated on save
- Enter marks for all 3 subjects

**Verify:**
- Marks are saved per student per subject
- Grade shows correctly (O/A+/A/B+/B/C/F based on %)
- You cannot enter marks > max marks

---

## Phase 4 — COE: Marks Review & Processing

**Login as: COE (role=7)**

### 4.1 Check Marks Entry Status
- Go to `/dashboard/exam/<exam_id>/marks/`
- Verify each subject shows: Enrolled count, Entered count, Pending count
- Status should show Complete / Partial / Not Started

**Expected:** All subjects show Complete before proceeding.

### 4.2 Apply Moderation (if needed)
- Go to `/dashboard/exam/<exam_id>/moderation/`
- Create a rule: select subject, type=ADD, value=5, reason="Paper was difficult"
- Click "Create Moderation Rule"
- Then click "Apply" on the rule
- Verify: marks for that subject increased by 5 for all students

### 4.3 Apply Grace Marks (borderline students)
- Go to `/dashboard/exam/<exam_id>/grace-marks/`
- Failing students appear at the top sorted by gap to passing
- For a failing student, enter grace amount (e.g. 3) and reason
- Click Apply
- Verify: marks updated, SGPA recalculated, "Applied" badge appears

### 4.4 Compute Results
- Go to `/dashboard/exam/<exam_id>/results/`
- Click "Compute Results"
- Verify: summary shows Total, Computed, Passed, Failed counts
- Each student row shows their result status (DRAFT)

### 4.5 Verify Results
- On the same page, click "Verify Results"
- Status changes from DRAFT → VERIFIED
- Verify: verified count in summary increases

### 4.6 Publish Results
- Click "Publish Results"
- Confirm the dialog
- Status changes VERIFIED → PUBLISHED
- Verify: published count = total students, students can now see results

### 4.7 Freeze Results
- Click "Freeze Results"
- A red frozen banner appears at the top
- Try clicking Compute/Verify/Publish — should show error "Results are frozen"

### 4.8 Unfreeze Results
- In the frozen banner, enter a reason (e.g. "Correction needed for roll 101")
- Click Unfreeze
- Banner disappears, actions are available again

---

## Phase 5 — Student: View Results

**Login as: Student (role=4)**
Dashboard: `/dashboard/student/`

### 5.1 View Results in Dashboard
- Click the "Results" tab in the student dashboard
- Verify: semester tabs appear, each showing SGPA
- Subject-wise marks table shows: subject name, code, exam, marks, grade, %
- Best subject and worst subject highlighted
- Grade distribution pills (O × 1, A+ × 2, etc.)

### 5.2 Check CGPA
- Top stat cards show CGPA
- Bottom of results section shows "CGPA (weighted): X.XX"

### 5.3 Download PDF Report
- Click "Download PDF Report"
- URL: `/dashboard/student/results/report/pdf/`
- Verify: PDF downloads with student info, semester results, marks breakdown

### 5.4 Download Official Transcript
- Click "Official Transcript"
- URL: `/dashboard/student/transcript/pdf/`
- Verify: formal A4 PDF with college header, student info table, semester-wise marks, CGPA summary, academic standing

---

## Phase 6 — Revaluation Flow

### 6.1 Student Requests Revaluation
**Login as: Student**

- In the Results tab, find a subject with a failing or low grade
- Click "Apply Revaluation" button on that subject row
- URL: `/dashboard/student/revaluation/<marks_id>/`
- This redirects to the revaluation fee payment page
- Complete the fee payment (use test mode if Razorpay is in test mode)
- After payment, `RevaluationRequest` is created with status=PENDING

### 6.2 COE Reviews Revaluation
**Login as: COE**

- Go to `/dashboard/exam/revaluations/`
- Pending requests appear in the table
- To accept: enter revised marks in the input, click "Accept"
  - Marks are updated, grade recalculated, SGPA recalculated
- To reject: click "Reject"
  - Status changes to REJECTED

### 6.3 Student Sees Updated Result
**Login as: Student**

- Go back to Results tab
- Verify: marks show the revised value, grade updated

---

## Phase 7 — Result Version History

**Login as: COE**

- Go to `/dashboard/exam/<exam_id>/result-versions/`
- Each student shows their current SGPA and snapshot count
- Expand to see version table: version number, SGPA, marks, %, reason, who created it, when
- Snapshots are created automatically on: publish, moderation apply, revaluation accept

**Verify:** After completing phases 4–6, each student should have at least 1–2 snapshots.

---

## Phase 8 — Supply Exam (Backlog)

**Login as: Student (with a failed subject)**

### 8.1 Register for Supply Exam
- Go to `/dashboard/student/supply-exam/register/`
- Select the exam and the failed subjects
- Total fee is calculated (per subject fee from FeeBreakdown)
- Click Register → redirected to payment

### 8.2 Pay Supply Exam Fee
- URL: `/dashboard/student/supply-exam/<reg_id>/pay/`
- Complete payment
- Status changes PENDING → PAID

---

## Phase 9 — Eligibility Override (Detained Student)

### 9.1 Student Requests Override
**Login as: Student (with attendance < 75%)**

- Go to `/dashboard/student/exam/<exam_id>/override/`
- Fill reason, submit
- Status = PENDING

### 9.2 COE Reviews Override
**Login as: COE**

- Go to `/dashboard/exam/<exam_id>/overrides/`
- Approve or reject the override request
- If approved, student's hall ticket status changes to ELIGIBLE

---

## Quick Smoke Test Checklist

Run through this after any code change:

- [ ] `/login/` — login works for all 4 roles
- [ ] `/dashboard/` — each role redirects correctly
- [ ] `/dashboard/exam/` — COE dashboard loads, shows exam list
- [ ] `/dashboard/exam/<id>/marks/` — marks overview loads
- [ ] `/dashboard/exam/<id>/results/` — results page loads, compute works
- [ ] `/dashboard/exam/<id>/grace-marks/` — grace marks page loads
- [ ] `/dashboard/exam/<id>/result-versions/` — version history loads
- [ ] `/dashboard/faculty/marks/<subject_id>/<exam_id>/` — marks entry form loads
- [ ] `/dashboard/student/` — student dashboard loads with results tab
- [ ] `/dashboard/student/transcript/pdf/` — transcript PDF downloads
- [ ] `/dashboard/student/results/report/pdf/` — report PDF downloads
- [ ] `/dashboard/exam/revaluations/` — revaluation list loads

---

## Common Issues

**COE dashboard shows "Exam Department access not found"**
→ The user's `ExamStaff` record is missing or `is_active=False`. Go to `/dashboard/exam/staff/` and check.

**Faculty can't see subjects in marks entry**
→ `FacultySubject` mapping is missing. Admin must assign faculty to subjects via the academic planner.

**Students not appearing in marks entry**
→ Student's `department` and `current_semester` must match the subject's department and semester.

**Hall tickets show DETAINED**
→ Student's attendance is below the `AttendanceRule` threshold (default 75%). Either correct attendance or use eligibility override.

**Results not visible to student**
→ `ExamResult.status` must be `PUBLISHED`. Run Compute → Verify → Publish in that order.

**Grace marks "already applied" error**
→ A `GraceMarksApplication` with `status=APPLIED` already exists for that marks record. Check the grace marks page — it shows "Applied" badge.

**Transcript PDF is blank / missing semesters**
→ `Result` records must exist (created during Compute step). Run compute first.
