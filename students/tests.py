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
    College,
    Classroom,
    Department,
    Exam,
    Faculty,
    FacultySubject,
    Fee,
    HOD,
    Marks,
    Notification,
    Payment,
    RegistrationInvite,
    RegistrationRequest,
    RevaluationRequest,
    Student,
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

        response = self.client.get(reverse("admin_subjects"), {"dept": str(self.cse.pk)})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_panel/subjects.html")
        subjects = list(response.context["subjects"])
        self.assertEqual(len(subjects), 1)
        self.assertEqual(subjects[0].department, self.cse)

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

        self.assertRedirects(response, reverse("admin_subjects"))
        self.assertTrue(
            Subject.objects.filter(name="Embedded Networks", code="301", department=self.ece, semester=5).exists()
        )

    def test_admin_subject_add_blocks_duplicate_in_same_department_and_semester(self):
        Subject.objects.create(name="Networks", code="CS301", department=self.cse, semester=5)

        response = self.client.post(
            reverse("admin_subject_add"),
            {
                "name": "Advanced Networks",
                "code": "CS301",
                "department": str(self.cse.pk),
                "semester": "5",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Subject.objects.filter(code="CS301", department=self.cse, semester=5).count(), 1)

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
        self.client.force_login(self.student_user)

        response = self.client.post(
            reverse("student_supply_exam_register"),
            {"subjects": [str(self.passed_subject.pk)]},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(SupplyExamRegistration.objects.filter(student=self.student, exam=self.exam).exists())

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
