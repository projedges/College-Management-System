# EduTrack — User Manual

## Getting Started

Open your browser and go to `http://localhost:8000` (or your deployed URL).

You will see the EduTrack home page. Click **Sign In to Portal** or go directly to `/login/`.

### Logging In

1. Enter your **Username** and **Password** (provided by your college admin)
2. Answer the **Security Check** — a simple math question (e.g. "What is 3 + 5?")
3. Check **Remember me for 8 hours** if you want to stay logged in after closing the browser
4. Click **Sign In**

After login you are automatically redirected to your role-specific dashboard.

> If you forgot your password, click **Forgot password?** on the login page and enter your email address. A reset link will be sent.

### Session Timeout

If you are inactive for 30 minutes, a warning modal appears with a countdown. Click **Stay Signed In** to continue. If you ignore it, you are automatically signed out. The sidebar shows a live countdown timer so you always know how much session time remains.

---

## Super Admin

**Login URL**: `/sys/platform-access/`  
**Access**: Only Django superusers

The super admin manages the platform itself, not individual colleges.

### Creating a College

1. Go to **Overview → New College**
2. Fill in: Name, Code (short unique identifier like `VITM`), City, State
3. Click **Create College**

> Always create the college before creating its admin.

### Adding a College Admin

1. Go to **College Admins → Add College Admin**
2. Fill in: First Name, Last Name, Username, Email, Password, select the College
3. Click **Create College Admin**

### Broadcasting a Platform Notice

1. Go to **Platform Notices → Broadcast Notice**
2. Enter a Title and Message
3. Click **Broadcast to All Colleges**

### Enabling / Disabling a College

In the **Colleges** section, click **Disable** or **Enable** next to any college.

---

## College Admin

**Login**: Use credentials provided by the super admin

### Dashboard Sidebar Sections

- **Overview** — stats, fast-track actions, recent support tickets
- **My Profile** — account details and dashboard color customization
- **Start Here** — setup guide for new semesters
- **Departments** — manage departments
- **Students** — student management
- **Staff** — faculty and HOD management
- **Academics** — subjects, exams
- **Attendance Rules** — configure eligibility thresholds per department/semester
- **Finance** — fee records and summary
- **Requests** — registration requests and invite links
- **Planner** — semester planner and timetable
- **Reports** — PDF exports
- **Notices** — announcements
- **Help Desk** — support tickets

### First-Time Setup Order

1. Add departments
2. Add subjects (per department, per semester)
3. Configure attendance rules (optional — defaults to 75%)
4. Add faculty and assign HODs
5. Add students
6. Add fee records
7. Create exams
8. Post announcements

### Managing Departments

1. Go to **Departments** in the sidebar
2. Click **Add Department** — enter Name, Code, optional description and established year

### Adding Students

**Option A — Direct Add:** Go to **Students → Add Student**, fill in details, click **Save**.

**Option B — Invite Link:** Go to **Requests → Create Invite Link**, enter the student's email and department, share the link. The student registers and you convert the request.

**Option C — Bulk Import:** Go to **Students → Bulk Import**, download the CSV template, fill it in, upload.

### Adding Faculty / HOD

Go to **Staff → Add Faculty** or **Staff → HODs → Add HOD**. Fill in details. Employee IDs are auto-generated.

### Adding Subjects

Go to **Academics → Subjects → Add Subject**. Enter Name, Code, Department, Semester, Weekly Hours.

### Creating Exams

Go to **Academics → Exams → Add Exam**. Enter Name, Semester, Start Date, End Date.

### Configuring Attendance Rules

Attendance rules control the minimum attendance % required for exam eligibility. The default is 75% if no rule is configured.

1. Go to **Attendance Rules** in the sidebar
2. Click **Add Rule**
3. Select Department (blank = college-wide) and Semester (blank = all semesters)
4. Configure thresholds, grace %, alert levels, and exemption policy
5. Click **Create Rule**

**Rule precedence:** Department + Semester > Department only > College-wide default.

### Fee Management

