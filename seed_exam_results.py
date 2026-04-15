"""
seed_exam_results.py
====================
Seeds complete examination data for VITM college:
  1. Creates ExamStaff (COE) account
  2. Creates EvaluationScheme
  3. Creates ExamSchedule for End Semester Exam (Sem 2)
  4. Enters Marks for ALL Sem-2 students across all 4 departments (faculty-side)
  5. Enters InternalMarks for all Sem-2 students
  6. Computes ExamResult + Result (SGPA) for every student
  7. Publishes all results

Run: python seed_exam_results.py
"""

import os, random, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studentmanagementsystem.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from students.models import (
    College, Department, Student, Faculty, Subject, Exam, Marks, Result,
    ExamResult, ExamStaff, ExamType, EvaluationScheme, ExamSchedule,
    InternalMark, FacultySubject, UserRole, ResultVersion, AuditLog,
    GraceMarksRule,
)

random.seed(42)

# ── helpers ──────────────────────────────────────────────────────────────────

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

def compute_sgpa(student, semester, exam):
    marks_qs = Marks.objects.filter(
        student=student, exam=exam, subject__semester=semester
    ).select_related('subject')
    tcp, tc = 0.0, 0
    for m in marks_qs:
        cr = m.subject.credits or 3
        gp = grade_point(m.grade or 'F')
        tcp += cr * gp
        tc += cr
    return (round(tcp / tc, 2) if tc > 0 else 0.0), tc

def realistic_marks(base, spread=15):
    """Return a realistic mark with some variance."""
    val = base + random.randint(-spread, spread)
    return max(20, min(100, val))

# ── 1. Get college ────────────────────────────────────────────────────────────

college = College.objects.get(code='VITM')
print(f"College: {college.name}")

# ── 2. Create ExamStaff (COE) ─────────────────────────────────────────────────

with transaction.atomic():
    coe_user, created = User.objects.get_or_create(
        username='coe_vitm',
        defaults={
            'first_name': 'Ramesh',
            'last_name': 'Kumar',
            'email': 'coe@vitm.edu',
            'is_active': True,
        }
    )
    if created:
        coe_user.set_password('Test@1234')
        coe_user.save()
        print("Created COE user: coe_vitm / Test@1234")
    else:
        print("COE user already exists: coe_vitm")

    ec, _ = ExamStaff.objects.get_or_create(
        user=coe_user,
        defaults={
            'college': college,
            'exam_role': 'COE',
            'employee_id': 'COE-VITM-001',
            'phone_number': '9876543210',
            'is_active': True,
        }
    )
    UserRole.objects.update_or_create(
        user=coe_user,
        defaults={'role': 7, 'college': college}
    )
    print(f"ExamStaff: {ec.user.username} [{ec.exam_role}]")

# ── 3. Create EvaluationScheme ────────────────────────────────────────────────

with transaction.atomic():
    scheme, _ = EvaluationScheme.objects.get_or_create(
        college=college,
        department=None,
        name='VITM Standard Scheme',
        defaults={
            'description': 'Standard evaluation: CIE 50 + SEE 50',
            'cie_count': 2,
            'cie_best_of': 2,
            'cie_max_per_test': 25,
            'cie_total_max': 50,
            'see_max': 100,
            'see_scaled_to': 50,
            'see_passing_min': 20,
            'overall_passing_min': 40,
            'grading_type': 'ABSOLUTE',
            'is_active': True,
        }
    )
    print(f"EvaluationScheme: {scheme.name}")

    # Grace marks rule
    GraceMarksRule.objects.get_or_create(
        scheme=scheme,
        defaults={
            'max_grace_per_subject': 5,
            'max_grace_total': 10,
            'apply_only_if_failing': True,
            'requires_approval': False,
            'is_active': True,
        }
    )
    print("GraceMarksRule created")

# ── 4. Get the End Semester Exam (Sem 2) ─────────────────────────────────────

ese = Exam.objects.get(id=21)  # End Semester Exam | Sem 2 | VITM
print(f"\nUsing exam: {ese.name} (Sem {ese.semester})")

# ── 5. Create ExamType ────────────────────────────────────────────────────────

with transaction.atomic():
    see_type, _ = ExamType.objects.get_or_create(
        college=college,
        name='SEE Nov 2025',
        defaults={
            'category': 'SEE',
            'max_marks': 100,
            'passing_marks': 40,
            'weightage_percent': 50,
            'is_active': True,
        }
    )
    cie_type, _ = ExamType.objects.get_or_create(
        college=college,
        name='CIE-1',
        defaults={
            'category': 'CIE',
            'max_marks': 25,
            'passing_marks': 10,
            'weightage_percent': 25,
            'is_active': True,
        }
    )
    print(f"ExamTypes: {see_type.name}, {cie_type.name}")

