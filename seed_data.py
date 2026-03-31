"""
EduTrack seed script — VITM Demo
Run with: python seed_data.py

Creates:
  1 college · 1 superuser · 1 college admin · 1 principal
  4 departments · 4 HODs · 8 faculty · 100 students · 1 lab staff
  subjects · classrooms · timetable slots · attendance sessions
  marks · results · fees · announcements · substitution demo
"""

import os, random, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studentmanagementsystem.settings")
django.setup()

from datetime import date, time, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from students.models import (
    Announcement, FeeStructure, Assignment, Attendance, AttendanceSession,
    Address, Classroom, College, Department, EmergencyContact, Exam,
    Faculty, FacultyAvailability, FacultySubject, Fee, HelpDeskTicket,
    HOD, HODApproval, Marks, Parent, Principal, RegistrationInvite,
    Result, Student, StudentProfile, Subject, Substitution, Timetable, UserRole,
)

print("=" * 55)
print("  EduTrack Seed — VITM Demo")
print("=" * 55)

# ── 1. Clean slate ────────────────────────────────────────
print("\n[1] Cleaning old demo data...")
College.objects.filter(Q(code="VITM") | Q(name__icontains="Vidyalankar")).delete()
User.objects.filter(
    Q(username__startswith="fac_") | Q(username__startswith="stu_") |
    Q(username__startswith="hod_") | Q(username__startswith="lab_") |
    Q(username__in=["admin_vitm","principal_vitm","lab_suresh_vitm","superadmin"])
).delete()
# Clean orphaned profiles (from partial previous runs)
from students.models import StudentProfile as SP
SP.objects.filter(user__isnull=True).delete()

# ── 2. College ────────────────────────────────────────────
print("[2] Creating college...")
college = College.objects.create(
    code="VITM", name="Vidyalankar Institute of Technology",
    city="Mumbai", state="Maharashtra",
    email="info@vitm.edu.in", website="https://vitm.edu.in"
)

# ── 3. Superuser ──────────────────────────────────────────
if not User.objects.filter(username="superadmin").exists():
    User.objects.create_superuser("superadmin", "superadmin@edutrack.in", "Super@1234",
                                   first_name="Super", last_name="Admin")
    print("  [OK] Superuser: superadmin / Super@1234")

# ── 4. College Admin ──────────────────────────────────────
admin_user = User.objects.create_user(
    "admin_vitm", "admin@vitm.edu.in", "Admin@1234",
    first_name="Sanjay", last_name="Deshmukh"
)
UserRole.objects.create(user=admin_user, role=1, college=college)

# ── 5. Principal ──────────────────────────────────────────
principal_user = User.objects.create_user(
    "principal_vitm", "principal@vitm.edu.in", "Principal@1234",
    first_name="Aruna", last_name="Rao"
)
UserRole.objects.create(user=principal_user, role=6, college=college)
Principal.objects.create(
    user=principal_user, college=college,
    employee_id="PRN-VIT-001", phone_number="9820012345",
    qualification="Ph.D Physics", experience_years=25
)

# ── 6. Departments ────────────────────────────────────────
print("[3] Creating departments...")
dept_data = [
    ("Computer Science Engineering", "CSE"),
    ("Information Science",          "ISE"),
    ("Electronics & Communication",  "ECE"),
    ("Mechanical Engineering",       "ME"),
]
departments = []
for name, code in dept_data:
    dept = Department.objects.create(name=name, code=code, college=college, established_year=2005)
    departments.append(dept)
    for sem in range(1, 9):
        FeeStructure.objects.get_or_create(
            college=college, department=dept, semester=sem,
            defaults={"total_fees": 85000.0}
        )

# ── 7. Classrooms ─────────────────────────────────────────
print("[4] Creating classrooms...")
rooms = []
for i in range(1, 9):
    r = Classroom.objects.create(college=college, room_number=f"R{i:03d}", capacity=60)
    rooms.append(r)

