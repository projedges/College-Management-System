"""
Management command: seed_semester_planner
Seeds demo Regulation, CurriculumEntry, and ElectivePool data
for the ISE department of Annamacharya University (created by seed_annamacharya).

Usage:
    python manage.py seed_semester_planner
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed demo regulation, curriculum, and elective pool data'

    def handle(self, *args, **options):
        from students.models import (
            College, Department, Subject, Regulation,
            CurriculumEntry, ElectivePool,
        )
        from django.contrib.auth.models import User

        self.stdout.write('=== Semester Planner Demo Seed ===')

        college = College.objects.filter(code='ANU').first()
        if not college:
            self.stderr.write('College ANU not found. Run seed_annamacharya first.')
            return

        dept = Department.objects.filter(college=college, code='ISE').first()
        if not dept:
            self.stderr.write('ISE department not found. Run seed_annamacharya first.')
            return

        admin_user = User.objects.filter(username='anu_admin').first()

        with transaction.atomic():

            # ── 1. Regulation ─────────────────────────────────────────────────
            reg, created = Regulation.objects.get_or_create(
                college=college, code='ANU2021',
                defaults={
                    'name': 'Annamacharya University Scheme 2021',
                    'description': 'B.Tech 4-year programme under ANU 2021 regulations. '
                                   'CIE 40 marks + SEE 60 marks. Min 75% attendance.',
                    'effective_from_year': 2021,
                    'is_active': True,
                }
            )
            self._log('Regulation', reg.name, created)

            # ── 2. Subjects for ISE Sem 5 ─────────────────────────────────────
            subjects_data = [
                # (name, code, L, T, P, credits, category)
                ('Machine Learning',          'ISE501', 3, 0, 2, 4, 'PC'),
                ('Big Data Analytics',        'ISE502', 3, 0, 2, 4, 'PC'),
                ('Cloud Computing',           'ISE503', 3, 0, 0, 3, 'PC'),
                ('Professional Ethics',       'ISE504', 2, 0, 0, 2, 'MC'),
                # Program Electives (PE-1 — choose one)
                ('Internet of Things',        'ISE511', 3, 0, 2, 4, 'PE'),
                ('Natural Language Processing','ISE512', 3, 0, 2, 4, 'PE'),
                ('Blockchain Technology',     'ISE513', 3, 0, 0, 3, 'PE'),
                # Open Electives (OE-1 — choose one)
                ('Entrepreneurship',          'ISE521', 2, 0, 0, 2, 'OE'),
                ('Environmental Science',     'ISE522', 2, 0, 0, 2, 'OE'),
            ]

            subj_map = {}
            for name, code, L, T, P, credits, cat in subjects_data:
                subj, c = Subject.objects.get_or_create(
                    department=dept, code=code,
                    defaults={
                        'name': name, 'semester': 5,
                        'lecture_hours': L, 'tutorial_hours': T,
                        'practical_hours': P, 'credits': credits,
                        'weekly_hours': L + T + P, 'category': cat,
                    }
                )
                subj_map[code] = subj
                self._log(f'Subject', f'{code} — {name}', c)

            # ── 3. Curriculum entries ─────────────────────────────────────────
            fixed_codes = ['ISE501', 'ISE502', 'ISE503', 'ISE504']
            pe_codes    = ['ISE511', 'ISE512', 'ISE513']
            oe_codes    = ['ISE521', 'ISE522']

            for code in fixed_codes:
                entry, c = CurriculumEntry.objects.get_or_create(
                    regulation=reg, department=dept,
                    subject=subj_map[code], semester=5,
                    defaults={'elective_type': 'FIXED'}
                )
                self._log('CurriculumEntry (FIXED)', code, c)

            for code in pe_codes:
                entry, c = CurriculumEntry.objects.get_or_create(
                    regulation=reg, department=dept,
                    subject=subj_map[code], semester=5,
                    defaults={'elective_type': 'PE'}
                )
                self._log('CurriculumEntry (PE)', code, c)

            for code in oe_codes:
                entry, c = CurriculumEntry.objects.get_or_create(
                    regulation=reg, department=dept,
                    subject=subj_map[code], semester=5,
                    defaults={'elective_type': 'OE'}
                )
                self._log('CurriculumEntry (OE)', code, c)

            # ── 4. Elective Pools ─────────────────────────────────────────────
            # PE-1 pool
            pe_pool, c = ElectivePool.objects.get_or_create(
                regulation=reg, department=dept, semester=5, slot_name='PE-1',
                defaults={
                    'elective_type': 'PE',
                    'quota_per_subject': 40,
                    'status': 'OPEN',
                    'deadline': timezone.now() + timezone.timedelta(days=7),
                    'created_by': admin_user,
                }
            )
            pe_pool.subjects.set([subj_map[c] for c in pe_codes])
            self._log('ElectivePool', 'PE-1 (IoT / NLP / Blockchain)', c)

            # OE-1 pool
            oe_pool, c = ElectivePool.objects.get_or_create(
                regulation=reg, department=dept, semester=5, slot_name='OE-1',
                defaults={
                    'elective_type': 'OE',
                    'quota_per_subject': 60,
                    'status': 'OPEN',
                    'deadline': timezone.now() + timezone.timedelta(days=7),
                    'created_by': admin_user,
                }
            )
            oe_pool.subjects.set([subj_map[c] for c in oe_codes])
            self._log('ElectivePool', 'OE-1 (Entrepreneurship / Env. Science)', c)

        self.stdout.write(self.style.SUCCESS('\n=== Done ==='))
        self.stdout.write('\nWhat to test:')
        self.stdout.write('  Admin → Regulations     : /dashboard/admin/regulations/')
        self.stdout.write('  Admin → Curriculum      : /dashboard/admin/regulations/<id>/curriculum/?dept=<ISE_id>&sem=5')
        self.stdout.write('  Admin → Elective Pools  : /dashboard/admin/electives/')
        self.stdout.write('  Student → Choose Elective: /dashboard/student/electives/')
        self.stdout.write('    (Login as any ISE Sem-5 student)')

    def _log(self, kind, name, created):
        if created:
            self.stdout.write(self.style.SUCCESS(f'  [+] {kind}: {name}'))
        else:
            self.stdout.write(f'  [=] {kind}: {name} (exists)')
