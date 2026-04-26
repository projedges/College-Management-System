#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studentmanagementsystem.settings')
django.setup()

from students.models import Department, Subject, Faculty, Section, Regulation, Classroom, TimetableBreak
from django.contrib.auth.models import User
from django.utils import timezone

college_id = 1

# Create sample department
dept, _ = Department.objects.get_or_create(
    code='CSE',
    defaults={
        'name': 'Computer Science & Engineering',
        'college_id': college_id,
        'section_capacity': 60
    }
)

# Create sample subjects for Semester 1
subjects_data = [
    {'code': 'CS101', 'name': 'Programming Fundamentals', 'credits': 4, 'semester': 1},
    {'code': 'CS102', 'name': 'Data Structures', 'credits': 4, 'semester': 1},
    {'code': 'CS103', 'name': 'Web Development', 'credits': 3, 'semester': 1},
    {'code': 'CS104', 'name': 'Database Management', 'credits': 4, 'semester': 1},
]

for subj_data in subjects_data:
    Subject.objects.get_or_create(
        code=subj_data['code'],
        defaults={
            'name': subj_data['name'],
            'credits': subj_data['credits'],
            'semester': subj_data['semester'],
            'department': dept,
            'is_active': True
        }
    )

# Create sample faculty
faculty_data = [
    {'first_name': 'John', 'last_name': 'Smith', 'email': 'john.smith@college.edu'},
    {'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'sarah.johnson@college.edu'},
    {'first_name': 'Michael', 'last_name': 'Brown', 'email': 'michael.brown@college.edu'},
]

for fac_data in faculty_data:
    user, _ = User.objects.get_or_create(
        username=fac_data['email'].split('@')[0],
        defaults={
            'first_name': fac_data['first_name'],
            'last_name': fac_data['last_name'],
            'email': fac_data['email']
        }
    )
    Faculty.objects.get_or_create(
        user=user,
        defaults={
            'department': dept,
            'college_id': college_id
        }
    )

# Create sample sections
for i in range(1, 3):
    Section.objects.get_or_create(
        department=dept,
        semester=1,
        label=chr(64 + i),
        defaults={
            'capacity': 60,
            'college_id': college_id
        }
    )

# Create sample classrooms
classroom_data = [
    {'room_number': '101', 'building': 'Block A', 'capacity': 60, 'room_type': 'lecture'},
    {'room_number': '102', 'building': 'Block A', 'capacity': 50, 'room_type': 'lecture'},
    {'room_number': 'Lab-01', 'building': 'Block B', 'capacity': 40, 'room_type': 'lab'},
]

for room_data in classroom_data:
    Classroom.objects.get_or_create(
        room_number=room_data['room_number'],
        college_id=college_id,
        defaults={
            'building': room_data['building'],
            'capacity': room_data['capacity'],
            'room_type': room_data['room_type']
        }
    )

# Create sample breaks
break_data = [
    {'label': 'Lunch Break', 'day_of_week': 'MON', 'start_time': '12:00', 'end_time': '13:00'},
    {'label': 'Tea Break', 'day_of_week': 'MON', 'start_time': '15:00', 'end_time': '15:15'},
]

for brk_data in break_data:
    TimetableBreak.objects.get_or_create(
        college_id=college_id,
        day_of_week=brk_data['day_of_week'],
        start_time=brk_data['start_time'],
        end_time=brk_data['end_time'],
        defaults={
            'label': brk_data['label'],
            'applies_to_all': True,
            'applies_to': 'college',
            'break_type': 'regular'
        }
    )

# Create sample regulation
Regulation.objects.get_or_create(
    code='CBCS-2024',
    college_id=college_id,
    defaults={
        'name': 'Choice Based Credit System 2024',
        'effective_from_year': 2024,
        'description': 'Modern curriculum with flexible course selection',
        'is_active': True
    }
)

print("✓ Sample data created successfully!")
print(f"  - Department: {dept.name} ({dept.code})")
print(f"  - Subjects: {Subject.objects.filter(department=dept, semester=1).count()}")
print(f"  - Faculty: {Faculty.objects.filter(department=dept).count()}")
print(f"  - Sections: {Section.objects.filter(department=dept, semester=1).count()}")
print(f"  - Classrooms: {Classroom.objects.filter(college_id=college_id).count()}")
print(f"  - Breaks: {TimetableBreak.objects.filter(college_id=college_id).count()}")
print(f"  - Regulations: {Regulation.objects.filter(college_id=college_id).count()}")
