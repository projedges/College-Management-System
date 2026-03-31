# EduTrack — Feature Testing Guide

## Quick Start

```bash
# 1. Activate virtual environment
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# 2. Run migrations
python manage.py migrate

# 3. Seed demo data
python seed_data.py

# 4. Start server
python manage.py runserver
```

Open: http://localhost:8000

---

## Test Credentials

| Role | Username | Password |
|------|----------|----------|
| Super Admin | `superadmin` | `Super@1234` |
| College Admin | `admin_vitm` | `Admin@1234` |
| Principal | `principal_vitm` | `Principal@1234` |
| HOD (CSE) | `hod_rajesh_vitm` | `Hod@1234` |
| HOD (ISE) | `hod_meera_vitm` | `Hod@1234` |
| HOD (ECE) | `hod_vikram_vitm` | `Hod@1234` |
| HOD (ME) | `hod_homi_vitm` | `Hod@1234` |
| Faculty | `fac_sunita_vitm` | `Faculty@1234` |
| Faculty | `fac_amit_vitm` | `Faculty@1234` |
| Faculty | `fac_priya_vitm` | `Faculty@1234` |
| Lab Staff | `lab_suresh_vitm` | `Lab@1234` |
| Student | `stu_1_vitm` | `Student@1234` |
| Student | `stu_50_vitm` | `Student@1234` |

---

## Feature Walkthrough by Role

### 1. Super Admin
Login: `superadmin / Super@1234`  
URL: http://localhost:8000/sys/platform-access/

- View all colleges on the platform
- Add a new college → fill name, code, city, state
- Add a college admin user for that college
- Post a platform-wide announcement
- Toggle a college active/inactive

---

### 2. College Admin
Login: `admin_vitm / Admin@1234`

**Dashboard sections (sidebar):**

- **Overview** — stat cards, fast-track actions, recent support tickets
- **My Profile** — view profile details, change dashboard colors (4 presets + custom hex)
- **Start Here** — setup guide for new semester
- **Students** — recent registrations table
- **Staff** — faculty and HOD setup shortcuts
- **Academics** — departments, subjects, exams
- **Finance** — fee summary, collected vs pending
- **Requests** — pending registration requests
- **Planner** — semester planner
- **Reports** — export attendance/payment/result PDFs
- **Notices** — post and manage announcements
- **Help Desk** — view and resolve support tickets

**Things to test:**

1. Add a department → Manage → Departments → Add
2. Add a subject → Manage → Subjects → Add
3. Add a faculty member → Manage → Faculty → Add
4. Add an HOD → Manage → HODs → Add
5. Create an invite link → Manage → Invite Links → Create
6. Add a student directly → Manage → Students → Add
7. Add a fee record → Finance → Fee Records → Add
8. Create an exam → Manage → Exams → Add
9. Post an announcement → Notices → Post Announcement
10. Export a PDF report → Reports → any export button
11. Change dashboard colors → My Profile → Dashboard Colors → pick a preset → Save Colors
12. Bulk import students → Manage → Bulk Import → download template → upload CSV

---

### 3. Principal
Login: `principal_vitm / Principal@1234`

- View college-wide stats (departments, faculty, students, HODs)
- Check fee collection summary
- Review attendance health per department (bar chart)
- Browse all faculty and students
- Read college notices

---

### 4. HOD
Login: `hod_rajesh_vitm / Hod@1234` (CSE department)

1. **Dashboard** — faculty count, student count, pending approvals, classes today
2. **My Profile** — name, employee ID, department, qualification
3. **Faculty** — full faculty list for CSE
4. **Students** — all active CSE students
5. **Today's Timetable** — CSE classes scheduled today
6. **Attendance** — subject-wise attendance % for CSE
7. **Approvals** — approve or reject faculty leave/event requests
8. **Substitutions** → http://localhost:8000/dashboard/hod/substitutions/
   - Select a timetable slot
   - Pick a substitute faculty
   - Set a date → Submit
   - The substitute faculty can now mark attendance for that slot
