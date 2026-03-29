# EduTrack Testing Guide

All demo users below belong to **Sri Venkateswara College of Engineering (SVCE)** unless stated otherwise.

## Quick Start

```bash
venv\Scripts\activate
python manage.py migrate
python seed_data.py
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Access Rules

- Public `/register/` is **not** direct account creation anymore.
- Public `/register/` is only for **student access requests**.
- Public `/register/` works only with a one-time invite link shared by college admin.
- Students should not receive direct account-creation access from the public site.
- College admin creates invite links, reviews the request, and creates the actual student account.
- Public `/helpdesk/` is the fallback when a student does not have a valid invite link.
- Staff, principal, college admin, and super admin accounts are created internally.
- All real users sign in from `/login/`.

## Test Accounts

| Role | Username | Password | Portal URL |
|------|----------|----------|------------|
| Super Admin | `admin_et` | `Admin@1234` | `/superadmin1/` |
| College Admin | `college_admin_svce` | `College@1234` | `/dashboard/admin/` |
| Principal | `principal_svce` | `Principal@1234` | `/dashboard/principal/` |
| HOD | `hod_cse` | `Hod@1234` | `/dashboard/hod/` |
| Faculty | `faculty_raj` | `Faculty@1234` | `/dashboard/faculty/` |
| Faculty | `faculty_priya` | `Faculty@1234` | `/dashboard/faculty/` |
| Student | `student_arjun` | `Student@1234` | `/dashboard/student/` |
| Student | `student_meena` | `Student@1234` | `/dashboard/student/` |
| Student | `student_kiran` | `Student@1234` | `/dashboard/student/` |
| Lab Staff | `lab_suresh` | `Lab@1234` | `/dashboard/student/` |

## What Is Preloaded

### College Structure

- 1 college: SVCE
- 3 departments: CSE, ECE, MECH

### Subjects

- `CSE401` Data Structures
- `CSE402` Operating Systems
- `CSE403` Database Management

### Faculty Mapping

- `faculty_raj` teaches `CSE401` and `CSE402`
- `faculty_priya` teaches `CSE403`

### Attendance

- `student_arjun` has attendance seeded across the CSE subjects

### Marks and Results

- Mid-semester marks are seeded for `student_arjun`
- Semester results are seeded for `student_arjun`

### Fees

- `student_arjun` fully paid
- `student_meena` partial payment
- `student_kiran` pending payment

### Other Demo Data

- timetable entries
- announcements
- one HOD approval sample
- one assignment
- one student profile with contact details

## Role Testing Flow

### Super Admin

1. Login as `admin_et`
2. Confirm redirect to `/superadmin1/`
3. Check colleges list
4. Check college-admin list
5. Open add-college form
6. Open add-college-admin form

### College Admin

1. Login as `college_admin_svce`
2. Confirm redirect to `/dashboard/admin/`
3. Verify college name is visible in the dashboard
4. Open workflow sections: Students, Staff, Academics, Finance, Requests, Reports
5. Open the invite link page and generate a one-time onboarding link
6. Open the request queue and confirm it is available
7. Open the semester planner
8. Export student data as CSV
9. Open fee add form
10. Export at least one PDF report

### Principal

1. Login as `principal_svce`
2. Confirm redirect to `/dashboard/principal/`
3. Verify college name is visible
4. Check departments, faculty, students, HODs, and notices

### HOD

1. Login as `hod_cse`
2. Confirm redirect to `/dashboard/hod/`
3. Verify department and college name are visible
4. Check faculty list
5. Check attendance overview
6. Approve or reject the seeded request

### Faculty

1. Login as `faculty_raj`
2. Confirm redirect to `/dashboard/faculty/`
3. Verify college name is visible
4. Open attendance page for a subject
5. Open marks page for a subject and exam
6. Create an assignment
7. Review a student submission if available

### Student

1. Login as `student_arjun`
2. Confirm redirect to `/dashboard/student/`
3. Verify college name is visible
4. Open profile section
5. Open results and download result PDF
6. Open assignments and submit work
7. Open fees and inspect payment status

### Payment Flow

Use `student_meena`:

1. Login
2. Open `/dashboard/student/fees/pay/`
3. Submit a small payment
4. Confirm redirect to receipt page
5. Download receipt PDF

## Public Flow Testing

### Home Page

1. Open `/`
2. Confirm there is no public admin button
3. Confirm the public CTA is sign-in or student request

### Student Access Request

1. Login as `college_admin_svce`
2. Open `/dashboard/admin/student-invites/`
3. Create an invite link for a fresh email
4. Open that invite link in a new browser session
5. Submit the student access request once
6. Confirm the same invite link no longer opens the form a second time
7. Login again as `college_admin_svce`
8. Open `/dashboard/admin/registration-requests/`
9. Confirm the request appears
10. Use **Convert** to open prefilled student creation form

### Help Desk

1. Open `/helpdesk/`
2. Submit an access-related ticket
3. Login as `college_admin_svce`
4. Open `/dashboard/admin/helpdesk/`
5. Confirm the ticket appears and update its status

### Student CSV Export

1. Login as `college_admin_svce`
2. Open `/dashboard/admin/students/`
3. Apply a department or semester filter if needed
4. Use **Export CSV**
5. Confirm the download contains student rows and generated roll numbers

### Semester Planner

1. Login as `college_admin_svce`
2. Open `/dashboard/admin/academic-planner/`
3. Choose a department and semester
4. Add a semester subject if needed
5. Assign faculty to a subject
6. Add faculty availability
7. Use **Auto Update Timetable**
8. Confirm timetable rows are created

## Error Handling

Check:

- missing page shows custom 404
- forbidden/CSRF failures show custom 403
- password reset pages open correctly

## Current Limitations

- Lab Staff still falls back to the student flow
- Faculty cannot yet submit HOD approval requests from their own UI
- Principal management still partly depends on Django admin
- Subject allocation still needs a better college-admin workflow
- Automated tests are still basic and should be expanded

## Suggested Demo Order

1. Home page
2. Super admin workspace
3. College admin guided dashboard
4. Student request queue and conversion
5. Faculty attendance and assignments
6. Student profile, payment, and PDF reports
7. HOD approvals

This sequence gives the clearest internship-style demonstration of the system.