Go to **Finance → Add Fee Record**. Select a student, enter total amount. The system tracks paid vs pending as students make payments.

### Posting Announcements

Go to **Notices → Post Announcement**. Enter Title and Message. Visible to all users in the college.

### Customizing Dashboard Colors

Go to **My Profile → Dashboard Colors**. Click a preset or enter custom hex values. Click **Save Colors**.

### Exporting Reports

Go to **Reports**: Attendance PDF, Payment PDF, Result PDF, Student CSV.

---

## Principal

**Login**: Credentials created by college admin

Read-only oversight of the entire college. Cannot create or edit records.

### Dashboard Sections

- **Dashboard** — college-wide stats
- **Departments** — full list with student and faculty counts
- **Faculty** — all faculty across all departments
- **Students** — all students with department, semester, and status
- **HODs** — all heads of department
- **Fee Overview** — total collected, total pending, students with dues
- **Attendance Health** — average attendance % per department
- **Notices** — college announcements

---

## HOD (Head of Department)

**Login**: Credentials created by college admin

### Dashboard Sections

- **Dashboard** — faculty count, student count, pending approvals, today's classes
- **Faculty** — all faculty in the department
- **Students** — all active students in the department
- **Today's Timetable** — all classes scheduled today
- **Attendance** — subject-wise attendance overview
- **Defaulters Report** — full list of students with eligibility status and failure reasons
- **Exemption Requests** — review and approve student attendance exemption requests
- **Approvals** — pending faculty requests
- **History** — past approval decisions
- **Notices** — college announcements
- **Substitutions** — manage faculty substitutions

### Approving Faculty Requests

Go to **Approvals**. Click **Approve** or **Reject** on each pending request.

### Reviewing Attendance Exemptions

1. Go to **Exemption Requests** in the sidebar
2. Review reason type, dates, and supporting document
3. Add a review note and click **Approve** or **Reject**

Approved exemptions are excluded from the student's attendance denominator — their percentage recalculates automatically.

### Viewing the Defaulters Report

Go to **Defaulters Report**. Filter by semester. Students are sorted with ineligible ones first, showing their overall %, eligibility status, and specific failure reasons.

### Managing Substitutions

Go to **Substitutions**. Select a timetable slot, substitute faculty, and date. Click **Assign Substitution**.

---

## Faculty

**Login**: Credentials created by college admin

### Dashboard Sections

- **Dashboard** — subjects assigned, sessions today, pending reviews
- **My Subjects** — all assigned subjects with action buttons
- **Attendance** — recent sessions, defaulter counts per subject
- **Today's Timetable** — today's class schedule
- **Internal Marks** — IA1, IA2, assignment, attendance components per student
- **Assignments & Reviews** — create assignments, review submissions
- **Leave Application** — apply for leave
- **My Requests** — HOD approval requests
- **Notices** — college announcements

### Marking Attendance

1. Go to **My Subjects** — click **Attendance** next to a subject
2. The date defaults to today (you can change it)
3. Use **All Present** or **All Absent** for bulk marking, then adjust individual students
4. Click **Save Attendance**

> Attendance can only be marked once per subject per day. In production there is a time window (class time + 10 min grace + 60 min edit window).

### Correcting Attendance

Click the correction icon next to a student's record. Select the new status, enter a mandatory reason, click **Save Correction**. All corrections are logged with your name and timestamp.

### Viewing Defaulters

Go to **My Subjects → Defaulters** next to a subject. Students are sorted by attendance % (lowest first). The threshold shown is the one configured by your admin.

### Entering Marks

Go to **My Subjects → Marks** next to a subject. Set Max Marks, enter marks per student, click **Save Marks**.

### Entering Internal Marks

Go to **Internal Marks → Enter Internals** next to a subject. Enter IA1, IA2, Assignment, Attendance marks per student. Click **Save**.

### Creating an Assignment

Go to **Assignments & Reviews → Create Assignment**. Fill in Subject, Title, Description, Deadline. Click **Save** (draft), then **Publish** to make it visible to students.