9. **Notices** — college announcements

---

### 5. Faculty
Login: `fac_sunita_vitm / Faculty@1234`

1. **Dashboard** — subjects assigned, sessions today, pending reviews
2. **My Profile** — employee ID, designation, qualification
3. **My Subjects** — list of assigned subjects with action buttons
4. **Mark Attendance** → click Attendance button on any subject
   - Select date (defaults to today)
   - Mark each student Present / Absent / Late
   - Click Save — attendance is locked in DEBUG mode is relaxed
5. **Enter Marks** → click Marks button (requires an exam to exist)
6. **Internal Marks** → enter IA1, IA2, assignment marks per student
7. **Lesson Plans** → add weekly lesson plan entries per subject
8. **Attendance Defaulters** → see students below 75%
9. **Assignments** → Create Assignment → fill title, description, deadline, subject → Save → Publish
10. **Quizzes** → Create Quiz → add questions and options → mark correct answer → activate
11. **Leave Application** → apply for leave with substitute suggestion
12. **My Requests** → submit a request to HOD (leave/event/course)

---

### 6. Student
Login: `stu_1_vitm / Student@1234`

1. **Dashboard** — attendance summary, CGPA, fee balance, today's timetable
2. **Profile** — photo avatar, personal details, edit profile
   - Edit Profile → upload a profile photo → save
3. **Attendance** — subject-wise attendance bars with % and present/total
4. **Results** — semester GPA, subject marks breakdown
5. **Assignments** — pending assignments → Submit Assignment → upload file
6. **Quizzes** — active quizzes → attempt quiz → submit
7. **Fees** → Pay Fees → enter amount → complete payment → download receipt PDF
8. **Timetable** — today's class schedule
9. **Notices** — college announcements
10. **Download Result PDF** → Profile section → Result PDF button

---

### 7. Lab Staff
Login: `lab_suresh_vitm / Lab@1234`

- View active sessions happening right now
- Full today's schedule across all rooms
- Classroom list with capacity
- Raise a help desk ticket

---

## Registration Flow (Invite-based)

1. Login as **College Admin**
2. Go to Manage → Invite Links → Create Invite Link → copy the link
3. Open the link in a new browser / incognito
4. Fill the registration form and submit
5. Back as Admin → Manage → Requests → find the pending request
6. Click Convert → prefilled student form opens → save
7. New student account is created with generated roll number

---

## Substitution Flow

1. Login as **HOD** (`hod_rajesh_vitm`)
2. Sidebar → Substitutions
3. Pick a timetable slot (e.g. Data Structures - MON)
4. Pick a substitute faculty from the dropdown
5. Set date → Submit
6. Logout → Login as the **substitute faculty**
7. Go to My Subjects → the substituted subject appears
8. Click Attendance → mark attendance → Save

---

## College Branding / Theme

1. Login as **College Admin**
2. Dashboard → My Profile (sidebar) → Dashboard Colors section
3. Click a preset swatch (Ocean / Royal / Forest / Crimson)
4. Or enter custom hex values for Primary, Accent, Sidebar colors
5. Click Save Colors
6. Page reloads — sidebar and accent colors update across all dashboards for that college

---

## PDF Reports

| Report | How to access |
|--------|--------------|
| Attendance report | Admin → Reports → Export Attendance PDF |
| Payment report | Admin → Reports → Export Payment PDF |
| Result report | Admin → Reports → Export Result PDF |
| Student result | Student dashboard → Profile → Result PDF |
| Payment receipt | Student dashboard → Fees → Receipt |

---

## Notes

- `DEBUG=True` in settings — attendance time-lock is disabled for testing. Faculty can mark attendance at any time.
- Re-run `python seed_data.py` at any time to reset all demo data to a clean state.
- Django admin panel: http://localhost:8000/admin/ (login with `superadmin / Super@1234`)