# ── 8. HODs (role=2, also Faculty records so they can teach) ─
print("[5] Creating HODs + Faculty...")
hod_data = [
    ("Rajesh",  "Khanna",  "CSE", "HOD-CSE-001"),
    ("Meera",   "Nair",    "ISE", "HOD-ISE-001"),
    ("Vikram",  "Seth",    "ECE", "HOD-ECE-001"),
    ("Homi",    "Bhabha",  "ME",  "HOD-ME-001"),
]
hod_objs = {}
for fn, ln, dcode, emp_id in hod_data:
    dept = next(d for d in departments if d.code == dcode)
    uname = f"hod_{fn.lower()}_vitm"
    u = User.objects.create_user(uname, f"{fn.lower()}.hod@vitm.edu.in", "Hod@1234",
                                  first_name=fn, last_name=ln)
    UserRole.objects.create(user=u, role=2, college=college)
    hod = HOD.objects.create(user=u, employee_id=emp_id, department=dept,
                              phone_number="9800000001", qualification="Ph.D", experience_years=15)
    # Also create Faculty record so HOD can be assigned subjects / mark attendance
    fac = Faculty.objects.create(user=u, employee_id=f"FAC-{emp_id}", department=dept,
                                  designation="Professor & HOD", qualification="Ph.D",
                                  experience_years=15, phone_number="9800000001")
    hod_objs[dcode] = (hod, fac)

# ── 9. Regular Faculty (role=3) ───────────────────────────
fac_data = [
    ("Sunita",  "Sharma",  "CSE", "FAC-CSE-002"),
    ("Amit",    "Verma",   "CSE", "FAC-CSE-003"),
    ("Suresh",  "Raina",   "ISE", "FAC-ISE-002"),
    ("Anjali",  "Gupta",   "ECE", "FAC-ECE-002"),
    ("Rahul",   "Dravid",  "ECE", "FAC-ECE-003"),
    ("Vijay",   "Kumar",   "ME",  "FAC-ME-002"),
    ("Priya",   "Menon",   "CSE", "FAC-CSE-004"),
    ("Deepak",  "Joshi",   "ISE", "FAC-ISE-003"),
]
faculty_by_dept = {d.code: [] for d in departments}
for fn, ln, dcode, emp_id in fac_data:
    dept = next(d for d in departments if d.code == dcode)
    uname = f"fac_{fn.lower()}_vitm"
    u = User.objects.create_user(uname, f"{fn.lower()}@vitm.edu.in", "Faculty@1234",
                                  first_name=fn, last_name=ln)
    UserRole.objects.create(user=u, role=3, college=college)
    fac = Faculty.objects.create(user=u, employee_id=emp_id, department=dept,
                                  designation="Assistant Professor", qualification="M.Tech",
                                  experience_years=5, phone_number="9810000001")
    faculty_by_dept[dcode].append(fac)

# Add HOD faculty records to the pool too
for dcode, (hod, fac) in hod_objs.items():
    faculty_by_dept[dcode].insert(0, fac)

# ── 10. Subjects (semesters 2 & 4 per dept) ──────────────
print("[6] Creating subjects & assigning faculty...")
SUBJECT_NAMES = {
    "CSE": ["Data Structures", "Algorithms", "DBMS", "OS", "Computer Networks",
            "Software Engineering", "Machine Learning", "Web Technologies"],
    "ISE": ["Information Systems", "Data Mining", "Cloud Computing", "Cyber Security",
            "Big Data", "IoT", "Python Programming", "Network Security"],
    "ECE": ["Digital Electronics", "Signals & Systems", "VLSI Design", "Microprocessors",
            "Communication Systems", "Embedded Systems", "Antenna Theory", "Control Systems"],
    "ME":  ["Engineering Mechanics", "Thermodynamics", "Fluid Mechanics", "Manufacturing",
            "Machine Design", "Heat Transfer", "CAD/CAM", "Industrial Engineering"],
}
subjects_by_dept_sem = {}  # {(dept_code, sem): [subjects]}
for dept in departments:
    names = SUBJECT_NAMES[dept.code]
    for sem_idx, sem in enumerate([2, 4]):
        sem_subjects = []
        for i in range(4):  # 4 subjects per semester
            name = names[sem_idx * 4 + i]
            code = f"{dept.code}{sem}0{i+1}"
            sub, _ = Subject.objects.get_or_create(
                code=code,
                defaults={"name": name, "department": dept, "semester": sem, "weekly_hours": 4}
            )
            sem_subjects.append(sub)
            # Assign a faculty
            fac_pool = faculty_by_dept[dept.code]
            assigned_fac = fac_pool[i % len(fac_pool)]
            FacultySubject.objects.get_or_create(faculty=assigned_fac, subject=sub)
        subjects_by_dept_sem[(dept.code, sem)] = sem_subjects

