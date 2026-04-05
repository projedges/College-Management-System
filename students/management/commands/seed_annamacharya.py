"""
Management command: seed_annamacharya
Creates Annamacharya University college, departments, college admin,
HOD, principal, faculty (from faculty_final.csv) and students
(from students_final_correct.csv) — all additive, never deletes existing data.

Usage:
    python manage.py seed_annamacharya
    python manage.py seed_annamacharya --students students_final_correct.csv --faculty faculty_final.csv
"""
import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone


DEPT_MAP = {
    '1': ('Computer Science & Engineering', 'CSE'),
    '01': ('Computer Science & Engineering', 'CSE'),
    '2': ('Electronics & Communication Engineering', 'ECE'),
    '02': ('Electronics & Communication Engineering', 'ECE'),
    '3': ('Mechanical Engineering', 'MECH'),
    '03': ('Mechanical Engineering', 'MECH'),
    '4': ('Civil Engineering', 'CIVIL'),
    '04': ('Civil Engineering', 'CIVIL'),
    '5': ('Information Science & Engineering', 'ISE'),
    '05': ('Information Science & Engineering', 'ISE'),
}

COLLEGE_NAME = 'Annamacharya University'
COLLEGE_CODE = 'ANU'


class Command(BaseCommand):
    help = 'Seed Annamacharya University data from CSV files (additive only)'

    def add_arguments(self, parser):
        parser.add_argument('--students', default='students_final_correct.csv')
        parser.add_argument('--faculty', default='faculty_final.csv')

    def handle(self, *args, **options):
        from students.models import (
            College, Department, UserRole, Student, Faculty,
            HOD, Principal, AdminProfile, Fee,
        )

        self.stdout.write(self.style.MIGRATE_HEADING('=== Annamacharya University Seed ==='))

        with transaction.atomic():
            # ── 1. College ────────────────────────────────────────────────────
            college, created = College.objects.get_or_create(
                name=COLLEGE_NAME,
                defaults={
                    'code': COLLEGE_CODE,
                    'city': 'Rajampet',
                    'state': 'Andhra Pradesh',
                    'email': 'admin@annamacharya.edu',
                    'website': 'https://annamacharya.edu',
                    'is_active': True,
                }
            )
            self._log('College', COLLEGE_NAME, created)

            # ── 2. Departments ────────────────────────────────────────────────
            depts = {}
            for code_key, (name, code) in DEPT_MAP.items():
                if code in depts:
                    continue
                dept, c = Department.objects.get_or_create(
                    college=college, code=code,
                    defaults={'name': name}
                )
                depts[code] = dept
                self._log('Department', code, c)

            # Helper: resolve dept from CSV dept_code field
            def get_dept(raw_code):
                raw = str(raw_code).strip()
                entry = DEPT_MAP.get(raw)
                if not entry:
                    return None
                return depts.get(entry[1])

            # ── 3. College Admin ──────────────────────────────────────────────
            admin_user, created = self._get_or_create_user(
                username='anu_admin',
                email='admin@annamacharya.edu',
                password='ANU@Admin2026',
                first_name='College',
                last_name='Admin',
            )
            if created or not UserRole.objects.filter(user=admin_user).exists():
                UserRole.objects.update_or_create(
                    user=admin_user,
                    defaults={'role': 1, 'college': college}
                )
                AdminProfile.objects.get_or_create(
                    user=admin_user,
                    defaults={'full_name': 'College Admin', 'phone_number': '9000000000',
                              'designation': 'College Administrator'}
                )
            self._log('College Admin', 'anu_admin', created)

            # ── 4. Principal ──────────────────────────────────────────────────
            principal_user, created = self._get_or_create_user(
                username='anu_principal',
                email='principal@annamacharya.edu',
                password='ANU@Principal2026',
                first_name='Dr. Ravi',
                last_name='Kumar',
            )
            if created or not UserRole.objects.filter(user=principal_user).exists():
                UserRole.objects.update_or_create(
                    user=principal_user,
                    defaults={'role': 5, 'college': college}
                )
                Principal.objects.get_or_create(
                    user=principal_user,
                    defaults={
                        'college': college,
                        'employee_id': 'ANU-PRIN-001',
                        'phone_number': '9000000001',
                        'qualification': 'PhD',
                        'experience_years': 20,
                    }
                )
            self._log('Principal', 'anu_principal', created)

            # ── 5. HODs (one per department) ──────────────────────────────────
            hod_data = [
                ('CSE',   'anu_hod_cse',   'hod.cse@annamacharya.edu',   'Dr. Suresh',  'Reddy'),
                ('ECE',   'anu_hod_ece',   'hod.ece@annamacharya.edu',   'Dr. Priya',   'Sharma'),
                ('MECH',  'anu_hod_mech',  'hod.mech@annamacharya.edu',  'Dr. Ramesh',  'Naidu'),
                ('CIVIL', 'anu_hod_civil', 'hod.civil@annamacharya.edu', 'Dr. Lakshmi', 'Devi'),
                ('ISE',   'anu_hod_ise',   'hod.ise@annamacharya.edu',   'Dr. Venkat',  'Rao'),
            ]
            for dept_code, uname, email, fname, lname in hod_data:
                dept = depts.get(dept_code)
                if not dept:
                    continue
                hod_user, created = self._get_or_create_user(
                    username=uname, email=email, password='ANU@HOD2026',
                    first_name=fname, last_name=lname,
                )
                if created or not UserRole.objects.filter(user=hod_user).exists():
                    UserRole.objects.update_or_create(
                        user=hod_user,
                        defaults={'role': 2, 'college': college}
                    )
                from students.models import HOD
                HOD.objects.get_or_create(
                    user=hod_user, department=dept,
                    defaults={
                        'is_active': True,
                        'employee_id': f'ANU-HOD-{dept_code}',
                        'phone_number': '9000000002',
                        'qualification': 'PhD',
                        'experience_years': 15,
                    }
                )
                self._log(f'HOD ({dept_code})', uname, created)

            # ── 6. Faculty from CSV ───────────────────────────────────────────
            fac_path = options['faculty']
            if not os.path.isabs(fac_path):
                fac_path = os.path.join(os.getcwd(), fac_path)

            fac_ok = fac_skip = fac_err = 0
            if os.path.exists(fac_path):
                with open(fac_path, encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            dept = get_dept(row.get('dept_code', ''))
                            if not dept:
                                fac_err += 1
                                continue
                            username = (row.get('username') or row.get('email', '')).strip()
                            email = row.get('email', '').strip()
                            emp_id = row.get('employee_id', '').strip()
                            if not username or not email or not emp_id:
                                fac_err += 1
                                continue
                            if User.objects.filter(username=username).exists():
                                fac_skip += 1
                                continue
                            if Faculty.objects.filter(employee_id=emp_id).exists():
                                fac_skip += 1
                                continue
                            user = User.objects.create_user(
                                username=username, email=email,
                                password=row.get('password', 'EduTrack@123'),
                                first_name=row.get('first_name', '').strip(),
                                last_name=row.get('last_name', '').strip(),
                            )
                            UserRole.objects.create(user=user, role=3, college=college)
                            Faculty.objects.create(
                                user=user,
                                employee_id=emp_id,
                                department=dept,
                                designation=row.get('designation', 'Assistant Professor').strip(),
                                qualification=row.get('qualification', 'M.Tech').strip(),
                                experience_years=int(row.get('experience_years', 0) or 0),
                                phone_number=row.get('phone_number', '').strip(),
                            )
                            fac_ok += 1
                        except Exception as e:
                            fac_err += 1
                            self.stderr.write(f'  Faculty row error: {e}')
                self.stdout.write(self.style.SUCCESS(
                    f'Faculty: {fac_ok} imported, {fac_skip} skipped, {fac_err} errors'
                ))
            else:
                self.stderr.write(f'Faculty CSV not found: {fac_path}')

            # ── 7. Students from CSV ──────────────────────────────────────────
            stu_path = options['students']
            if not os.path.isabs(stu_path):
                stu_path = os.path.join(os.getcwd(), stu_path)

            stu_ok = stu_skip = stu_err = 0
            if os.path.exists(stu_path):
                with open(stu_path, encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            dept = get_dept(row.get('dept_code', ''))
                            if not dept:
                                stu_err += 1
                                continue
                            username = (row.get('username') or row.get('email', '')).strip()
                            email = row.get('email', '').strip()
                            if not username or not email:
                                stu_err += 1
                                continue
                            if User.objects.filter(username=username).exists():
                                stu_skip += 1
                                continue
                            if User.objects.filter(email=email).exists():
                                stu_skip += 1
                                continue
                            adm_year = int(row.get('admission_year', 2024) or 2024)
                            sem = int(row.get('current_semester', 1) or 1)
                            # Auto-generate roll number
                            roll = row.get('roll_number', '').strip()
                            if not roll:
                                year_short = str(adm_year)[-2:]
                                count = Student.objects.filter(
                                    department=dept, admission_year=adm_year
                                ).count() + 1
                                roll = f"{adm_year}-{COLLEGE_CODE}-{dept.code}-{count:03d}"
                            if Student.objects.filter(roll_number=roll).exists():
                                stu_skip += 1
                                continue
                            user = User.objects.create_user(
                                username=username, email=email,
                                password=row.get('password', 'edutrack@123'),
                                first_name=row.get('first_name', '').strip(),
                                last_name=row.get('last_name', '').strip(),
                            )
                            UserRole.objects.create(user=user, role=4, college=college)
                            student = Student.objects.create(
                                user=user,
                                roll_number=roll,
                                department=dept,
                                admission_year=adm_year,
                                current_semester=sem,
                                status='ACTIVE',
                            )
                            # Create default fee record
                            year_offset = (sem - 1) // 2
                            start_year = adm_year + year_offset
                            Fee.objects.create(
                                student=student,
                                total_amount=50000.0,
                                paid_amount=0.0,
                                semester=sem,
                                academic_year=f"{start_year}-{str(start_year+1)[-2:]}",
                                status='PENDING',
                            )
                            stu_ok += 1
                        except Exception as e:
                            stu_err += 1
                            self.stderr.write(f'  Student row error: {e}')
                self.stdout.write(self.style.SUCCESS(
                    f'Students: {stu_ok} imported, {stu_skip} skipped, {stu_err} errors'
                ))
            else:
                self.stderr.write(f'Students CSV not found: {stu_path}')

        self.stdout.write(self.style.SUCCESS('\n=== Done. Existing data untouched. ==='))
        self.stdout.write('\nLogin credentials created:')
        self.stdout.write('  College Admin : username=anu_admin        password=ANU@Admin2026')
        self.stdout.write('  Principal     : username=anu_principal    password=ANU@Principal2026')
        self.stdout.write('  HOD (CSE)     : username=anu_hod_cse      password=ANU@HOD2026')
        self.stdout.write('  HOD (ECE)     : username=anu_hod_ece      password=ANU@HOD2026')
        self.stdout.write('  HOD (MECH)    : username=anu_hod_mech     password=ANU@HOD2026')
        self.stdout.write('  HOD (CIVIL)   : username=anu_hod_civil    password=ANU@HOD2026')
        self.stdout.write('  HOD (ISE)     : username=anu_hod_ise      password=ANU@HOD2026')

    def _get_or_create_user(self, username, email, password, first_name, last_name):
        if User.objects.filter(username=username).exists():
            return User.objects.get(username=username), False
        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name,
        )
        return user, True

    def _log(self, kind, name, created):
        if created:
            self.stdout.write(self.style.SUCCESS(f'  [+] {kind}: {name}'))
        else:
            self.stdout.write(f'  [=] {kind}: {name} (already exists)')
