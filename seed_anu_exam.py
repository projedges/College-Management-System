"""
seed_anu_exam.py
================
Seeds the Examination Department for Annamacharya University (ANU):
  1. Creates ExamStaff: COE + Deputy COE + Section Officers (per dept)
  2. Creates EvaluationScheme
  3. Creates ExamTypes (Mid Sem, End Sem, Supplementary)
  4. Creates Exams for active semesters (1, 3, 5)
  5. Creates ExamSchedule entries per subject
  6. Enters Marks for all ANU students
  7. Computes ExamResult + Result (SGPA/CGPA)
  8. Publishes all results

Run: python seed_anu_exam.py
"""

import os, random, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studentmanagementsystem.settings')
django.setup()

from datetime import date, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from students.models import (
    College, Department, Student, Faculty, Subject, Exam, Marks, Result,
    ExamResult, ExamStaff, ExamType, EvaluationScheme, ExamSchedule,
    InternalMark, FacultySubject, UserRole, GraceMarksRule,
)

random.seed(99)

# ── helpers ───────────────────────────────────────────────────────────────────

def grade_from_pct(pct):
    if pct >= 90: return 'O'
    if pct >= 80: return 'A+'
    if pct >= 70: return 'A'
    if pct >= 60: return 'B+'
    if pct >= 55: return 'B'
    if pct >= 50: return 'C'
    if pct >= 40: return 'P'
    return 'F'

def grade_point(grade):
    return {'O':10,'A+':9,'A':8,'B+':7,'B':6,'C':5,'P':4,'F':0}.get(grade, 0)

def compute_sgpa(marks_list):
    tcp, tc = 0.0, 0
    for m in marks_list:
        cr = getattr(m.subject, 'credits', None) or 3
        gp = grade_point(m.grade or grade_from_pct(
            round(m.marks_obtained / m.max_marks * 100, 1) if m.max_marks else 0
        ))
        tcp += cr * gp
        tc += cr
    return (round(tcp / tc, 2) if tc > 0 else 0.0), tc

def rand_marks(base=72, spread=18):
    return max(25, min(100, base + random.randint(-spread, spread)))

# ── 1. Get ANU college ────────────────────────────────────────────────────────

print("=" * 60)
print("  ANU Examination Department Seed")
print("=" * 60)

try:
    college = College.objects.get(code='ANU')
except College.DoesNotExist:
    print("ERROR: ANU college not found. Run the ANU seed first.")
    exit(1)

print(f"\nCollege: {college.name}")
departments = list(Department.objects.filter(college=college).order_by('code'))
print(f"Departments: {[d.code for d in departments]}")

# ── 2. Create Exam Staff ──────────────────────────────────────────────────────

print("\n[1] Creating Exam Staff...")

staff_data = [
    ('anu_coe',         'Venkata',   'Rao',       'coe@anu.edu.in',         'COE',              'COE-ANU-001', '9876500001'),
    ('anu_deputy_coe',  'Lakshmi',   'Devi',      'deputy.coe@anu.edu.in',  'DEPUTY_COE',       'COE-ANU-002', '9876500002'),
    ('anu_exam_coord',  'Suresh',    'Babu',      'coord@anu.edu.in',       'COORDINATOR',      'COE-ANU-003', '9876500003'),
    ('anu_section_cse', 'Ramaiah',   'Naidu',     'section.cse@anu.edu.in', 'SECTION_OFFICER',  'COE-ANU-004', '9876500004'),
    ('anu_section_ece', 'Padmavathi','Reddy',     'section.ece@anu.edu.in', 'SECTION_OFFICER',  'COE-ANU-005', '9876500005'),
    ('anu_valuation',   'Krishna',   'Murthy',    'valuation@anu.edu.in',   'VALUATION_OFFICER','COE-ANU-006', '9876500006'),
    ('anu_data_entry',  'Srinivas',  'Prasad',    'data@anu.edu.in',        'DATA_ENTRY',       'COE-ANU-007', '9876500007'),
]

exam_staff_objs = {}
for uname, fn, ln, email, role, emp_id, phone in staff_data:
    with transaction.atomic():
        user, created = User.objects.get_or_create(
            username=uname,
            defaults={'first_name': fn, 'last_name': ln, 'email': email, 'is_active': True}
        )
        if created:
            user.set_password('Exam@1234')
            user.save()

        es, _ = ExamStaff.objects.get_or_create(
            user=user,
            defaults={
                'college': college,
                'exam_role': role,
                'employee_id': emp_id,
                'phone_number': phone,
                'is_active': True,
            }
        )
        # Assign section officers to specific departments
        if role == 'SECTION_OFFICER':
            if 'cse' in uname:
                depts = Department.objects.filter(college=college, code__in=['CSE', 'ISE'])
            else:
                depts = Department.objects.filter(college=college, code__in=['ECE', 'MECH', 'CIVIL'])
            es.departments.set(depts)

        UserRole.objects.update_or_create(
            user=user,
            defaults={'role': 7, 'college': college}
        )
        exam_staff_objs[uname] = es
        status = "created" if created else "exists"
        print(f"  [{status}] {uname} | {role}")

