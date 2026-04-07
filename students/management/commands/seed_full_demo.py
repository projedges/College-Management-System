"""
Management command: seed_full_demo
Creates a complete working demo for ISE department:
  - Regulation + Curriculum (Sem 5, 9 subjects)
  - 2 Sections (A & B), 60 students each
  - 8 Faculty members assigned to subjects
  - 4 Classrooms + 1 Lab
  - Full timetable: Mon–Sat, 9:00–13:00 & 14:00–16:00
    · 50-min periods, 10-min breaks between
    · 13:00–14:00 lunch
    · Lab = 2 consecutive periods (100 min)
  - TimetableBreaks registered
  - Elective pools (PE-1, OE-1) with min/max, all confirmed

Usage:
    python manage.py seed_full_demo
"""
from datetime import time, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User


PERIOD = 50       # minutes
BREAK  = 10       # minutes between periods
LUNCH_START = time(13, 0)
LUNCH_END   = time(14, 0)
AM_START    = time(9, 0)
PM_START    = time(14, 0)


def add_minutes(t, mins):
    total = t.hour * 60 + t.minute + mins
    return time(total // 60, total % 60)


def build_slots():
    """
    Returns list of (start, end, is_lab) for a full day.
    AM: 09:00–13:00  → 4 theory periods (50 min) + 3 breaks (10 min) = 240 min ✓
    Lunch: 13:00–14:00
    PM: 14:00–16:00  → 2 theory periods (50 min) + 1 break (10 min) = 110 min
    Lab slots replace 2 consecutive theory periods (100 min, no break between).
    """
    slots = []
    cur = AM_START
    for i in range(4):
        end = add_minutes(cur, PERIOD)
        slots.append((cur, end))
        if i < 3:
            cur = add_minutes(end, BREAK)
        else:
            cur = LUNCH_END  # jump to PM after 4th AM period
    for i in range(2):
        end = add_minutes(cur, PERIOD)
        slots.append((cur, end))
        if i < 1:
            cur = add_minutes(end, BREAK)
    return slots  # 6 slots: [0..3] AM, [4..5] PM


# Slot indices: 0=9:00, 1=10:00, 2=11:00, 3=12:00, 4=14:00, 5=15:00
# Lab = slots 0+1 (9:00–10:50) or 4+5 (14:00–15:50)

DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

# Timetable plan per section
# Format: (day, slot_index, subject_code, is_lab)
# Lab entries use slot_index as start; end = start+100min (2 periods + no break)
SECTION_A_PLAN = [
    # MON
    ('MON', 0, 'ISE501', False),   # ML 9:00
    ('MON', 1, 'ISE502', False),   # Big Data 10:00
    ('MON', 2, 'ISE503', False),   # Cloud 11:00
    ('MON', 3, 'ISE504', False),   # Ethics 12:00
    ('MON', 4, 'ISE511', False),   # PE (IoT) 14:00
    ('MON', 5, 'ISE521', False),   # OE 15:00
    # TUE
    ('TUE', 0, 'ISE502', False),
    ('TUE', 1, 'ISE501', False),
    ('TUE', 2, 'ISE511', False),
    ('TUE', 3, 'ISE503', False),
    ('TUE', 4, 'ISE501_LAB', True),   # ML Lab 14:00–15:50 (2 periods)
    # WED
    ('WED', 0, 'ISE503', False),
    ('WED', 1, 'ISE502', False),
    ('WED', 2, 'ISE504', False),
    ('WED', 3, 'ISE511', False),
    ('WED', 4, 'ISE502_LAB', True),   # Big Data Lab 14:00–15:50
    # THU
    ('THU', 0, 'ISE501', False),
    ('THU', 1, 'ISE503', False),
    ('THU', 2, 'ISE502', False),
    ('THU', 3, 'ISE521', False),
    ('THU', 4, 'ISE511', False),
    ('THU', 5, 'ISE504', False),
    # FRI
    ('FRI', 0, 'ISE502', False),
    ('FRI', 1, 'ISE501', False),
    ('FRI', 2, 'ISE511', False),
    ('FRI', 3, 'ISE503', False),
    ('FRI', 4, 'ISE511_LAB', True),   # IoT Lab 14:00–15:50
    # SAT
    ('SAT', 0, 'ISE503', False),
    ('SAT', 1, 'ISE504', False),
    ('SAT', 2, 'ISE521', False),
    ('SAT', 3, 'ISE501', False),
]

# Section B gets same subjects, different faculty, different room
SECTION_B_PLAN = SECTION_A_PLAN  # same schedule structure, different faculty/room


class Command(BaseCommand):
    help = 'Seed complete ISE Sem-5 demo: sections, faculty, timetable, electives'

    def handle(self, *args, **options):
        from students.models import (
            College, Department, Subject, Faculty, FacultySubject,
            Student, UserRole, Classroom, Timetable, TimetableBreak,
            Regulation, CurriculumEntry, ElectivePool, ElectiveSelection,
            Fee,
        )

        self.stdout.write(self.style.MIGRATE_HEADING('=== Full Demo Seed ==='))

        college = College.objects.filter(code='ANU').first()
        if not college:
            self.stderr.write('College ANU not found. Run seed_annamacharya first.')
            return

        dept = Department.objects.filter(college=college, code='ISE').first()
        if not dept:
            self.stderr.write('ISE dept not found. Run seed_annamacharya first.')
            return

        slots = build_slots()

        with transaction.atomic():

            # ── 1. Regulation + Subjects + Curriculum ─────────────────────────
            reg, _ = Regulation.objects.get_or_create(
                college=college, code='ANU2021',
                defaults={
                    'name': 'Annamacharya University Scheme 2021',
                    'description': 'CIE 40 + SEE 60. Min 75% attendance.',
                    'effective_from_year': 2021, 'is_active': True,
                }
            )

            subjects_data = [
                # (code, name, L, T, P, credits, category, has_lab)
                ('ISE501',     'Machine Learning',           3, 0, 2, 4, 'PC', True),
                ('ISE501_LAB', 'Machine Learning Lab',       0, 0, 4, 2, 'PC', False),
                ('ISE502',     'Big Data Analytics',         3, 0, 2, 4, 'PC', True),
                ('ISE502_LAB', 'Big Data Analytics Lab',     0, 0, 4, 2, 'PC', False),
                ('ISE503',     'Cloud Computing',            3, 0, 0, 3, 'PC', False),
                ('ISE504',     'Professional Ethics',        2, 0, 0, 2, 'MC', False),
                ('ISE511',     'Internet of Things',         3, 0, 2, 4, 'PE', True),
                ('ISE511_LAB', 'IoT Lab',                    0, 0, 4, 2, 'PE', False),
                ('ISE521',     'Entrepreneurship',           2, 0, 0, 2, 'OE', False),
            ]

            subj_map = {}
            for code, name, L, T, P, credits, cat, _ in subjects_data:
                subj, c = Subject.objects.get_or_create(
                    department=dept, code=code,
                    defaults={
                        'name': name, 'semester': 5,
                        'lecture_hours': L, 'tutorial_hours': T,
                        'practical_hours': P, 'credits': credits,
                        'weekly_hours': max(L + T + P, 1), 'category': cat,
                    }
                )
                subj_map[code] = subj
                self._log('Subject', code, c)

            # Curriculum entries
            fixed = ['ISE501', 'ISE501_LAB', 'ISE502', 'ISE502_LAB', 'ISE503', 'ISE504']
            pe    = ['ISE511', 'ISE511_LAB']
            oe    = ['ISE521']
            for code in fixed:
                CurriculumEntry.objects.get_or_create(
                    regulation=reg, department=dept, subject=subj_map[code], semester=5,
                    defaults={'elective_type': 'FIXED'}
                )
            for code in pe:
                CurriculumEntry.objects.get_or_create(
                    regulation=reg, department=dept, subject=subj_map[code], semester=5,
                    defaults={'elective_type': 'PE'}
                )
            for code in oe:
                CurriculumEntry.objects.get_or_create(
                    regulation=reg, department=dept, subject=subj_map[code], semester=5,
                    defaults={'elective_type': 'OE'}
                )
            self.stdout.write(self.style.SUCCESS('  [+] Curriculum entries done'))

            # ── 2. Classrooms ─────────────────────────────────────────────────
            rooms_data = [
                ('ISE-101', 'ISE Block', 65),   # Section A theory
                ('ISE-102', 'ISE Block', 65),   # Section B theory
                ('ISE-LAB1', 'ISE Block', 40),  # ML / Big Data Lab
                ('ISE-LAB2', 'ISE Block', 40),  # IoT Lab
            ]
            room_map = {}
            for rnum, building, cap in rooms_data:
                room, c = Classroom.objects.get_or_create(
                    college=college, room_number=rnum,
                    defaults={'building': building, 'capacity': cap}
                )
                room_map[rnum] = room
                self._log('Classroom', rnum, c)

            # ── 3. Faculty (8 members) ────────────────────────────────────────
            faculty_data = [
                # (username, email, fname, lname, emp_id, designation, subject_codes)
                ('fac_ml',    'ml@anu.edu',    'Dr. Ananya',  'Krishnan', 'ISE-F01', 'Associate Professor', ['ISE501', 'ISE501_LAB']),
                ('fac_bd',    'bd@anu.edu',    'Dr. Suresh',  'Babu',     'ISE-F02', 'Associate Professor', ['ISE502', 'ISE502_LAB']),
                ('fac_cloud', 'cloud@anu.edu', 'Dr. Priya',   'Nair',     'ISE-F03', 'Assistant Professor', ['ISE503']),
                ('fac_eth',   'eth@anu.edu',   'Mr. Ramesh',  'Kumar',    'ISE-F04', 'Assistant Professor', ['ISE504']),
                ('fac_iot',   'iot@anu.edu',   'Dr. Venkat',  'Reddy',    'ISE-F05', 'Associate Professor', ['ISE511', 'ISE511_LAB']),
                ('fac_oe',    'oe@anu.edu',    'Ms. Lakshmi', 'Devi',     'ISE-F06', 'Assistant Professor', ['ISE521']),
                # Section B duplicates for same subjects
                ('fac_ml_b',  'ml_b@anu.edu',  'Dr. Kiran',   'Sharma',   'ISE-F07', 'Associate Professor', ['ISE501', 'ISE501_LAB']),
                ('fac_bd_b',  'bd_b@anu.edu',  'Dr. Meena',   'Pillai',   'ISE-F08', 'Associate Professor', ['ISE502', 'ISE502_LAB']),
            ]

            fac_map = {}
            for uname, email, fname, lname, emp_id, desig, subj_codes in faculty_data:
                user, uc = User.objects.get_or_create(username=uname)
                user.email      = email
                user.first_name = fname
                user.last_name  = lname
                user.set_password('Faculty@123')
                user.save()
                if uc:
                    UserRole.objects.get_or_create(user=user, defaults={'role': 3, 'college': college})

                fac, fc = Faculty.objects.get_or_create(
                    user=user,
                    defaults={
                        'employee_id': emp_id, 'department': dept,
                        'designation': desig, 'qualification': 'M.Tech / PhD',
                        'experience_years': 5, 'phone_number': '9000000000',
                    }
                )
                fac_map[uname] = fac
                self._log('Faculty', f'{fname} {lname}', uc)

                for sc in subj_codes:
                    FacultySubject.objects.get_or_create(faculty=fac, subject=subj_map[sc])

            # ── 4. Students — 60 per section ──────────────────────────────────
            for section in ['A', 'B']:
                for i in range(1, 61):
                    uname = f'ise5_{section.lower()}{i:02d}'
                    roll  = f'2021-ANU-ISE-{section}{i:03d}'
                    email = f'{uname}@student.anu.edu'
                    user, uc = User.objects.get_or_create(username=uname)
                    user.email      = email
                    user.first_name = f'Student{i}'
                    user.last_name  = f'Sec{section}'
                    user.set_password('Student@123')
                    user.save()
                    if uc:
                        UserRole.objects.get_or_create(user=user, defaults={'role': 4, 'college': college})

                    student, sc = Student.objects.get_or_create(
                        roll_number=roll,
                        defaults={
                            'user': user, 'department': dept,
                            'admission_year': 2021, 'current_semester': 5,
                            'section': section, 'status': 'ACTIVE',
                        }
                    )
                    if sc:
                        Fee.objects.get_or_create(
                            student=student,
                            defaults={
                                'total_amount': 75000.0, 'paid_amount': 0.0,
                                'semester': 5, 'academic_year': '2023-24', 'status': 'PENDING',
                            }
                        )
                if i == 60:
                    self.stdout.write(self.style.SUCCESS(f'  [+] 60 students in Section {section}'))

            # ── 5. Timetable Breaks ───────────────────────────────────────────
            for day in DAYS:
                TimetableBreak.objects.get_or_create(
                    college=college, day_of_week=day,
                    label='Lunch Break', start_time=LUNCH_START, end_time=LUNCH_END,
                    defaults={'applies_to_all': True}
                )
            self.stdout.write(self.style.SUCCESS('  [+] Lunch breaks registered (Mon–Sat 1:00–2:00 PM)'))

            # ── 6. Timetable entries ──────────────────────────────────────────
            # Section A faculty map: subject_code → faculty username
            sec_a_fac = {
                'ISE501': 'fac_ml',  'ISE501_LAB': 'fac_ml',
                'ISE502': 'fac_bd',  'ISE502_LAB': 'fac_bd',
                'ISE503': 'fac_cloud', 'ISE504': 'fac_eth',
                'ISE511': 'fac_iot', 'ISE511_LAB': 'fac_iot',
                'ISE521': 'fac_oe',
            }
            # Section B faculty map
            sec_b_fac = {
                'ISE501': 'fac_ml_b', 'ISE501_LAB': 'fac_ml_b',
                'ISE502': 'fac_bd_b', 'ISE502_LAB': 'fac_bd_b',
                'ISE503': 'fac_cloud', 'ISE504': 'fac_eth',
                'ISE511': 'fac_iot',  'ISE511_LAB': 'fac_iot',
                'ISE521': 'fac_oe',
            }
            # Section A rooms
            sec_a_room = {
                'ISE501': 'ISE-101', 'ISE502': 'ISE-101', 'ISE503': 'ISE-101',
                'ISE504': 'ISE-101', 'ISE511': 'ISE-101', 'ISE521': 'ISE-101',
                'ISE501_LAB': 'ISE-LAB1', 'ISE502_LAB': 'ISE-LAB1', 'ISE511_LAB': 'ISE-LAB2',
            }
            # Section B rooms
            sec_b_room = {
                'ISE501': 'ISE-102', 'ISE502': 'ISE-102', 'ISE503': 'ISE-102',
                'ISE504': 'ISE-102', 'ISE511': 'ISE-102', 'ISE521': 'ISE-102',
                'ISE501_LAB': 'ISE-LAB1', 'ISE502_LAB': 'ISE-LAB1', 'ISE511_LAB': 'ISE-LAB2',
            }

            tt_count = 0
            for section, fac_lookup, room_lookup in [
                ('A', sec_a_fac, sec_a_room),
                ('B', sec_b_fac, sec_b_room),
            ]:
                for day, slot_idx, subj_code, is_lab in SECTION_A_PLAN:
                    subj   = subj_map.get(subj_code)
                    fac    = fac_map.get(fac_lookup.get(subj_code, ''))
                    room   = room_map.get(room_lookup.get(subj_code, 'ISE-101'))
                    if not subj or not fac or not room:
                        continue

                    start = slots[slot_idx][0]
                    if is_lab:
                        # Lab = 2 separate 50-min rows back-to-back
                        end1 = add_minutes(start, PERIOD)
                        start2 = end1
                        end2 = add_minutes(start2, PERIOD)
                        for s, e in [(start, end1), (start2, end2)]:
                            Timetable.objects.get_or_create(
                                subject=subj, faculty=fac, day_of_week=day,
                                start_time=s, section=section,
                                defaults={'end_time': e, 'classroom': room}
                            )
                            tt_count += 1
                    else:
                        end = add_minutes(start, PERIOD)
                        Timetable.objects.get_or_create(
                            subject=subj, faculty=fac, day_of_week=day,
                            start_time=start, section=section,
                            defaults={'end_time': end, 'classroom': room}
                        )
                        tt_count += 1

            self.stdout.write(self.style.SUCCESS(f'  [+] {tt_count} timetable slots created (Sec A + B)'))

            # ── 7. Elective Pools with min/max ────────────────────────────────
            pe_pool, c = ElectivePool.objects.get_or_create(
                regulation=reg, department=dept, semester=5, slot_name='PE-1',
                defaults={
                    'elective_type': 'PE',
                    'min_students_per_subject': 10,
                    'quota_per_subject': 60,
                    'status': 'OPEN',
                    'deadline': timezone.now() + timezone.timedelta(days=7),
                    'created_by': User.objects.filter(username='anu_admin').first(),
                }
            )
            pe_pool.subjects.set([subj_map['ISE511']])
            self._log('ElectivePool', 'PE-1 (IoT) min=10 max=60', c)

            oe_pool, c = ElectivePool.objects.get_or_create(
                regulation=reg, department=dept, semester=5, slot_name='OE-1',
                defaults={
                    'elective_type': 'OE',
                    'min_students_per_subject': 10,
                    'quota_per_subject': 60,
                    'status': 'OPEN',
                    'deadline': timezone.now() + timezone.timedelta(days=7),
                    'created_by': User.objects.filter(username='anu_admin').first(),
                }
            )
            oe_pool.subjects.set([subj_map['ISE521']])
            self._log('ElectivePool', 'OE-1 (Entrepreneurship) min=10 max=60', c)

            # Auto-confirm all students into their electives
            all_students = Student.objects.filter(department=dept, current_semester=5)
            sel_count = 0
            for student in all_students:
                for pool, subj_code in [(pe_pool, 'ISE511'), (oe_pool, 'ISE521')]:
                    ElectiveSelection.objects.get_or_create(
                        student=student, pool=pool,
                        defaults={
                            'subject': subj_map[subj_code],
                            'status': 'CONFIRMED',
                            'confirmed_at': timezone.now(),
                        }
                    )
                    sel_count += 1
            self.stdout.write(self.style.SUCCESS(f'  [+] {sel_count} elective selections confirmed'))

        self.stdout.write(self.style.SUCCESS('\n=== Done ==='))
        self._print_summary()

    def _print_summary(self):
        self.stdout.write('\n' + '─' * 55)
        self.stdout.write('DEMO CREDENTIALS')
        self.stdout.write('─' * 55)
        self.stdout.write('Admin    : anu_admin        / ANU@Admin2026')
        self.stdout.write('Faculty  : fac_ml           / Faculty@123')
        self.stdout.write('         : fac_bd           / Faculty@123')
        self.stdout.write('         : fac_iot          / Faculty@123')
        self.stdout.write('Student  : ise5_a01         / Student@123  (Sec A)')
        self.stdout.write('         : ise5_b01         / Student@123  (Sec B)')
        self.stdout.write('─' * 55)
        self.stdout.write('TIMETABLE STRUCTURE (Mon–Sat)')
        self.stdout.write('  09:00–09:50  Period 1')
        self.stdout.write('  09:50–10:00  Break')
        self.stdout.write('  10:00–10:50  Period 2')
        self.stdout.write('  10:50–11:00  Break')
        self.stdout.write('  11:00–11:50  Period 3')
        self.stdout.write('  11:50–12:00  Break')
        self.stdout.write('  12:00–12:50  Period 4')
        self.stdout.write('  12:50–13:00  Break')
        self.stdout.write('  13:00–14:00  LUNCH BREAK')
        self.stdout.write('  14:00–14:50  Period 5')
        self.stdout.write('  14:50–15:00  Break')
        self.stdout.write('  15:00–15:50  Period 6')
        self.stdout.write('  Lab slots  : 14:00–15:40 (2×50 min, no break)')
        self.stdout.write('─' * 55)

    def _log(self, kind, name, created):
        if created:
            self.stdout.write(self.style.SUCCESS(f'  [+] {kind}: {name}'))
        else:
            self.stdout.write(f'  [=] {kind}: {name} (exists)')