# ── 11. Timetable slots ───────────────────────────────────
print("[7] Creating timetable slots...")
DAYS = ["MON", "TUE", "WED", "THU", "FRI"]
SLOTS = [
    (time(9, 0),  time(10, 0)),
    (time(10, 0), time(11, 0)),
    (time(11, 15),time(12, 15)),
    (time(12, 15),time(13, 15)),
]
room_idx = 0
for dept in departments:
    for sem in [2, 4]:
        subs = subjects_by_dept_sem.get((dept.code, sem), [])
        for s_idx, sub in enumerate(subs):
            fac_sub = FacultySubject.objects.filter(subject=sub).first()
            if not fac_sub:
                continue
            day = DAYS[s_idx % len(DAYS)]
            slot_time = SLOTS[s_idx % len(SLOTS)]
            room = rooms[room_idx % len(rooms)]
            room_idx += 1
            Timetable.objects.get_or_create(
                subject=sub, day_of_week=day,
                defaults={
                    "faculty": fac_sub.faculty,
                    "classroom": room,
                    "start_time": slot_time[0],
                    "end_time": slot_time[1],
                }
            )

# ── 12. Exams ─────────────────────────────────────────────
print("[8] Creating exams...")
exam_mid = Exam.objects.create(college=college, name="Mid Semester Exam", semester=2,
                                start_date=date.today() - timedelta(days=30),
                                end_date=date.today() - timedelta(days=25),
                                created_by=admin_user)
exam_end = Exam.objects.create(college=college, name="End Semester Exam", semester=2,
                                start_date=date.today() - timedelta(days=10),
                                end_date=date.today() - timedelta(days=5),
                                created_by=admin_user)

# ── 13. Students (100) ────────────────────────────────────
print("[9] Creating 100 students...")
FIRST = ["Aarav","Vihaan","Aditya","Arjun","Ishaan","Sai","Ananya","Diya","Pari","Myra",
         "Saanvi","Riya","Kavya","Zara","Rohan","Kiran","Neha","Pooja","Rahul","Priya"]
LAST  = ["Patel","Sharma","Gupta","Mehta","Iyer","Nair","Khan","Singh","Reddy","Deshmukh"]

students_created = []
for i in range(1, 101):
    fn = FIRST[i % len(FIRST)]
    ln = LAST[i % len(LAST)]
    dept = departments[i % len(departments)]
    adm_year = random.choice([2021, 2022, 2023])
    sem = min((2024 - adm_year) * 2, 8)
    # Snap to a seeded semester (2 or 4)
    sem = 4 if sem >= 4 else 2

    roll = f"{adm_year}-VITM-{dept.code}-{i:03d}"
    uname = f"stu_{i}_vitm"
    u = User.objects.create_user(uname, f"student{i}@vitm.edu.in", "Student@1234",
                                  first_name=fn, last_name=ln)
    UserRole.objects.create(user=u, role=4, college=college)
    student = Student.objects.create(
        user=u, roll_number=roll, department=dept,
        admission_year=adm_year, current_semester=sem, status="ACTIVE"
    )
    # Fee
    total = 85000.0
    paid = random.choice([0.0, 42500.0, 85000.0])
    status = "PAID" if paid == total else ("PARTIAL" if paid > 0 else "PENDING")
    Fee.objects.create(student=student, total_amount=total, paid_amount=paid, status=status)

    # Profile
    StudentProfile.objects.create(
        user=u, phone_number=f"98{i:08d}",
        date_of_birth=date(2000 + (i % 5), (i % 12) + 1, (i % 28) + 1),
        gender="Male" if i % 2 == 0 else "Female",
        nationality="Indian", blood_group=random.choice(["A+","B+","O+","AB+"]),
        category="General",
        aadhaar_number=f"{i:012d}",
        inter_college_name="Demo Junior College",
        inter_passed_year=2020 + (i % 3),
        inter_percentage=round(60 + (i % 35), 2),
        school_name="Demo High School",
        school_passed_year=2018 + (i % 3),
        school_percentage=round(65 + (i % 30), 2),
    )
    students_created.append(student)