# ── 6. Create ExamSchedule for all Sem-2 subjects ────────────────────────────

sem2_subjects = Subject.objects.filter(
    department__college=college, semester=2
).select_related('department')

from datetime import date, timedelta
base_date = date(2026, 3, 21)

with transaction.atomic():
    for i, subj in enumerate(sem2_subjects.order_by('department__code', 'code')):
        ExamSchedule.objects.get_or_create(
            exam=ese,
            subject=subj,
            defaults={
                'exam_type': see_type,
                'date': base_date + timedelta(days=i),
                'start_time': '09:00',
                'end_time': '12:00',
                'venue': f'Hall {(i % 4) + 1}',
                'max_marks': 100,
                'passing_marks': 40,
            }
        )
    print(f"ExamSchedule: {sem2_subjects.count()} subjects scheduled")

# ── 7. Enter Marks for ALL Sem-2 students (faculty-side) ─────────────────────

# Department-wise base marks (realistic distribution)
DEPT_PROFILES = {
    'CSE': {'base': 72, 'spread': 18},
    'ISE': {'base': 68, 'spread': 20},
    'ECE': {'base': 65, 'spread': 22},
    'ME':  {'base': 60, 'spread': 20},
}

# Subject difficulty modifier
SUBJECT_MODIFIERS = {
    'CSE201': 5, 'CSE202': -5, 'CSE203': 0, 'CSE204': -8,
    'ISE201': 3, 'ISE202': -3, 'ISE203': 5, 'ISE204': -10,
    'ECE201': 0, 'ECE202': -8, 'ECE203': -5, 'ECE204': 8,
    'ME201': 5, 'ME202': -10, 'ME203': 0, 'ME204': 3,
}

# Get faculty user for audit
admin_user = User.objects.get(username='admin_vitm')

marks_created = 0
internal_created = 0