coe_user = exam_staff_objs['anu_coe'].user

# ── 3. Evaluation Scheme ──────────────────────────────────────────────────────

print("\n[2] Creating Evaluation Scheme...")
with transaction.atomic():
    scheme, created = EvaluationScheme.objects.get_or_create(
        college=college,
        department=None,
        name='ANU Standard Scheme',
        defaults={
            'description': 'ANU standard: CIE 30 + SEE 70',
            'cie_count': 2,
            'cie_best_of': 2,
            'cie_max_per_test': 15,
            'cie_total_max': 30,
            'see_max': 100,
            'see_scaled_to': 70,
            'see_passing_min': 28,
            'overall_passing_min': 40,
            'is_active': True,
        }
    )
    print(f"  {'created' if created else 'exists'}: {scheme.name}")

# ── 4. Exam Types ─────────────────────────────────────────────────────────────

print("\n[3] Creating Exam Types...")
exam_type_data = [
    ('Mid Semester Examination',  'CIE'),
    ('End Semester Examination',  'SEE'),
    ('Supplementary Examination', 'SEE'),
]
exam_types = {}
for name, category in exam_type_data:
    et, created = ExamType.objects.get_or_create(
        college=college, name=name,
        defaults={'category': category, 'max_marks': 100, 'passing_marks': 40, 'is_active': True}
    )
    exam_types[name] = et
    print(f"  {'created' if created else 'exists'}: {name}")

# ── 5. Create Exams ───────────────────────────────────────────────────────────

print("\n[4] Creating Exams...")
today = date.today()

# Semesters active in ANU: 1, 3, 5 (based on seeded students)
exam_defs = [
    ('Mid Semester Exam — Sem 1',  1, -45, 5, 'Mid Semester Examination'),
    ('End Semester Exam — Sem 1',  1, -10, 7, 'End Semester Examination'),
    ('Mid Semester Exam — Sem 3',  3, -45, 5, 'Mid Semester Examination'),
    ('End Semester Exam — Sem 3',  3, -10, 7, 'End Semester Examination'),
    ('Mid Semester Exam — Sem 5',  5, -45, 5, 'Mid Semester Examination'),
    ('End Semester Exam — Sem 5',  5, -10, 7, 'End Semester Examination'),
]

exams = {}
for name, sem, start_offset, duration, type_name in exam_defs:
    start = today + timedelta(days=start_offset)
    end = start + timedelta(days=duration)
    exam, created = Exam.objects.get_or_create(
        college=college, name=name, semester=sem,
        defaults={
            'start_date': start,
            'end_date': end,
            'created_by': coe_user,
        }
    )
    exams[(sem, type_name)] = exam
    print(f"  {'created' if created else 'exists'}: {name}")

# ── 6. Exam Schedules ─────────────────────────────────────────────────────────

print("\n[5] Creating Exam Schedules...")
from datetime import time as dtime

schedule_count = 0
for (sem, type_name), exam in exams.items():
    subjects = Subject.objects.filter(department__college=college, semester=sem)
    exam_type = exam_types.get(type_name)
    for i, subj in enumerate(subjects):
        exam_date = exam.start_date + timedelta(days=i % 5)
        _, created = ExamSchedule.objects.get_or_create(
            exam=exam, subject=subj,
            defaults={
                'exam_type': exam_type,
                'date': exam_date,
                'start_time': dtime(10, 0),
                'end_time': dtime(13, 0),
                'max_marks': 100,
                'passing_marks': 40,
            }
        )
        if created:
            schedule_count += 1

print(f"  Created {schedule_count} schedule entries")

# ── 7. Enter Marks ────────────────────────────────────────────────────────────

print("\n[6] Entering Marks for all ANU students...")

marks_created = 0
results_created = 0

# Only use End Semester exams for results
end_exams = {sem: exams[(sem, 'End Semester Examination')] for sem in [1, 3, 5] if (sem, 'End Semester Examination') in exams}

