# EduTrack Current Working Status

This file is the clear "what is already done" reference for the current internship build.

## 1. Core Working Model

- `Super Admin` works from a dedicated hidden workspace at `/superadmin1/`
- `Super Admin` creates colleges and college-admin accounts
- `College Admin` is scoped to one college and manages that college's records
- `Principal`, `HOD`, `Faculty`, and `Student` have separate dashboards
- Public `/register/` is no longer open self-registration
- Public `/register/` now works only through a one-time invite link shared by college admin
- Student accounts are created by the college admin after review and conversion

## 2. What Changed In This Build

- Removed public admin exposure from the home page
- Added a proper super admin interface instead of relying only on Django admin
- Added college-aware dashboards so the active college is visible after login
- Reworked dashboards to use focused dynamic sections instead of one long clumsy page
- Added a controlled student onboarding flow through request review and conversion
- Simplified the college-admin dashboard to make daily operations easier
- Added error pages, password reset pages, PDF outputs, and stronger demo readiness

## 3. Public Portal Status

- Home page is public-facing and cleaner for demo use
- Super admin entry is not shown in the public UI
- Login page is the normal entry for existing users
- Register page is locked behind one-time invite links
- Public help desk is available for access issues and support escalation
- Login and register pages include password visibility toggles

## 4. Super Admin Features

- View colleges
- View college-admin entities
- Create new colleges
- Create college-admin accounts linked to a college
- Use Django admin only as a fallback management tool

## 5. College Admin Features

- Guided college-admin dashboard with workflow-oriented sections
- Manage departments
- Manage students
- Manage faculty
- Manage HODs
- Manage subjects
- Manage fee records
- Manage announcements
- Manage exams
- Review student access requests
- Generate one-time onboarding invite links for students
- Convert approved requests into prefilled student account creation
- Export filtered student data as CSV
- Use a semester planner to manage semester subjects, faculty assignment, availability, and timetable generation
- Review and manage help desk tickets
- Export attendance, payment, and result PDF reports

## 6. Principal Features

- College-wide overview dashboard
- View departments
- View students
- View faculty
- View HODs
- View notices

## 7. HOD Features

- Department-specific dashboard
- Faculty list
- Student count visibility
- Attendance overview
- Approval queue
- Approval history
- Notice visibility

## 8. Faculty Features

- Faculty dashboard with dynamic sections
- Mark attendance
- Enter marks
- Create assignments
- Review student submissions

## 9. Student Features

- Student dashboard with dynamic sections
- Profile edit page
- Attendance overview
- Result viewing
- Subject-wise semester marks visible inside the results area
- Result PDF download
- Assignment submission
- Fee payment flow
- Payment receipt page
- Payment receipt PDF download

## 10. Security, Reliability, and UX

- CSRF support improved for localhost and ngrok-style access
- Custom 400, 403, 404, and 500 pages added
- Password reset flow added
- Basic login/logout activity logging exists
- Login attempt tracking exists in user security records
- Missing admin templates and broken admin pages were repaired
- Roll numbers are auto-generated in `year-collegecode-branch-serial` format during student onboarding

## 11. Demo Data Available

- One demo college is seeded
- Demo users exist for super admin, college admin, principal, HOD, faculty, student, and lab staff
- Attendance, marks, results, fees, timetable, announcements, and one HOD approval are seeded
- Invite-link and help-desk demo records are seeded
- Student profile data and one assignment are available for demo use

## 12. Current Gaps

- Lab Staff still does not have a dedicated dashboard
- Faculty still cannot raise approval requests directly to HOD from their own UI
- Principal creation/editing still partly depends on Django admin
- Semester planner is now present, but deeper timetable logic and conflict detection still need expansion
- Automated tests are still limited and should be expanded

## 13. Recommended Demo Flow

1. Show home page and controlled login/request entry
2. Show super admin creating college-level control
3. Show college-admin guided workspace
4. Show invite-link onboarding and request conversion
5. Show semester planner and CSV export
6. Show faculty attendance and assignment workflow
7. Show student dashboard, subject-wise results, payment, and help desk
8. Show custom error pages and password reset briefly

This gives the clearest picture of what is already complete in the current build.