with transaction.atomic():
    for dept in Department.objects.filter(college=college):
        profile = DEPT_PROFILES.get(dept.code, {'base': 65, 'spread': 18})
        subjects = Subject.objects.filter(department=dept, semester=2)
        students = Student.objects.filter(
            department=dept, current_semester=2, is_deleted=False, status='ACTIVE'
        ).select_related('user')

        if not students.exists() or not subjects.exists():
            continue

        print(f"\n  {dept.code}: {students.count()} students × {subjects.count()} subjects")

        for student in students:
            # Vary per-student ability
            student_ability = random.randint(-15, 15)

            for subj in subjects:
                subj_mod = SUBJECT_MODIFIERS.get(subj.code, 0)
                base = profile['base'] + student_ability + subj_mod
                obtained = realistic_marks(base, profile['spread'] // 2)
                grade = grade_from_pct(obtained)
                gp = grade_point(grade)

                m, created = Marks.objects.update_or_create(
                    student=student,
                    subject=subj,
                    exam=ese,
                    defaults={
                        'marks_obtained': float(obtained),
                        'max_marks': 100.0,
                        'grade': grade,
                        'grade_point': float(gp),
                    }
                )
                if created:
                    marks_created += 1

            # Internal marks (IA1, IA2, assignment, attendance)
            ia1 = min(25, max(8, int(student_ability * 0.3 + profile['base'] * 0.25 + random.randint(-3, 3))))
            ia2 = min(25, max(8, int(student_ability * 0.3 + profile['base'] * 0.25 + random.randint(-3, 3))))
            asgn = min(20, max(5, int(profile['base'] * 0.18 + random.randint(-2, 4))))
            att = random.choice([3, 4, 4, 5, 5, 5])

            # Get faculty for this student's first subject
            first_subj = subjects.first()
            fs = FacultySubject.objects.filter(subject=first_subj).first()
            entered_by = fs.faculty.user if fs else admin_user

            im, created = InternalMark.objects.update_or_create(
                student=student,
                subject=first_subj,
                defaults={
                    'entered_by': entered_by,
                    'ia1': float(ia1),
                    'ia2': float(ia2),
                    'assignment_marks': float(asgn),
                    'attendance_marks': float(att),
                }
            )
            if created:
                internal_created += 1

print(f"\nMarks created: {marks_created}")
print(f"InternalMarks created: {internal_created}")

# ── 8. Compute ExamResult + Result (SGPA) for all Sem-2 students ─────────────

print("\n=== Computing Results ===")
results_computed = 0
passing_min = scheme.overall_passing_min  # 40

with transaction.atomic():
    for dept in Department.objects.filter(college=college):
        students = Student.objects.filter(
            department=dept, current_semester=2, is_deleted=False, status='ACTIVE'
        )
        if not students.exists():
            continue

        for student in students:
            # Total marks across all subjects
            marks_qs = Marks.objects.filter(student=student, exam=ese)
            total_obtained = sum(m.marks_obtained for m in marks_qs)
            total_max = sum(m.max_marks for m in marks_qs)
            pct = round(total_obtained / total_max * 100, 1) if total_max > 0 else 0
            overall_grade = grade_from_pct(pct)
            is_pass = pct >= passing_min

            # ExamResult
            ExamResult.objects.update_or_create(
                student=student,
                exam=ese,
                defaults={
                    'total_marks_obtained': total_obtained,
                    'total_max_marks': total_max,
                    'percentage': pct,
                    'grade': overall_grade,
                    'is_pass': is_pass,
                    'status': 'PUBLISHED',
                    'published_by': coe_user,
                    'published_at': timezone.now(),
                    'verified_by': coe_user,
                }
            )

            # SGPA
            sgpa, total_credits = compute_sgpa(student, 2, ese)

            result_obj, _ = Result.objects.update_or_create(
                student=student,
                semester=2,
                defaults={
                    'gpa': sgpa,
                    'sgpa': sgpa,
                    'total_marks': total_obtained,
                    'percentage': pct,
                    'total_credits': total_credits,
                }
            )

            # Snapshot (version 1 = publication)
            if not ResultVersion.objects.filter(result=result_obj, version_no=1).exists():
                ResultVersion.objects.create(
                    result=result_obj,
                    version_no=1,
                    sgpa=sgpa,
                    total_marks=total_obtained,
                    percentage=pct,
                    snapshot_reason='Initial publication',
                    created_by=coe_user,
                )

            results_computed += 1

print(f"Results computed & published: {results_computed}")

# ── 9. Print summary ──────────────────────────────────────────────────────────

print("\n" + "="*60)
print("SEED COMPLETE — VITM Sem-2 End Semester Exam")
print("="*60)

total_pass = ExamResult.objects.filter(exam=ese, status='PUBLISHED', is_pass=True).count()
total_fail = ExamResult.objects.filter(exam=ese, status='PUBLISHED', is_pass=False).count()
print(f"Total published results : {results_computed}")
print(f"Passed                  : {total_pass}")
print(f"Failed                  : {total_fail}")

print("\n--- Per-department breakdown ---")
for dept in Department.objects.filter(college=college):
    students = Student.objects.filter(department=dept, current_semester=2)
    if not students.exists():
        continue
    results = Result.objects.filter(student__in=students, semester=2)
    if results.exists():
        avg_sgpa = round(sum(r.sgpa for r in results) / results.count(), 2)
        print(f"  {dept.code}: {results.count()} students | avg SGPA {avg_sgpa}")

print("\n--- Sample student results ---")
for er in ExamResult.objects.filter(exam=ese, status='PUBLISHED').select_related(
    'student__user', 'student__department'
).order_by('student__department__code', 'student__roll_number')[:12]:
    r = Result.objects.filter(student=er.student, semester=2).first()
    sgpa = r.sgpa if r else '—'
    print(f"  {er.student.roll_number:25} | {er.student.department.code} | "
          f"{er.percentage:.1f}% | {er.grade} | SGPA {sgpa} | {'PASS' if er.is_pass else 'FAIL'}")

print("\n--- Login credentials ---")
print("  COE (Exam Dept) : coe_vitm / Test@1234  →  /dashboard/exam/")
print("  Faculty (CSE)   : fac_sunita_vitm / (existing password)  →  /dashboard/faculty/")
print("  Faculty (ISE)   : fac_suresh_vitm / (existing password)  →  /dashboard/faculty/")
print("  Student (ISE)   : stu_1_vitm / (existing password)  →  /dashboard/student/")
print("  Student (ECE)   : stu_2_vitm / (existing password)  →  /dashboard/student/")
print("  Admin           : admin_vitm / (existing password)  →  /dashboard/admin/")
print("\nExam ID for URLs: 21  (End Semester Exam Sem 2)")
print("  /dashboard/exam/21/results/")
print("  /dashboard/exam/21/marks/")
print("  /dashboard/exam/21/grace-marks/")
print("  /dashboard/exam/21/result-versions/")