for sem, exam in end_exams.items():
    students = Student.objects.filter(
        department__college=college,
        current_semester=sem,
        status='ACTIVE'
    ).select_related('department')

    subjects = list(Subject.objects.filter(department__college=college, semester=sem))

    print(f"  Sem {sem}: {students.count()} students × {len(subjects)} subjects")

    for student in students:
        dept_subjects = [s for s in subjects if s.department == student.department]
        student_marks = []

        for subj in dept_subjects:
            pct_base = random.randint(55, 92)
            raw = rand_marks(pct_base, 12)
            pct = round(raw / 100 * 100, 1)
            grade = grade_from_pct(pct)

            m, created = Marks.objects.get_or_create(
                student=student, subject=subj, exam=exam,
                defaults={
                    'marks_obtained': raw,
                    'max_marks': 100,
                    'grade': grade,
                    'grade_point': grade_point(grade),
                }
            )
            if created:
                marks_created += 1
            student_marks.append(m)

        # Compute SGPA and save Result
        if student_marks:
            sgpa, total_credits = compute_sgpa(student_marks)
            total_marks = sum(m.marks_obtained for m in student_marks)
            max_total = sum(m.max_marks for m in student_marks)
            pct = round(total_marks / max_total * 100, 2) if max_total else 0

            Result.objects.update_or_create(
                student=student, semester=sem,
                defaults={
                    'total_marks': total_marks,
                    'percentage': pct,
                    'gpa': sgpa,
                }
            )
            results_created += 1

            # ExamResult
            total_max = sum(m.max_marks for m in student_marks)
            ExamResult.objects.update_or_create(
                student=student, exam=exam,
                defaults={
                    'total_marks_obtained': total_marks,
                    'total_max_marks': total_max,
                    'percentage': pct,
                    'grade': grade_from_pct(pct),
                    'is_pass': pct >= 40,
                    'status': 'PUBLISHED',
                    'published_by': coe_user,
                    'published_at': timezone.now(),
                }
            )

print(f"  Marks created: {marks_created}")
print(f"  Results created: {results_created}")

# ── 8. Internal Marks (CIE) ───────────────────────────────────────────────────

print("\n[7] Entering Internal Marks (CIE)...")

im_count = 0
for sem in [1, 3, 5]:
    students = Student.objects.filter(
        department__college=college,
        current_semester=sem,
        status='ACTIVE'
    )
    subjects = list(Subject.objects.filter(department__college=college, semester=sem))

    for student in students:
        dept_subjects = [s for s in subjects if s.department == student.department]
        for subj in dept_subjects:
            ia1 = random.randint(10, 15)
            ia2 = random.randint(10, 15)
            asgn = random.randint(3, 5)
            att_marks = random.randint(3, 5)
            _, created = InternalMark.objects.get_or_create(
                student=student, subject=subj,
                defaults={
                    'ia1': ia1,
                    'ia2': ia2,
                    'assignment_marks': asgn,
                    'attendance_marks': att_marks,
                }
            )
            if created:
                im_count += 1

print(f"  Internal marks created: {im_count}")

# ── 9. Grace Marks Rule ───────────────────────────────────────────────────────

print("\n[8] Creating Grace Marks Rule...")
try:
    scheme_obj = EvaluationScheme.objects.filter(college=college).first()
    if scheme_obj:
        GraceMarksRule.objects.get_or_create(
            scheme=scheme_obj,
            defaults={
                'max_grace_per_subject': 5,
                'max_grace_total': 10,
                'apply_only_if_failing': True,
                'requires_approval': True,
                'is_active': True,
            }
        )
        print("  Grace marks rule created")
    else:
        print("  Skipped: no evaluation scheme found")
except Exception as e:
    print(f"  Skipped grace marks rule: {e}")

# ── Done ──────────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("  ANU Exam Seed Complete!")
print("=" * 60)
print()
print("  Exam Staff Login Credentials (all: Exam@1234)")
print("  ─────────────────────────────────────────────")
print("  COE (Controller)    : anu_coe         / Exam@1234")
print("  Deputy COE          : anu_deputy_coe  / Exam@1234")
print("  Exam Coordinator    : anu_exam_coord  / Exam@1234")
print("  Section Officer CSE : anu_section_cse / Exam@1234")
print("  Section Officer ECE : anu_section_ece / Exam@1234")
print("  Valuation Officer   : anu_valuation   / Exam@1234")
print("  Data Entry Operator : anu_data_entry  / Exam@1234")
print()
print("  Dashboard URL: /dashboard/exam/")
print()
print("  Exams seeded for semesters: 1, 3, 5")
print("  Marks + Results published for all active ANU students")
print("=" * 60)