### Reviewing Submissions

Go to **Assignments & Reviews**. Click **Review** next to a submission. Enter marks and feedback. Click **Save Review**.

### Creating a Quiz

Go to **Quizzes → Create Quiz**. Enter details, add questions (MCQ or True/False), mark correct answers. Click **Activate Quiz** to make it live.

### Applying for Leave

Go to **Leave Application**. Select leave type, enter dates and reason, optionally suggest a substitute. Click **Submit**.

---

## Student

**Login**: Credentials provided by college admin after registration

### Dashboard Sections

- **Dashboard** — attendance snapshot, CGPA, pending assignments, fee status, today's timetable
- **What's New** — new assignments and active quizzes from the last 7 days
- **Profile** — personal details, photo, edit profile
- **Attendance** — eligibility status banner, subject-wise attendance with predictor
- **Results** — semester GPA, subject marks, grade breakdown
- **Academic Track** — CGPA trend across semesters
- **Course Structure** — all subjects for current semester
- **Internal Marks** — IA1, IA2, assignment, attendance components
- **Quizzes** — active quizzes to attempt
- **Today's Timetable** — today's class schedule
- **Assignments** — pending, submitted, and graded assignments
- **Fees** — fee status, payment history, pay now
- **Notices** — college announcements
- **Notifications** — system alerts (low attendance, fee reminders)
- **Support** — link to help desk

### Viewing Attendance & Eligibility

Go to **Attendance** in the sidebar. At the top you will see an **Eligibility Status Banner**:

- **Green — Eligible for Exams**: Your attendance meets all configured thresholds
- **Red — Currently Ineligible**: Shows specific reasons (e.g. "Overall: 68% < 70% required")

Each subject shows a progress bar, present/total count, percentage, and a predictor ("Can miss X more classes" or "Attend X consecutive classes to reach threshold"). The threshold shown is the one configured by your admin for your department and semester.

### Applying for an Attendance Exemption

If you were absent due to medical reasons, sports events, or official duty:

1. Go to **Attendance** — click **Apply Exemption** (shown when ineligible)
2. Select Reason Type, enter dates, describe the reason, upload a document (optional)
3. Click **Submit Request**

Your HOD will review and approve or reject. Approved exemptions are excluded from your attendance denominator.

### Requesting an Eligibility Override

If you are detained and have exceptional circumstances:

1. Go to **Attendance** — click the override request button (shown when ineligible)
2. Enter a detailed reason
3. Click **Submit Request**

The exam cell will review. If approved, your hall ticket will be issued.

### Viewing Results

Go to **Results**. Each semester shows GPA, percentage, and subject-wise breakdown. Click **Download PDF Report** for a printable result card.

### Requesting Revaluation

After results are published, if you believe marks were incorrectly evaluated:

1. Go to **Results** — find the subject
2. Click **Request Revaluation**
3. Enter a reason and click **Submit**

The exam cell will review and either accept (with revised marks) or reject.

### Submitting an Assignment

Go to **Assignments → Pending**. Click **Submit**, upload your file, click **Submit Assignment**.

### Attempting a Quiz

Go to **Quizzes**. Click **Attempt Quiz**, answer all questions, click **Submit Quiz** before the timer runs out.

### Paying Fees

Go to **Fees → Pay Now**. Enter amount, select payment method, enter transaction ID, click **Complete Payment**.

### Raising a Support Ticket

Go to **Support → Open Help Desk**. Fill in details and click **Submit**.

---

## Lab Staff

**Login**: Credentials created by college admin

### Dashboard Sections

- **Dashboard** — active sessions right now, today's class count, classroom count
- **Today's Schedule** — full schedule for all rooms today
- **Classrooms** — all classrooms with room number and capacity
- **Notices** — college announcements

---

## Examination Department

**Login**: Credentials assigned by the Controller of Examinations or College Admin (role: Exam Controller)

### Exam Staff Roles

