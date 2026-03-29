"""
EduTrack seed script.

Run with:
    python seed_data.py

Creates:
- 1 college
- 1 superuser
- 1 principal
- 1 college admin role (the superuser also remains global admin through Django)
- 3 departments
- 1 HOD
- 2 faculty
- 3 students
- 1 lab staff
- subjects, timetable, attendance, marks, results, fees, announcements
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studentmanagementsystem.settings")
django.setup()

from datetime import date, time, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from students.models import (
    Announcement,
    Assignment,
    Attendance,
    AttendanceSession,
    Address,
    Classroom,
    College,
    Department,
    EmergencyContact,
    Exam,
    Faculty,
    FacultyAvailability,
    FacultySubject,
    Fee,
    HelpDeskTicket,
    HOD,
    HODApproval,
    Marks,
    Parent,
    Principal,
    RegistrationInvite,
    Result,
    Student,
    StudentProfile,
    Subject,
    Timetable,
    UserRole,
)


print("Starting seed...")

User.objects.filter(
    username__in=[
        "admin_et",
        "college_admin_svce",
        "principal_svce",
        "hod_cse",
        "faculty_raj",
        "faculty_priya",
        "student_arjun",
        "student_meena",
        "student_kiran",
        "lab_suresh",
    ]
).delete()

college, _ = College.objects.get_or_create(
    code="SVCE",
    defaults={
        "name": "Sri Venkateswara College of Engineering",
        "city": "Tirupati",
        "state": "Andhra Pradesh",
    },
)
print(f"  [OK] College: {college}")

cse, _ = Department.objects.get_or_create(
    name="Computer Science & Engineering",
    code="CSE",
    defaults={"college": college, "established_year": 2005},
)
ece, _ = Department.objects.get_or_create(
    name="Electronics & Communication",
    code="ECE",
    defaults={"college": college, "established_year": 2006},
)
mech, _ = Department.objects.get_or_create(
    name="Mechanical Engineering",
    code="MECH",
    defaults={"college": college, "established_year": 2004},
)
for dept in (cse, ece, mech):
    if dept.college_id != college.id:
        dept.college = college
        dept.save(update_fields=["college"])
print(f"  [OK] Departments: {cse.code}, {ece.code}, {mech.code}")

admin_user = User.objects.create_superuser(
    username="admin_et",
    password="Admin@1234",
    email="admin@edutrack.in",
    first_name="System",
    last_name="Admin",
)
print("  [OK] Super Admin: admin_et")

college_admin_user = User.objects.create_user(
    username="college_admin_svce",
    password="College@1234",
    email="college.admin@edutrack.in",
    first_name="College",
    last_name="Admin",
)
UserRole.objects.create(user=college_admin_user, role=1, college=college)
print("  [OK] College Admin: college_admin_svce")

principal_user = User.objects.create_user(
    username="principal_svce",
    password="Principal@1234",
    email="principal@edutrack.in",
    first_name="Dr. Anil",
    last_name="Kumar",
)
UserRole.objects.create(user=principal_user, role=6, college=college)
Principal.objects.create(
    user=principal_user,
    college=college,
    employee_id="PRN001",
    phone_number="9876500100",
    qualification="Ph.D Administration",
    experience_years=20,
)
print("  [OK] Principal: principal_svce")

hod_user = User.objects.create_user(
    username="hod_cse",
    password="Hod@1234",
    email="hod.cse@edutrack.in",
    first_name="Dr. Ramesh",
    last_name="Iyer",
)
UserRole.objects.create(user=hod_user, role=2, college=college)
HOD.objects.create(
    user=hod_user,
    employee_id="HOD001",
    department=cse,
    phone_number="9876543210",
    qualification="Ph.D Computer Science",
    experience_years=18,
)
print("  [OK] HOD: hod_cse")

fac1_user = User.objects.create_user(
    username="faculty_raj",
    password="Faculty@1234",
    email="raj@edutrack.in",
    first_name="Rajesh",
    last_name="Kumar",
)
UserRole.objects.create(user=fac1_user, role=3, college=college)
fac1 = Faculty.objects.create(
    user=fac1_user,
    employee_id="FAC001",
    department=cse,
    designation="Assistant Professor",
    qualification="M.Tech CSE",
    experience_years=6,
    phone_number="9876500001",
)

fac2_user = User.objects.create_user(
    username="faculty_priya",
    password="Faculty@1234",
    email="priya@edutrack.in",
    first_name="Priya",
    last_name="Sharma",
)
UserRole.objects.create(user=fac2_user, role=3, college=college)
fac2 = Faculty.objects.create(
    user=fac2_user,
    employee_id="FAC002",
    department=cse,
    designation="Associate Professor",
    qualification="Ph.D CSE",
    experience_years=12,
    phone_number="9876500002",
)
print("  [OK] Faculty: faculty_raj, faculty_priya")

s1_user = User.objects.create_user(
    username="student_arjun",
    password="Student@1234",
    email="arjun@edutrack.in",
    first_name="Arjun",
    last_name="Mehta",
)
UserRole.objects.create(user=s1_user, role=4, college=college)
s1 = Student.objects.create(
    user=s1_user,
    roll_number="2021-SVCE-CSE-001",
    department=cse,
    admission_year=2021,
    current_semester=4,
    status="ACTIVE",
)
Fee.objects.create(student=s1, total_amount=45000, paid_amount=45000, status="PAID")

s2_user = User.objects.create_user(
    username="student_meena",
    password="Student@1234",
    email="meena@edutrack.in",
    first_name="Meena",
    last_name="Krishnan",
)
UserRole.objects.create(user=s2_user, role=4, college=college)
s2 = Student.objects.create(
    user=s2_user,
    roll_number="2020-SVCE-ECE-001",
    department=ece,
    admission_year=2020,
    current_semester=6,
    status="ACTIVE",
)
Fee.objects.create(student=s2, total_amount=45000, paid_amount=22500, status="PARTIAL")

s3_user = User.objects.create_user(
    username="student_kiran",
    password="Student@1234",
    email="kiran@edutrack.in",
    first_name="Kiran",
    last_name="Patil",
)
UserRole.objects.create(user=s3_user, role=4, college=college)
s3 = Student.objects.create(
    user=s3_user,
    roll_number="2023-SVCE-MECH-001",
    department=mech,
    admission_year=2023,
    current_semester=2,
    status="ACTIVE",
)
Fee.objects.create(student=s3, total_amount=45000, paid_amount=0, status="PENDING")
print("  [OK] Students: student_arjun, student_meena, student_kiran")

lab_user = User.objects.create_user(
    username="lab_suresh",
    password="Lab@1234",
    email="suresh@edutrack.in",
    first_name="Suresh",
    last_name="Nair",
)
UserRole.objects.create(user=lab_user, role=5, college=college)
print("  [OK] Lab Staff: lab_suresh")

sub1, _ = Subject.objects.get_or_create(name="Data Structures", code="CSE401", defaults={"department": cse, "semester": 4})
sub2, _ = Subject.objects.get_or_create(name="Operating Systems", code="CSE402", defaults={"department": cse, "semester": 4})
sub3, _ = Subject.objects.get_or_create(name="Database Management", code="CSE403", defaults={"department": cse, "semester": 4})
FacultySubject.objects.get_or_create(faculty=fac1, subject=sub1)
FacultySubject.objects.get_or_create(faculty=fac1, subject=sub2)
FacultySubject.objects.get_or_create(faculty=fac2, subject=sub3)
print("  [OK] Subjects assigned")

room, _ = Classroom.objects.get_or_create(room_number="CS-101", defaults={"capacity": 60})

today_weekday = date.today().weekday()
day_map = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT", 6: "MON"}
today_code = day_map[today_weekday]

FacultyAvailability.objects.get_or_create(faculty=fac1, day_of_week=today_code, start_time=time(9, 0), end_time=time(10, 0))
FacultyAvailability.objects.get_or_create(faculty=fac1, day_of_week=today_code, start_time=time(10, 0), end_time=time(11, 0))
FacultyAvailability.objects.get_or_create(faculty=fac2, day_of_week=today_code, start_time=time(11, 0), end_time=time(12, 0))

Timetable.objects.get_or_create(subject=sub1, faculty=fac1, day_of_week=today_code, defaults={"start_time": time(9, 0), "end_time": time(10, 0), "classroom": room})
Timetable.objects.get_or_create(subject=sub2, faculty=fac1, day_of_week=today_code, defaults={"start_time": time(10, 0), "end_time": time(11, 0), "classroom": room})
Timetable.objects.get_or_create(subject=sub3, faculty=fac2, day_of_week=today_code, defaults={"start_time": time(11, 0), "end_time": time(12, 0), "classroom": room})

for i in range(10):
    day = date.today() - timedelta(days=i + 1)
    for subj, fac in [(sub1, fac1), (sub2, fac1), (sub3, fac2)]:
        sess, created = AttendanceSession.objects.get_or_create(subject=subj, faculty=fac, date=day)
        if created:
            status = "PRESENT" if i % 5 != 0 else "ABSENT"
            Attendance.objects.get_or_create(session=sess, student=s1, defaults={"status": status, "marked_by": fac.user})

exam, _ = Exam.objects.get_or_create(
    name="Mid Semester Exam",
    semester=4,
    college=college,
    defaults={
        "start_date": date.today() - timedelta(days=30),
        "end_date": date.today() - timedelta(days=28),
        "created_by": admin_user,
    },
)
for subj, obtained in [(sub1, 82), (sub2, 76), (sub3, 91)]:
    Marks.objects.get_or_create(
        student=s1,
        subject=subj,
        exam=exam,
        defaults={"marks_obtained": obtained, "max_marks": 100, "grade": "A" if obtained >= 70 else "B+"},
    )

Result.objects.get_or_create(student=s1, semester=3, defaults={"gpa": 8.4, "total_marks": 520, "percentage": 74.3})
Result.objects.get_or_create(student=s1, semester=2, defaults={"gpa": 7.9, "total_marks": 490, "percentage": 70.0})

StudentProfile.objects.update_or_create(
    user=s1_user,
    defaults={
        "first_name": "Arjun",
        "last_name": "Mehta",
        "date_of_birth": date(2003, 4, 16),
        "gender": "Male",
        "phone_number": "9876501111",
        "aadhaar_number": "123412341234",
        "inter_college_name": "SV Junior College",
        "inter_passed_year": 2021,
        "inter_percentage": 91.2,
        "school_name": "Little Flower High School",
        "school_passed_year": 2019,
        "school_percentage": 92.4,
        "blood_group": "B+",
        "nationality": "Indian",
        "category": "OC",
    },
)
Address.objects.update_or_create(
    user=s1_user,
    city="Tirupati",
    defaults={"street": "12-4-8, Lake View Colony", "state": "Andhra Pradesh", "pincode": "517501", "country": "India"},
)
Parent.objects.update_or_create(
    user=s1_user,
    parent_type="FATHER",
    defaults={"name": "Rohit Mehta", "phone_number": "9876502222", "email": "rohit.mehta@example.com", "occupation": "Engineer"},
)
EmergencyContact.objects.update_or_create(
    user=s1_user,
    name="Sneha Mehta",
    defaults={"relation": "Sister", "phone_number": "9876503333"},
)

Assignment.objects.get_or_create(
    subject=sub1,
    title="Linked List Practice Set",
    created_by=fac1_user,
    defaults={
        "description": "Solve the linked list problems and upload a short PDF with explanations.",
        "deadline": timezone.now() + timedelta(days=5),
    },
)

Announcement.objects.get_or_create(
    title="End Semester Exam Schedule Released",
    college=college,
    defaults={"message": "End semester exams begin from 10th November 2026. Check the portal for hall tickets.", "created_by": admin_user},
)
Announcement.objects.get_or_create(
    title="Fee Payment Deadline - 5th November",
    college=college,
    defaults={"message": "Last date for semester fee payment is 5th November 2026. Late fee applicable after due date.", "created_by": admin_user},
)
Announcement.objects.get_or_create(
    title="Internal Assessment Marks Published",
    college=college,
    defaults={"message": "IA marks for Sem 3 and Sem 5 are now available on the student portal.", "created_by": admin_user},
)

HODApproval.objects.get_or_create(
    requested_by=fac1_user,
    department=cse,
    approval_type="LEAVE",
    status="PENDING",
    defaults={"description": "Requesting 2 days leave for attending a national conference on AI/ML at IIT Bombay."},
)

RegistrationInvite.objects.get_or_create(
    college=college,
    invited_email="freshstudent@edutrack.in",
    defaults={
        "department": cse,
        "admission_year": 2026,
        "current_semester": 1,
        "created_by": college_admin_user,
    },
)

HelpDeskTicket.objects.get_or_create(
    college=college,
    email="support.student@edutrack.in",
    subject="Need invite link for onboarding",
    defaults={
        "name": "Support Student",
        "issue_type": "ACCESS",
        "description": "Student could not find the onboarding link and needs access guidance.",
        "status": "OPEN",
    },
)

print("\nSeed complete. Accounts ready:\n")
print("  Superuser: admin_et / Admin@1234")
print("  College Admin: college_admin_svce / College@1234")
print("  Principal: principal_svce / Principal@1234")
print("  HOD: hod_cse / Hod@1234")
print("  Faculty: faculty_raj / Faculty@1234")
print("  Faculty: faculty_priya / Faculty@1234")
print("  Student: student_arjun / Student@1234")
print("  Student: student_meena / Student@1234")
print("  Student: student_kiran / Student@1234")
print("  Lab Staff: lab_suresh / Lab@1234")
