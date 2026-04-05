# EduTrack — Product Overview

## What Is EduTrack?

EduTrack is a web-based academic management platform built for colleges and universities. It replaces paper registers, spreadsheets, and disconnected tools with a single portal where every person in a college — from the principal down to a student — has their own dashboard, their own data, and their own set of actions.

The system is multi-tenant. One installation can serve multiple colleges. Each college is completely isolated — its students, faculty, departments, and data are never visible to another college.

---

## Who Is It For?

| Role | What they do on EduTrack |
|------|--------------------------|
| Super Admin | Manages the platform itself — creates colleges, assigns college admins |
| College Admin | Runs the college — manages departments, students, faculty, fees, exams, announcements |
| Principal | Read-only oversight of the entire college — attendance health, fee summary, department stats |
| HOD (Head of Department) | Manages their department — approves faculty requests, manages substitutions, monitors attendance |
| Faculty | Marks attendance, enters marks, creates assignments and quizzes, applies for leave |
| Student | Views attendance, results, timetable, submits assignments, attempts quizzes, pays fees |
| Lab Staff | Monitors live classroom sessions and room schedules |

---

## Core Modules

### 1. College & Department Management
Every college has departments. Departments are the backbone — students, faculty, subjects, and timetables all belong to a department. A college admin creates and manages departments. Department names and codes are unique within a college (two colleges can both have a "CSE" department).

### 2. User Management & Onboarding
EduTrack does not allow open self-registration. Access is controlled:
- College admin creates an **invite link** tied to a specific department and email
- The student fills a registration form through that link
- Admin reviews the request and converts it into a real student account
- Roll numbers are auto-generated based on a configurable rule (e.g. `2024-VITM-CSE-001`)

Faculty, HODs, and principals are created directly by the college admin.

### 3. Academic Structure
- **Subjects** belong to a department and a semester (integer 1–8)
- **Faculty** are assigned to subjects via Faculty-Subject assignments
- **Timetable** slots are created per subject, with day, time, and classroom
- The system can auto-generate a timetable from faculty availability slots

### 4. Attendance
Faculty mark attendance per subject per day. The system:
- Enforces one session per subject per day
- Tracks Present / Absent / Late per student
- Calculates attendance percentage per subject
- Flags students below 75% with automatic notifications
- Supports substitutions — HOD assigns a substitute faculty who can then mark attendance for that slot

### 5. Marks & Results
- Faculty enter marks per student per subject per exam
- Grades are computed automatically (O / A+ / A / B+ / B / C / F)
- Internal marks (IA1, IA2, Assignment, Attendance components) are tracked separately
- Results (GPA, percentage, total marks) are published per semester
- Students can download a PDF result report

### 6. Assignments & Quizzes
- Faculty create assignments with deadlines and publish them to students
- Students upload files as submissions
- Faculty review submissions and assign marks with feedback
- Faculty create MCQ/True-False quizzes with time limits
- Students attempt quizzes within the active window
- Scores are auto-calculated

### 7. Fee Management
- College admin creates fee records per student
- Fee structures are defined per department per semester
- Students can make payments through the portal
- Payment receipts are generated as PDFs
- Admin sees a real-time summary of collected vs pending fees

### 8. Timetable & Substitutions
- Timetable slots are visible to students (today's classes), faculty (their schedule), HODs (department view), and lab staff (all rooms)
- HODs manage substitutions — when a faculty is absent, a substitute is assigned for a specific date
- The substitute faculty can then mark attendance for that slot

### 9. Announcements & Notifications
- College admin and super admin post announcements
- Announcements are visible to all roles within the college
- System auto-generates notifications for students (low attendance warnings, fee reminders)

### 10. Help Desk
- Anyone can submit a support ticket (login issues, fee problems, academic queries)
- College admin manages and resolves tickets
- Ticket comments allow back-and-forth communication

### 11. College Branding
- Each college can upload a logo
- College admin can customize dashboard colors (primary, accent, sidebar) using 4 presets or custom hex values
- Branding applies across all dashboards for that college's users

### 12. Reports & Exports
- Attendance report PDF (by department)
- Payment/fee report PDF
- Result report PDF
- Student list CSV export
- Individual student result PDF
- Payment receipt PDF

---

## Security Model

- **Session timeout**: Users are automatically logged out after 30 minutes of inactivity. A warning modal appears 2 minutes before logout with an option to stay signed in.
- **Role-based access**: Every view checks the user's role. A student cannot access faculty views, a faculty cannot access admin views, etc.
- **Invite-only registration**: No public sign-up. All accounts are created or approved by a college admin.
- **CAPTCHA on login**: A simple math captcha prevents automated login attempts.
- **Password hashing**: Argon2 (strongest available in Django).
- **Multi-college isolation**: All queries are scoped to the user's college. Cross-college data access is impossible.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.1 (Python) |
| Database | SQLite (dev) / PostgreSQL (production-ready) |
| Frontend | Server-rendered HTML + vanilla JS |
| Styling | Custom CSS with CSS variables for theming |
| Auth | Django's built-in auth + custom session middleware |
| PDF generation | Pure Python (no external library) |

---

## What EduTrack Is Not

- Not a video conferencing or LMS platform (no lecture recordings, no course content hosting)
- Not a financial accounting system (fee tracking only, not full accounting)
- Not a mobile app (responsive web, works on mobile browsers)
- Not a public-facing admissions portal (invite-only access)