# ── 14. Attendance sessions (past 10 days) ────────────────
print("[10] Seeding attendance sessions...")
for dept in departments:
    for sem in [2, 4]:
        subs = subjects_by_dept_sem.get((dept.code, sem), [])
        dept_students = [s for s in students_created if s.department == dept and s.current_semester == sem]
        if not dept_students:
            continue
        for sub in subs:
            fac_sub = FacultySubject.objects.filter(subject=sub).first()
            if not fac_sub:
                continue
            for day_offset in range(1, 11):  # last 10 days
                session_date = date.today() - timedelta(days=day_offset)
                if session_date.weekday() >= 5:  # skip weekends
                    continue
                sess, created = AttendanceSession.objects.get_or_create(
                    subject=sub, faculty=fac_sub.faculty, date=session_date
                )
                if created:
                    for student in dept_students:
                        Attendance.objects.get_or_create(
                            session=sess, student=student,
                            defaults={
                                "status": random.choices(
                                    ["PRESENT", "ABSENT", "LATE"],
                                    weights=[75, 20, 5]
                                )[0],
                                "marked_by": fac_sub.faculty.user
                            }
                        )

# ── 15. Marks & Results ───────────────────────────────────
print("[11] Seeding marks & results...")
for student in students_created[:30]:  # first 30 students get results
    subs = subjects_by_dept_sem.get((student.department.code, 2), [])
    total_marks = 0
    for sub in subs:
        m = random.randint(55, 98)
        Marks.objects.get_or_create(
            student=student, subject=sub, exam=exam_end,
            defaults={"marks_obtained": m, "max_marks": 100}
        )
        total_marks += m
    if subs:
        pct = round(total_marks / (len(subs) * 100) * 100, 2)
        gpa = round(4.0 * pct / 100 + 6.0 * (1 - pct / 100), 2)
        gpa = min(10.0, max(0.0, round(pct / 10, 1)))
        Result.objects.get_or_create(
            student=student, semester=2,
            defaults={"total_marks": total_marks, "percentage": pct, "gpa": gpa}
        )

# ── 16. Lab Staff ─────────────────────────────────────────
print("[12] Creating lab staff...")
lab_user = User.objects.create_user(
    "lab_suresh_vitm", "suresh.lab@vitm.edu.in", "Lab@1234",
    first_name="Suresh", last_name="Mistry"
)
UserRole.objects.create(user=lab_user, role=5, college=college)

# ── 17. Announcements ─────────────────────────────────────
print("[13] Creating announcements...")
Announcement.objects.create(
    college=college, title="Welcome to VITM Portal",
    message="All students and faculty can now access the EduTrack portal. Contact admin for any issues.",
    created_by=admin_user
)
Announcement.objects.create(
    college=college, title="End Semester Exam Schedule Released",
    message="End semester exams for Semester 2 are scheduled. Check the Exams section for details.",
    created_by=admin_user
)

# ── 18. Demo Substitution ─────────────────────────────────
print("[14] Creating demo substitution...")
cse_slot = Timetable.objects.filter(subject__department__code="CSE").first()
cse_sub_fac = faculty_by_dept["CSE"][1] if len(faculty_by_dept["CSE"]) > 1 else None
if cse_slot and cse_sub_fac and cse_slot.faculty != cse_sub_fac:
    Substitution.objects.get_or_create(
        timetable_slot=cse_slot,
        date=date.today() + timedelta(days=1),
        defaults={
            "original_faculty": cse_slot.faculty,
            "substitute_faculty": cse_sub_fac,
        }
    )

# ── 19. Help Desk ticket ──────────────────────────────────
HelpDeskTicket.objects.create(
    college=college, name="Test Student", email="student1@vitm.edu.in",
    subject="Cannot login to portal", issue_type="ACCESS",
    description="I am unable to login with my credentials.", status="OPEN"
)

print("\n" + "=" * 55)
print("  Seed complete! Test credentials:")
print("=" * 55)
print(f"  Superadmin  : superadmin        / Super@1234")
print(f"  College Admin: admin_vitm       / Admin@1234")
print(f"  Principal   : principal_vitm    / Principal@1234")
print(f"  HOD (CSE)   : hod_rajesh_vitm   / Hod@1234")
print(f"  HOD (ISE)   : hod_meera_vitm    / Hod@1234")
print(f"  HOD (ECE)   : hod_vikram_vitm   / Hod@1234")
print(f"  HOD (ME)    : hod_homi_vitm     / Hod@1234")
print(f"  Faculty     : fac_sunita_vitm   / Faculty@1234")
print(f"  Faculty     : fac_amit_vitm     / Faculty@1234")
print(f"  Faculty     : fac_priya_vitm    / Faculty@1234")
print(f"  Lab Staff   : lab_suresh_vitm   / Lab@1234")
print(f"  Student 1   : stu_1_vitm        / Student@1234")
print(f"  Student 2   : stu_2_vitm        / Student@1234")
print(f"  Student 50  : stu_50_vitm       / Student@1234")
print("=" * 55)
