import os
from datetime import time
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    Attendance,
    AttendanceSession,
    Address,
    College,
    Classroom,
    EmergencyContact,
    Department,
    Exam,
    Faculty,
    FacultySubject,
    Fee,
    HOD,
    Marks,
    Notification,
    Parent,
    Payment,
    RegistrationInvite,
    RegistrationRequest,
    RevaluationRequest,
    Student,
    StudentProfile,
    Subject,
    Timetable,
    SupplyExamRegistration,
    UserRole,
)


class AdminViewsRegressionTests(TestCase):
    def setUp(self):
        self.college = College.objects.create(name="Alpha College", code="ALPHA")
        self.other_college = College.objects.create(name="Beta College", code="BETA")
        self.admin_user = User.objects.create_user(
            username="admin1",
            password="pass12345",
            first_name="Admin",
            last_name="User",
        )
        UserRole.objects.create(user=self.admin_user, role=1, college=self.college)
        self.client.force_login(self.admin_user)

        self.cse = Department.objects.create(college=self.college, name="Computer Science", code="CSE")
        self.ece = Department.objects.create(college=self.college, name="Electronics", code="ECE")
        self.other_dept = Department.objects.create(college=self.other_college, name="Computer Science", code="CSE")

    def test_admin_hods_page_renders_real_template_context(self):
        hod_user = User.objects.create_user(username="hod1", password="pass12345", first_name="Hari")
        HOD.objects.create(
            user=hod_user,
            employee_id="HOD-001",
            department=self.cse,
            qualification="PhD",
            experience_years=8,
            phone_number="9999999999",
            is_active=True,
        )

        response = self.client.get(reverse("admin_hods"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_panel/hods.html")
        self.assertContains(response, "Hari")
        self.assertIn(self.ece, response.context["depts_without_hod"])

    def test_admin_subjects_page_renders_and_filters(self):
        Subject.objects.create(name="Data Structures", code="CS201", department=self.cse, semester=3)
        Subject.objects.create(name="Signals", code="EC201", department=self.ece, semester=3)
        Subject.objects.create(name="Operating Systems", code="CS501", department=self.cse, semester=5)

        response = self.client.get(
            reverse("admin_subjects"),
            {"dept": str(self.cse.pk), "sem": "3", "q": "Data"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_panel/subjects.html")
        subjects = list(response.context["subjects"])
        self.assertEqual(len(subjects), 1)
        self.assertEqual(subjects[0].department, self.cse)
        self.assertEqual(response.context["semester_filter"], "3")
        self.assertEqual(response.context["search_query"], "Data")

    def test_admin_subject_add_allows_same_code_in_different_departments(self):
        Subject.objects.create(name="Networks", code="301", department=self.cse, semester=5)

        response = self.client.post(
            reverse("admin_subject_add"),
            {
                "name": "Embedded Networks",
                "code": "301",
                "department": str(self.ece.pk),
                "semester": "5",
            },
        )

        self.assertRedirects(response, f"{reverse('admin_subjects')}?dept={self.ece.pk}&sem=5")
        self.assertTrue(
            Subject.objects.filter(name="Embedded Networks", code="301", department=self.ece, semester=5).exists()
        )

    def test_admin_subject_add_prefills_and_cancels_back_to_filtered_subjects(self):
        response = self.client.get(
            reverse("admin_subject_add"),
            {"dept": str(self.cse.pk), "sem": "5"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_dept"], str(self.cse.pk))
        self.assertEqual(response.context["selected_semester"], "5")
        self.assertEqual(response.context["cancel_url"], f"{reverse('admin_subjects')}?dept={self.cse.pk}&sem=5")

    def test_admin_subject_edit_updates_subject_and_redirects_to_filtered_list(self):
        subject = Subject.objects.create(
            name="Operating Systems",
            code="CS503",
            department=self.cse,
            semester=5,
            lecture_hours=3,
            tutorial_hours=1,
            practical_hours=0,
            credits=4,
            category="PC",
        )

        response = self.client.post(
            reverse("admin_subject_edit", args=[subject.pk]),
            {
                "name": "Advanced Operating Systems",
                "code": "CS553",
                "department": str(self.cse.pk),
                "semester": "6",
                "lecture_hours": "3",
                "tutorial_hours": "0",
                "practical_hours": "2",
                "credits": "4",
                "category": "PE",
            },
        )

        self.assertRedirects(response, f"{reverse('admin_subjects')}?dept={self.cse.pk}&sem=6")
        subject.refresh_from_db()
        self.assertEqual(subject.name, "Advanced Operating Systems")
        self.assertEqual(subject.code, "CS553")
        self.assertEqual(subject.semester, 6)
        self.assertEqual(subject.practical_hours, 2)
        self.assertEqual(subject.weekly_hours, 5)
        self.assertEqual(subject.category, "PE")

    def test_admin_subject_add_blocks_duplicate_code_in_same_department_even_for_different_semester(self):
        Subject.objects.create(name="Networks", code="CS301", department=self.cse, semester=5)

        response = self.client.post(
            reverse("admin_subject_add"),
            {
                "name": "Advanced Networks",
                "code": "CS301",
                "department": str(self.cse.pk),
                "semester": "6",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Subject.objects.filter(code="CS301", department=self.cse, semester=5).count(), 1)
        self.assertContains(response, 'Subject code')
        self.assertContains(response, 'already taken')
        self.assertContains(response, 'Advanced Networks')
        self.assertContains(response, 'value="CS301"', html=False)

    def test_admin_subject_edit_blocks_duplicate_code_in_same_department(self):
        Subject.objects.create(name="Networks", code="CS301", department=self.cse, semester=5)
        subject = Subject.objects.create(name="Compiler Design", code="CS302", department=self.cse, semester=6)

        response = self.client.post(
            reverse("admin_subject_edit", args=[subject.pk]),
            {
                "name": "Compiler Design",
                "code": "CS301",
                "department": str(self.cse.pk),
                "semester": "6",
                "lecture_hours": "3",
                "tutorial_hours": "0",
                "practical_hours": "0",
                "credits": "4",
                "category": "PC",
            },
        )

        self.assertEqual(response.status_code, 200)
        subject.refresh_from_db()
        self.assertEqual(subject.code, "CS302")
        self.assertContains(response, 'Subject code')
        self.assertContains(response, 'already taken')

    def test_admin_subject_add_blocks_code_longer_than_model_limit(self):
        response = self.client.post(
            reverse("admin_subject_add"),
            {
                "name": "Advanced Network Technologies",
                "code": "ADVANCEDNETWORKTECHNOLOGY101",
                "department": str(self.cse.pk),
                "semester": "7",
                "category": "PE",
                "lecture_hours": "3",
                "tutorial_hours": "0",
                "practical_hours": "0",
                "credits": "3",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Subject code cannot exceed 20 characters.')
        self.assertContains(response, 'value="ADVANCEDNETWORKTECHNOLOGY101"', html=False)
        self.assertFalse(Subject.objects.filter(code="ADVANCEDNETWORKTECHNOLOGY101", department=self.cse).exists())

    def test_admin_hod_add_rejects_duplicate_employee_id(self):
        existing_user = User.objects.create_user(username="hod-existing", password="pass12345")
        HOD.objects.create(
            user=existing_user,
            employee_id="HOD-007",
            department=self.cse,
            qualification="PhD",
            experience_years=12,
            phone_number="8888888888",
            is_active=True,
        )

        response = self.client.post(
            reverse("admin_hod_add"),
            {
                "first_name": "New",
                "last_name": "Hod",
                "username": "new-hod",
                "email": "newhod@example.com",
                "password": "pass12345",
                "employee_id": "HOD-007",
                "department": str(self.ece.pk),
                "qualification": "MTech",
                "experience_years": "6",
                "phone_number": "7777777777",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="new-hod").exists())

    def test_admin_student_add_generates_password_when_blank(self):
        response = self.client.post(
            reverse("admin_student_add"),
            {
                "first_name": "Student",
                "last_name": "User",
                "username": "2024-alpha-cse-001",
                "email": "student1@example.com",
                "password": "",
                "department": str(self.cse.pk),
                "admission_year": "2024",
                "current_semester": "1",
                "status": "ACTIVE",
            },
        )

        self.assertEqual(response.status_code, 302)
        created = User.objects.get(username="2024-alpha-cse-001")
        self.assertTrue(created.has_usable_password())

    def test_admin_student_add_auto_assigns_sections_from_department_capacity(self):
        self.cse.section_capacity = 2
        self.cse.save(update_fields=["section_capacity"])

        for index in range(3):
            response = self.client.post(
                reverse("admin_student_add"),
                {
                    "first_name": f"Student{index}",
                    "last_name": "User",
                    "username": f"2024-alpha-cse-10{index}",
                    "email": f"student{index}@example.com",
                    "password": "pass12345",
                    "department": str(self.cse.pk),
                    "admission_year": "2024",
                    "current_semester": "1",
                    "status": "ACTIVE",
                },
                follow=False,
            )
            self.assertEqual(response.status_code, 302)

        sections = list(
            Student.objects.filter(department=self.cse, admission_year=2024)
            .order_by("roll_number")
            .values_list("section", flat=True)
        )
        self.assertEqual(sections, ["A", "A", "B"])

    def test_admin_dashboard_students_filter_by_year_department_and_semester(self):
        cse_user = User.objects.create_user(username="cse3", password="pass12345", first_name="Cse")
        ece_user = User.objects.create_user(username="ece3", password="pass12345", first_name="Ece")
        Student.objects.create(
            user=cse_user,
            roll_number="2024-ALPHA-CSE-003",
            department=self.cse,
            admission_year=2024,
            current_semester=3,
        )
        Student.objects.create(
            user=ece_user,
            roll_number="2024-ALPHA-ECE-003",
            department=self.ece,
            admission_year=2024,
            current_semester=3,
        )
        old_user = User.objects.create_user(username="cse1old", password="pass12345", first_name="Old")
        Student.objects.create(
            user=old_user,
            roll_number="2023-ALPHA-CSE-001",
            department=self.cse,
            admission_year=2023,
            current_semester=1,
        )

        response = self.client.get(
            reverse("admin_dashboard"),
            {"year": "2024", "dept": str(self.cse.pk), "sem": "3"},
        )

        self.assertEqual(response.status_code, 200)
        students = list(response.context["all_students_full"])
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].roll_number, "2024-ALPHA-CSE-003")
        self.assertEqual(response.context["all_students_filtered_total"], 1)
        self.assertEqual(response.context["student_year_filter"], "2024")
        self.assertEqual(response.context["student_dept_filter"], str(self.cse.pk))
        self.assertEqual(response.context["student_sem_filter"], "3")

    def test_admin_students_export_csv_respects_year_filter(self):
        export_user = User.objects.create_user(username="csv2024", password="pass12345", first_name="Csv")
        Student.objects.create(
            user=export_user,
            roll_number="2024-ALPHA-CSE-010",
            department=self.cse,
            admission_year=2024,
            current_semester=1,
        )
        old_user = User.objects.create_user(username="csv2023", password="pass12345", first_name="OldCsv")
        Student.objects.create(
            user=old_user,
            roll_number="2023-ALPHA-CSE-010",
            department=self.cse,
            admission_year=2023,
            current_semester=1,
        )

        response = self.client.get(reverse("admin_students_export_csv"), {"year": "2024"})

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("2024-ALPHA-CSE-010", content)
        self.assertNotIn("2023-ALPHA-CSE-010", content)

    def test_admin_student_edit_updates_profile_related_records(self):
        student_user = User.objects.create_user(
            username="edit-student",
            password="pass12345",
            email="oldstudent@example.com",
            first_name="Edit",
            last_name="Student",
        )
        student = Student.objects.create(
            user=student_user,
            roll_number="2024-ALPHA-CSE-099",
            department=self.cse,
            admission_year=2024,
            current_semester=1,
        )

        response = self.client.post(
            reverse("admin_student_edit", args=[student.pk]),
            {
                "first_name": "Updated",
                "last_name": "Student",
                "email": "updatedstudent@example.com",
                "department": str(self.cse.pk),
                "admission_year": "2024",
                "current_semester": "2",
                "status": "ACTIVE",
                "admission_type": "regular",
                "entry_semester": "1",
                "date_of_birth": "2006-01-15",
                "gender": "Female",
                "phone_number": "9876543210",
                "alternate_phone": "9123456780",
                "aadhaar_number": "123412341234",
                "blood_group": "O+",
                "nationality": "Indian",
                "category": "OC",
                "college_email": "updated@college.edu",
                "personal_email": "updatedpersonal@example.com",
                "inter_college_name": "Sri Chaitanya",
                "inter_passed_year": "2023",
                "inter_percentage": "92.5",
                "school_name": "ZPHS",
                "school_passed_year": "2021",
                "school_percentage": "95.1",
                "street": "1-2-3 Main Road",
                "city": "Kadapa",
                "state": "AP",
                "pincode": "516001",
                "country": "India",
                "parent_type": "FATHER",
                "parent_name": "Ramesh",
                "parent_phone_number": "9000000000",
                "parent_email": "ramesh@example.com",
                "parent_occupation": "Teacher",
                "emergency_name": "Suresh",
                "emergency_relation": "Brother",
                "emergency_phone_number": "9111111111",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        student.refresh_from_db()
        profile = StudentProfile.objects.get(user=student_user)
        address = Address.objects.get(user=student_user)
        parent = Parent.objects.get(user=student_user)
        emergency = EmergencyContact.objects.get(user=student_user)

        self.assertEqual(student.user.first_name, "Updated")
        self.assertEqual(student.current_semester, 2)
        self.assertEqual(profile.phone_number, "9876543210")
        self.assertEqual(profile.aadhaar_number, "123412341234")
        self.assertEqual(profile.college_email, "updated@college.edu")
        self.assertEqual(address.city, "Kadapa")
        self.assertEqual(parent.name, "Ramesh")
        self.assertEqual(parent.parent_type, "FATHER")
        self.assertEqual(emergency.name, "Suresh")

    def test_admin_student_edit_rejects_invalid_contact_details(self):
        student_user = User.objects.create_user(
            username="invalid-student",
            password="pass12345",
            email="invalid-old@example.com",
        )
        student = Student.objects.create(
            user=student_user,
            roll_number="2024-ALPHA-CSE-120",
            department=self.cse,
            admission_year=2024,
            current_semester=1,
        )

        response = self.client.post(
            reverse("admin_student_edit", args=[student.pk]),
            {
                "first_name": "Invalid",
                "last_name": "Student",
                "email": "not-an-email",
                "department": str(self.cse.pk),
                "admission_year": "2024",
                "current_semester": "2",
                "status": "ACTIVE",
                "admission_type": "regular",
                "entry_semester": "3",
                "phone_number": "12345",
                "aadhaar_number": "1234",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        student.refresh_from_db()
        self.assertEqual(student.user.email, "invalid-old@example.com")
        self.assertFalse(StudentProfile.objects.filter(user=student_user).exists())

    def test_student_profile_edit_page_shows_admin_managed_academic_details(self):
        student_user = User.objects.create_user(
            username="student-profile",
            password="pass12345",
            email="student-profile@example.com",
        )
        student = Student.objects.create(
            user=student_user,
            roll_number="2024-ALPHA-CSE-140",
            department=self.cse,
            admission_year=2024,
            current_semester=1,
        )
        StudentProfile.objects.create(
            user=student_user,
            date_of_birth="2006-02-01",
            gender="Female",
            phone_number="9876543210",
            aadhaar_number="123412341234",
            inter_college_name="Narayana",
            inter_passed_year=2023,
            inter_percentage=94.2,
            school_name="ABC School",
            school_passed_year=2021,
            school_percentage=95.0,
            category="BC",
            college_email="student@college.edu",
            personal_email="student.personal@example.com",
        )
        Parent.objects.create(
            user=student_user,
            parent_type="MOTHER",
            name="Lakshmi",
            phone_number="9000000000",
        )
        self.client.force_login(student_user)

        response = self.client.get(reverse("student_profile_edit"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Academic Details")
        self.assertContains(response, "Narayana")
        self.assertContains(response, "student@college.edu")
        self.assertContains(response, "Mother")

    def test_student_profile_edit_does_not_change_parent_details(self):
        student_user = User.objects.create_user(
            username="student-parent-lock",
            password="pass12345",
            email="student-parent-lock@example.com",
            first_name="Lock",
            last_name="Test",
        )
        student = Student.objects.create(
            user=student_user,
            roll_number="2024-ALPHA-CSE-141",
            department=self.cse,
            admission_year=2024,
            current_semester=1,
        )
        UserRole.objects.create(user=student_user, role=4, college=self.college)
        StudentProfile.objects.create(
            user=student_user,
            date_of_birth="2006-02-01",
            gender="Female",
            phone_number="9876543210",
            aadhaar_number="123412341235",
            inter_college_name="Narayana",
            inter_passed_year=2023,
            inter_percentage=94.2,
            school_name="ABC School",
            school_passed_year=2021,
            school_percentage=95.0,
        )
        Parent.objects.create(
            user=student_user,
            parent_type="FATHER",
            name="Original Parent",
            phone_number="9000000000",
            email="original.parent@example.com",
            occupation="Farmer",
        )
        self.client.force_login(student_user)

        response = self.client.post(
            reverse("student_profile_edit"),
            {
                "first_name": "Lock",
                "last_name": "Test",
                "email": "student-parent-lock@example.com",
                "phone_number": "9876543210",
                "alternate_phone": "9123456789",
                "date_of_birth": "2006-02-01",
                "gender": "Female",
                "blood_group": "A+",
                "nationality": "Indian",
                "street": "Street 1",
                "city": "Kadapa",
                "state": "AP",
                "pincode": "516001",
                "country": "India",
                "parent_email": "changed.parent@example.com",
                "parent_occupation": "Engineer",
                "emergency_name": "Emergency",
                "emergency_relation": "Brother",
                "emergency_phone_number": "9111111111",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        parent = Parent.objects.get(user=student_user)
        self.assertEqual(parent.email, "original.parent@example.com")
        self.assertEqual(parent.occupation, "Farmer")

    def test_registration_request_cannot_be_marked_converted_without_student_creation(self):
        reg = RegistrationRequest.objects.create(
            college=self.college,
            desired_department=self.cse,
            first_name="Req",
            last_name="Student",
            email="req-student@example.com",
            status="SUBMITTED",
        )

        response = self.client.post(
            reverse("admin_registration_request_update", args=[reg.pk]),
            {"action": "CONVERTED"},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        reg.refresh_from_db()
        self.assertEqual(reg.status, "SUBMITTED")

    def test_registration_request_can_be_marked_needs_correction_with_review_metadata(self):
        reg = RegistrationRequest.objects.create(
            college=self.college,
            desired_department=self.cse,
            first_name="Needs",
            last_name="Correction",
            email="needs-correction@example.com",
        )

        response = self.client.post(
            reverse("admin_registration_request_update", args=[reg.pk]),
            {
                "action": "NEEDS_CORRECTION",
                "review_notes": "Academic records are incomplete.",
                "correction_fields": "Upload intermediate memo and corrected phone number.",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        reg.refresh_from_db()
        self.assertEqual(reg.status, "NEEDS_CORRECTION")
        self.assertEqual(reg.reviewed_by, self.admin_user)
        self.assertEqual(reg.review_notes, "Academic records are incomplete.")
        self.assertEqual(reg.correction_fields, "Upload intermediate memo and corrected phone number.")
        self.assertIsNotNone(reg.reviewed_at)

    def test_converting_approved_registration_request_marks_it_converted(self):
        reg = RegistrationRequest.objects.create(
            college=self.college,
            desired_department=self.cse,
            first_name="Approved",
            last_name="Applicant",
            email="approved@example.com",
            phone_number="9000000000",
            admission_year=2024,
            current_semester=1,
            status="APPROVED",
            review_notes="All documents verified.",
            reviewed_by=self.admin_user,
        )

        response = self.client.post(
            reverse("admin_student_add"),
            {
                "request_id": str(reg.pk),
                "first_name": "Approved",
                "last_name": "Applicant",
                "username": "2024-alpha-cse-001",
                "email": "approved@example.com",
                "password": "",
                "department": str(self.cse.pk),
                "admission_year": "2024",
                "current_semester": "1",
                "status": "ACTIVE",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        reg.refresh_from_db()
        self.assertEqual(reg.status, "CONVERTED")
        self.assertTrue(Student.objects.filter(user__email="approved@example.com").exists())

    def test_non_approved_registration_request_cannot_be_converted(self):
        reg = RegistrationRequest.objects.create(
            college=self.college,
            desired_department=self.cse,
            first_name="Submitted",
            last_name="Applicant",
            email="submitted@example.com",
            admission_year=2024,
            current_semester=1,
            status="SUBMITTED",
        )

        response = self.client.get(
            reverse("admin_student_add"),
            {"request": str(reg.pk)},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("admin_registration_requests"))
        self.assertFalse(Student.objects.filter(user__email="submitted@example.com").exists())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_registration_request_review_sends_email_to_applicant(self):
        reg = RegistrationRequest.objects.create(
            college=self.college,
            desired_department=self.cse,
            first_name="Review",
            last_name="Target",
            email="review-target@example.com",
        )

        response = self.client.post(
            reverse("admin_registration_request_update", args=[reg.pk]),
            {
                "action": "NEEDS_CORRECTION",
                "review_notes": "One document is unclear.",
                "correction_fields": "Upload a clearer intermediate marks memo.",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["review-target@example.com"])
        self.assertIn("needs correction", mail.outbox[0].subject.lower())
        self.assertIn("Upload a clearer intermediate marks memo.", mail.outbox[0].body)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_registration_submission_sends_received_email(self):
        invite = RegistrationInvite.objects.create(
            college=self.college,
            department=self.cse,
            invited_email="new-applicant@example.com",
            created_by=self.admin_user,
        )
        self.client.logout()

        response = self.client.post(
            reverse("register") + f"?token={invite.token}",
            {
                "first_name": "New",
                "last_name": "Applicant",
                "email": "new-applicant@example.com",
                "phone_number": "9000000001",
                "admission_year": "2024",
                "current_semester": "1",
                "desired_department": str(self.cse.pk),
                "message": "Looking forward to joining.",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["new-applicant@example.com"])
        self.assertIn("received", mail.outbox[0].subject.lower())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_conversion_sends_account_created_email_and_notification(self):
        reg = RegistrationRequest.objects.create(
            college=self.college,
            desired_department=self.cse,
            first_name="Account",
            last_name="Created",
            email="account-created@example.com",
            admission_year=2024,
            current_semester=1,
            status="APPROVED",
        )

        response = self.client.post(
            reverse("admin_student_add"),
            {
                "request_id": str(reg.pk),
                "first_name": "Account",
                "last_name": "Created",
                "username": "2024-alpha-cse-002",
                "email": "account-created@example.com",
                "password": "",
                "department": str(self.cse.pk),
                "admission_year": "2024",
                "current_semester": "1",
                "status": "ACTIVE",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        created_user = User.objects.get(username="2024-alpha-cse-002")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["account-created@example.com"])
        self.assertIn("account created", mail.outbox[0].subject.lower())
        self.assertTrue(Notification.objects.filter(user=created_user, message__icontains="student account").exists())

    def test_bulk_import_skips_duplicate_roll_without_creating_orphan_user(self):
        existing_user = User.objects.create_user("existing-stu", "existing@example.com", "pass12345")
        Student.objects.create(
            user=existing_user,
            roll_number="2024-ALPHA-CSE-050",
            department=self.cse,
            admission_year=2024,
            current_semester=1,
        )

        csv_bytes = (
            "username,email,first_name,last_name,dept_code,admission_year,current_semester,roll_number\n"
            "new-import,new-import@example.com,New,Import,CSE,2024,1,2024-ALPHA-CSE-050\n"
        ).encode("utf-8")

        response = self.client.post(
            reverse("admin_bulk_import"),
            {
                "import_type": "STUDENT",
                "csv_file": SimpleUploadedFile("students.csv", csv_bytes, content_type="text/csv"),
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username="new-import").exists())


class LoginAndPaymentSafetyTests(TestCase):
    def setUp(self):
        self.college = College.objects.create(name="Alpha College", code="ALPHA")
        self.other_college = College.objects.create(name="Beta College", code="BETA")

        self.student_user = User.objects.create_user(
            username="student1",
            password="safe-pass-123",
            email="student1@example.com",
            first_name="Stu",
            last_name="Dent",
        )
        self.student_role = UserRole.objects.create(user=self.student_user, role=4, college=self.college)
        self.dept = Department.objects.create(college=self.college, name="Computer Science", code="CSE")
        self.student = Student.objects.create(
            user=self.student_user,
            roll_number="2024-ALPHA-CSE-001",
            department=self.dept,
            admission_year=2024,
            current_semester=1,
        )
        self.fee = Fee.objects.create(
            student=self.student,
            total_amount=10000,
            paid_amount=0,
            semester=1,
            academic_year="2024-25",
            status="PENDING",
        )

        self.alpha_admin = User.objects.create_user("alphaadmin", "alpha-admin@example.com", "pass12345")
        self.beta_admin = User.objects.create_user("betaadmin", "beta-admin@example.com", "pass12345")
        UserRole.objects.create(user=self.alpha_admin, role=1, college=self.college)
        UserRole.objects.create(user=self.beta_admin, role=1, college=self.other_college)

    def test_login_rejects_external_next_redirect(self):
        session = self.client.session
        session["captcha_answer"] = 5
        session["captcha_q"] = "2 + 3"
        session.save()

        response = self.client.post(
            reverse("login") + "?next=https://evil.example/phish",
            {
                "username": "student1",
                "password": "safe-pass-123",
                "captcha": "5",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("dashboard"))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_payment_notification_goes_only_to_same_college_admins(self):
        self.client.force_login(self.student_user)
        payment = Payment.objects.create(
            user=self.student_user,
            fee=self.fee,
            amount=500,
            payment_type="TUITION",
            transaction_id="order_test_123",
            status="PENDING",
            payment_method="RAZORPAY",
        )

        class DummyUtility:
            @staticmethod
            def verify_payment_signature(_payload):
                return True

        class DummyClient:
            utility = DummyUtility()

        with patch("students.views._legacy._get_razorpay_client", return_value=DummyClient()):
            response = self.client.post(
                reverse("razorpay_verify_payment"),
                {
                    "razorpay_order_id": payment.transaction_id,
                    "razorpay_payment_id": "pay_123",
                    "razorpay_signature": "sig_123",
                },
                follow=False,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["alpha-admin@example.com"])

    def test_manual_library_payment_does_not_reduce_tuition_balance(self):
        self.client.force_login(self.student_user)

        response = self.client.post(
            reverse("student_fee_payment"),
            {
                "manual_payment": "1",
                "amount": "250",
                "payment_method": "Cash Counter",
                "fee_type": "LIBRARY",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.fee.refresh_from_db()
        self.assertEqual(self.fee.paid_amount, 0)
        payment = Payment.objects.get(user=self.student_user, payment_type="LIBRARY")
        self.assertEqual(payment.status, "SUCCESS")


class FacultyAndExamWorkflowTests(TestCase):
    def setUp(self):
        self.college = College.objects.create(name="Alpha College", code="ALPHA")
        self.other_college = College.objects.create(name="Beta College", code="BETA")
        self.dept = Department.objects.create(college=self.college, name="Computer Science", code="CSE")
        self.other_dept = Department.objects.create(college=self.other_college, name="Computer Science", code="CSE")

        self.faculty_user = User.objects.create_user("faculty1", "faculty1@example.com", "pass12345")
        self.faculty = Faculty.objects.create(
            user=self.faculty_user,
            employee_id="FAC-001",
            department=self.dept,
            designation="Assistant Professor",
            qualification="MTech",
            experience_years=5,
            phone_number="9999999999",
        )
        UserRole.objects.create(user=self.faculty_user, role=3, college=self.college)

        self.subject = Subject.objects.create(name="Data Structures", code="CS201", department=self.dept, semester=3)
        FacultySubject.objects.create(faculty=self.faculty, subject=self.subject)

        self.student_user = User.objects.create_user("stu1", "stu1@example.com", "pass12345", first_name="Stu")
        self.student = Student.objects.create(
            user=self.student_user,
            roll_number="2024-ALPHA-CSE-001",
            department=self.dept,
            admission_year=2024,
            current_semester=3,
        )

    def test_faculty_can_update_existing_attendance_for_same_subject_and_date(self):
        self.client.force_login(self.faculty_user)
        with patch.dict(os.environ, {"ATTENDANCE_TIME_LOCK_DISABLED": "1"}):
            first = self.client.post(
                reverse("faculty_mark_attendance", args=[self.subject.pk]),
                {
                    "date": "2026-04-01",
                    f"status_{self.student.pk}": "PRESENT",
                },
                follow=False,
            )
            second = self.client.post(
                reverse("faculty_mark_attendance", args=[self.subject.pk]),
                {
                    "date": "2026-04-01",
                    f"status_{self.student.pk}": "ABSENT",
                },
                follow=False,
            )

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(AttendanceSession.objects.filter(subject=self.subject, date="2026-04-01").count(), 1)
        attendance = Attendance.objects.get(session__subject=self.subject, student=self.student)
        self.assertEqual(attendance.status, "ABSENT")

    def test_faculty_cannot_enter_marks_for_exam_from_other_college(self):
        self.client.force_login(self.faculty_user)
        exam = Exam.objects.create(
            college=self.other_college,
            name="Other College Exam",
            semester=3,
            start_date="2026-04-01",
            end_date="2026-04-02",
            created_by=self.faculty_user,
        )

        response = self.client.get(reverse("faculty_enter_marks", args=[self.subject.pk, exam.pk]))

        self.assertEqual(response.status_code, 404)


class StudentAcademicWorkflowTests(TestCase):
    def setUp(self):
        self.college = College.objects.create(name="Alpha College", code="ALPHA")
        self.dept = Department.objects.create(college=self.college, name="Computer Science", code="CSE")
        self.student_user = User.objects.create_user("student1", "student1@example.com", "pass12345")
        self.student = Student.objects.create(
            user=self.student_user,
            roll_number="2024-ALPHA-CSE-001",
            department=self.dept,
            admission_year=2024,
            current_semester=3,
        )
        UserRole.objects.create(user=self.student_user, role=4, college=self.college)

        self.exam = Exam.objects.create(
            college=self.college,
            name="Semester End Exam",
            semester=3,
            start_date="2026-04-10",
            end_date="2026-04-20",
            created_by=self.student_user,
        )
        self.failed_subject = Subject.objects.create(name="DS", code="CS201", department=self.dept, semester=3)
        self.passed_subject = Subject.objects.create(name="DBMS", code="CS202", department=self.dept, semester=3)
        self.failed_marks = Marks.objects.create(student=self.student, subject=self.failed_subject, exam=self.exam, marks_obtained=20, max_marks=100, grade="F")
        Marks.objects.create(student=self.student, subject=self.passed_subject, exam=self.exam, marks_obtained=78, max_marks=100, grade="A")

    def test_supply_registration_rejects_non_failed_subject_selection(self):
        Exam.objects.create(
            college=self.college,
            name="Supply Exam Window",
            semester=1,
            start_date="2026-03-15",
            end_date="2026-03-16",
            created_by=self.student_user,
        )
        self.client.force_login(self.student_user)

        response = self.client.post(
            reverse("student_supply_exam_register"),
            {"subjects": [str(self.passed_subject.pk)]},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(SupplyExamRegistration.objects.filter(student=self.student, exam=self.exam).exists())

    def test_supply_registration_allows_new_selection_when_old_paid_registration_is_stale(self):
        old_subject_one = Subject.objects.create(name="OS", code="CS101", department=self.dept, semester=1)
        old_subject_two = Subject.objects.create(name="Maths", code="CS102", department=self.dept, semester=1)
        old_exam = Exam.objects.create(
            college=self.college,
            name="Old Supply Exam",
            semester=1,
            start_date="2026-03-01",
            end_date="2026-03-02",
            created_by=self.student_user,
        )
        old_payment = Payment.objects.create(
            user=self.student_user,
            amount=1500,
            payment_type="SUPPLY_EXAM",
            transaction_id="order_old_supply",
            status="SUCCESS",
            payment_method="RAZORPAY",
        )
        old_reg = SupplyExamRegistration.objects.create(
            student=self.student,
            exam=old_exam,
            total_fee=1500,
            payment=old_payment,
            status="PAID",
        )
        old_reg.subjects.set([old_subject_one, old_subject_two, self.failed_subject])

        self.client.force_login(self.student_user)

        response = self.client.post(
            reverse("student_supply_exam_register"),
            {"subjects": [str(self.failed_subject.pk)]},
            follow=False,
        )

        old_reg.refresh_from_db()
        self.assertRedirects(response, reverse("student_supply_exam_pay", args=[old_reg.pk]))
        self.assertEqual(old_reg.status, "PENDING")
        self.assertIsNone(old_reg.payment)
        self.assertEqual(list(old_reg.subjects.values_list("id", flat=True)), [self.failed_subject.pk])

    def test_revaluation_payment_flow_blocks_duplicate_existing_request(self):
        RevaluationRequest.objects.create(student=self.student, marks=self.failed_marks, status="PENDING")
        self.client.force_login(self.student_user)

        response = self.client.post(
            reverse("student_reval_fee_pay", args=[self.failed_marks.pk]),
            {"confirm_pay": "1"},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Payment.objects.filter(user=self.student_user, payment_type="REVALUATION").count(), 0)

    def test_supply_exam_receipt_lists_paid_subjects(self):
        supply_exam = Exam.objects.create(
            college=self.college,
            name="Supply Exam Window",
            semester=1,
            start_date="2026-03-15",
            end_date="2026-03-16",
            created_by=self.student_user,
        )
        extra_subject = Subject.objects.create(name="OS", code="CS203", department=self.dept, semester=2)
        payment = Payment.objects.create(
            user=self.student_user,
            amount=1000,
            payment_type="SUPPLY_EXAM",
            transaction_id="order_supply_receipt",
            status="SUCCESS",
            payment_method="RAZORPAY",
        )
        registration = SupplyExamRegistration.objects.create(
            student=self.student,
            exam=supply_exam,
            total_fee=1000,
            payment=payment,
            status="PAID",
        )
        registration.subjects.set([self.failed_subject, extra_subject])

        self.client.force_login(self.student_user)

        response = self.client.get(reverse("student_payment_receipt", args=[payment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Applied Supply Subjects")
        self.assertContains(response, self.failed_subject.code)
        self.assertContains(response, self.failed_subject.name)
        self.assertContains(response, extra_subject.code)
        self.assertContains(response, extra_subject.name)

    def test_exam_fee_payment_is_blocked_when_tuition_balance_is_pending(self):
        Fee.objects.create(
            student=self.student,
            total_amount=50000,
            paid_amount=45000,
            semester=3,
            academic_year="2026-27",
            status="PARTIAL",
        )
        self.client.force_login(self.student_user)

        response = self.client.post(
            reverse("razorpay_create_order"),
            {"amount": "1500", "fee_type": "EXAM"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("tuition balance", response.json()["error"].lower())

    def test_exam_fee_payment_is_blocked_when_attendance_is_not_eligible(self):
        Fee.objects.create(
            student=self.student,
            total_amount=50000,
            paid_amount=50000,
            semester=3,
            academic_year="2026-27",
            status="PAID",
        )
        self.client.force_login(self.student_user)

        with patch("students.views._legacy._compute_eligibility") as mocked_eligibility:
            mocked_eligibility.return_value = {
                "eligible": False,
                "reasons": ["Overall: 62% < 75% required"],
            }
            response = self.client.post(
                reverse("razorpay_create_order"),
                {"amount": "1500", "fee_type": "EXAM"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("attendance", response.json()["error"].lower())

    def test_exam_fee_payment_is_blocked_when_no_attendance_is_recorded(self):
        Fee.objects.create(
            student=self.student,
            total_amount=50000,
            paid_amount=50000,
            semester=3,
            academic_year="2026-27",
            status="PAID",
        )
        self.client.force_login(self.student_user)

        response = self.client.post(
            reverse("razorpay_create_order"),
            {"amount": "1500", "fee_type": "EXAM"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("attendance is recorded", response.json()["error"].lower())

    def test_exam_fee_receipt_lists_current_semester_subjects(self):
        fee = Fee.objects.create(
            student=self.student,
            total_amount=50000,
            paid_amount=50000,
            semester=3,
            academic_year="2026-27",
            status="PAID",
        )
        payment = Payment.objects.create(
            user=self.student_user,
            fee=fee,
            amount=1500,
            payment_type="EXAM",
            transaction_id="order_exam_receipt",
            status="SUCCESS",
            payment_method="RAZORPAY",
        )

        self.client.force_login(self.student_user)

        response = self.client.get(reverse("student_payment_receipt", args=[payment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Current Semester Exam Subjects")
        self.assertContains(response, self.failed_subject.code)
        self.assertContains(response, self.failed_subject.name)
        self.assertContains(response, self.passed_subject.code)
        self.assertContains(response, self.passed_subject.name)


class StudentSectionTimetableTests(TestCase):
    def setUp(self):
        self.college = College.objects.create(name="Alpha College", code="ALPHA")
        self.dept = Department.objects.create(college=self.college, name="Computer Science", code="CSE", section_capacity=2)
        self.student_user = User.objects.create_user("sectionstu", "sectionstu@example.com", "pass12345")
        UserRole.objects.create(user=self.student_user, role=4, college=self.college)
        self.student = Student.objects.create(
            user=self.student_user,
            roll_number="2024-ALPHA-CSE-001",
            department=self.dept,
            admission_year=2024,
            current_semester=3,
            section="A",
        )
        self.faculty_user = User.objects.create_user("faculty-sec", "faculty-sec@example.com", "pass12345")
        UserRole.objects.create(user=self.faculty_user, role=3, college=self.college)
        self.faculty = Faculty.objects.create(
            user=self.faculty_user,
            employee_id="FAC-SEC-1",
            department=self.dept,
            designation="Assistant Professor",
            qualification="MTech",
            experience_years=4,
            phone_number="9999999998",
        )
        self.subject = Subject.objects.create(name="Algorithms", code="CS301", department=self.dept, semester=3)
        self.room_a = Classroom.objects.create(college=self.college, room_number="A-101", capacity=60)
        self.room_b = Classroom.objects.create(college=self.college, room_number="A-102", capacity=60)
        Timetable.objects.create(
            subject=self.subject,
            faculty=self.faculty,
            day_of_week="MON",
            start_time=time(9, 0),
            end_time=time(10, 0),
            classroom=self.room_a,
            section="A",
        )
        Timetable.objects.create(
            subject=self.subject,
            faculty=self.faculty,
            day_of_week="MON",
            start_time=time(10, 0),
            end_time=time(11, 0),
            classroom=self.room_b,
            section="B",
        )

    def test_student_dashboard_shows_only_matching_section_timetable(self):
        self.client.force_login(self.student_user)

        response = self.client.get(reverse("student_dashboard"))

        self.assertEqual(response.status_code, 200)
        monday_slots = next(slots for day_code, _label, slots in response.context["week_timetable_list"] if day_code == "MON")
        self.assertEqual(len(monday_slots), 1)
        self.assertEqual(monday_slots[0].section, "A")