| Role | Permissions |
|---|---|
| Controller of Examinations (CoE) | Full access — publish results, manage staff, approve schemes |
| Deputy Controller | Same as CoE except cannot add/remove staff |
| Section Officer | Scoped to specific departments — hall tickets, marks verification, schedules |
| Valuation Officer | Assigned to evaluate answer scripts for specific subjects |
| Data Entry Operator | Enters marks only — cannot verify or publish |
| Coordinator | Manages schedules and logistics — no result access |

### Dashboard Overview

Shows total exams, marks entries, published/draft results, hall tickets issued, detained students, pending revaluations, exam staff roster, evaluation schemes, and recent audit log.

### Managing Exam Staff (CoE / Deputy only)

1. Go to **Exam Staff** in the sidebar
2. Click **Add Staff Member**
3. Enter the system username, select exam role, enter employee ID
4. For Section Officers: select the departments they are responsible for
5. Click **Add Staff Member**

### Configuring Evaluation Schemes

1. Go to **Eval Schemes** in the sidebar
2. Click **Add Scheme**
3. Select Department (blank = all departments)
4. Configure CIE (tests, best-of rule, marks), SEE (paper max, scaled contribution, min to pass), optional Practical, and overall passing %
5. Click **Save Scheme**

### Setting Up an Exam Schedule

From the dashboard, click **Schedule** next to an exam. For each subject: select date, time, venue, invigilator, max marks. Click **Save Slot**.

### Assigning Valuators

From the exam schedule page, go to **Valuation**. Select a subject slot, valuation type (First / Second / Arbitration), and assign an internal faculty or external examiner. Click **Assign**.

### Generating Hall Tickets

1. From the dashboard, click **Hall Tickets** next to an exam
2. Review the eligibility table (attendance %, fee dues, auto-determined status)
3. Click **Generate Hall Tickets**
   - Meets threshold + no fee dues → **Issued**
   - Below threshold → **Detained**
   - Fee dues → **Withheld**

> The attendance threshold is taken from the Attendance Rules configured by the admin. Default is 75%.

### Reviewing Eligibility Overrides

From the hall tickets page, click **Overrides**. Review pending requests, add a justification note, click **Approve** or **Reject**. Approved overrides automatically update the hall ticket to Issued.

### Monitoring Marks Entry

From the dashboard, click **Marks** next to an exam. See each subject's entry status (Complete / Partial / Not Started).

### Computing and Publishing Results

1. From the dashboard, click **Results** next to an exam
2. Click **Compute** — calculates marks, percentage, grade, pass/fail
3. Click **Verify** — marks results as verified (Deputy or CoE)
4. Click **Publish** — makes results visible to students (CoE only)

### Processing Revaluations

Go to **Revaluations** in the sidebar. Enter revised marks and click **Accept**, or click **Reject**.

---

## Help Desk (Public)

Anyone can submit a support ticket at `/helpdesk/`.

1. Select your college
2. Fill in: Name, Email, Issue Type, Subject, Description
3. Click **Submit Ticket**

---

## Common Questions

**I forgot my username.** Contact your college admin or submit a help desk ticket.

**My attendance shows wrong.** Contact your faculty to correct it (they can edit with a reason). Or submit a help desk ticket.

**I was absent for medical reasons — will it affect my eligibility?** Submit an Attendance Exemption Request from your Attendance section. Your HOD will review it.

**I am detained but I have a valid reason.** Submit an Eligibility Override Request from your Attendance section. The exam cell will review it.

**My fee balance looks wrong.** Contact your college admin via the help desk.

**I can't submit an assignment — the deadline has passed.** Assignments cannot be submitted after the deadline. Contact your faculty.

**The quiz timer ran out before I submitted.** Quizzes auto-submit when the timer expires.

**I don't see my result.** Results are published by the exam cell after marks are verified.

**My session keeps expiring.** The system logs you out after 30 minutes of inactivity. Check **Remember me** on login to extend to 8 hours.

**The attendance threshold shown is different from 75%.** Your college admin has configured a custom attendance rule for your department or semester.
