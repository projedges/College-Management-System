from datetime import timedelta
from uuid import uuid4

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


# USER ROLE MODEL

class UserRole(models.Model):
    ROLE_CHOICES = (
        (1, 'College Admin'),
        (2, 'HOD'),
        (3, 'Faculty'),
        (4, 'Student'),
        (5, 'Lab Staff'),
        (6, 'Principal'),
        (7, 'Exam Controller'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.IntegerField(choices=ROLE_CHOICES, default=4)
    college = models.ForeignKey('College', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_roles')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

# COLLEGE MODEL
class College(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=30, unique=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    
    # Branding & Contact Identity
    logo = models.ImageField(upload_to='college_logos/', null=True, blank=True)
    
    # ID Generation Rules
    student_id_rule = models.CharField(max_length=100, default='{YEAR}-{CODE}-{DEPT}-{SERIAL}')
    faculty_id_rule = models.CharField(max_length=100, default='FAC-{CODE}-{SERIAL}')

    email = models.EmailField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_logo_url(self):
        try:
            return self.logo.url
        except (ValueError, AttributeError):
            return f"https://placehold.co/400x400?text={self.code}+Logo"


# DEPARTMENT MODEL
class Department(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True, related_name='departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)

    description = models.TextField(null=True, blank=True)
    established_year = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            ('college', 'name'),
            ('college', 'code'),
        )

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    
    
# STUDENT MODEL
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    roll_number = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)    
    admission_year = models.IntegerField()
    current_semester = models.IntegerField()

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('GRADUATED', 'Graduated'),
        ('DROPPED', 'Dropped'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.roll_number


# STUDENT PROFILE MODEL
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Basic Info — first_name/last_name live on User model, not duplicated here
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)

    # Contact
    phone_number = models.CharField(max_length=15)

    # Government ID
    aadhaar_number = models.CharField(max_length=20, unique=True)

    # Academic History
    inter_college_name = models.CharField(max_length=150)
    inter_passed_year = models.IntegerField()
    inter_percentage = models.FloatField()

    school_name = models.CharField(max_length=150)
    school_passed_year = models.IntegerField()
    school_percentage = models.FloatField()

    # Extra
    blood_group = models.CharField(max_length=5, null=True, blank=True)
    nationality = models.CharField(max_length=50, default='Indian')
    category = models.CharField(max_length=20, null=True, blank=True)

    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def get_photo_url(self):
        try:
            return self.profile_photo.url
        except (ValueError, AttributeError):
            return "https://placehold.co/300x300?text=Profile+Photo"


# ADDRESS MODEL
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    street = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default='India')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.city}, {self.state}"


# PARENT MODEL
class Parent(models.Model):
    PARENT_TYPE = (
        ('FATHER', 'Father'),
        ('MOTHER', 'Mother'),
        ('GUARDIAN', 'Guardian'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    parent_type = models.CharField(max_length=10, choices=PARENT_TYPE)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'parent_type')

    def __str__(self):
        return f"{self.parent_type} - {self.name}"


# EMERGENCY CONTACT MODEL
class EmergencyContact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    relation = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return self.name


# USER SECURITY MODEL
class UserSecurity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    login_attempts = models.IntegerField(default=0)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    locked_until = models.DateTimeField(null=True, blank=True,
                                        help_text='Account locked until this time after too many failed logins')

    def __str__(self):
        return self.user.username

    @property
    def is_locked(self):
        if self.login_attempts < 5:
            return False
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False

class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    duration_years = models.IntegerField()

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} - {self.course}"

# ADMIN PROFILE
class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    designation = models.CharField(max_length=100, default="System Admin")

    def __str__(self):
        return self.full_name


# ANNOUNCEMENTS
class Announcement(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True, related_name='announcements')
    title = models.CharField(max_length=200)
    message = models.TextField()

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# NOTIFICATIONS
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    message = models.TextField()
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Notification"


class RegistrationRequest(models.Model):
    STATUS_CHOICES = (
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('NEEDS_CORRECTION', 'Needs Correction'),
        ('APPROVED', 'Approved'),
        ('CONVERTED', 'Converted'),
        ('REJECTED', 'Rejected'),
    )

    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True, related_name='registration_requests')
    desired_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15, blank=True)
    admission_year = models.IntegerField(null=True, blank=True)
    current_semester = models.IntegerField(null=True, blank=True)
    message = models.TextField(blank=True)
    
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)

    # New Fields for Registration
    photo_id = models.ImageField(upload_to='registration_ids/', null=True, blank=True)
    aadhaar_number = models.CharField(max_length=20, blank=True)
    inter_college_name = models.CharField(max_length=150, blank=True)
    inter_passed_year = models.IntegerField(null=True, blank=True)
    inter_percentage = models.FloatField(null=True, blank=True)
    school_name = models.CharField(max_length=150, blank=True)
    school_passed_year = models.IntegerField(null=True, blank=True)
    school_percentage = models.FloatField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_registration_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    correction_fields = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"


class RegistrationInvite(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='registration_invites')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    invited_email = models.EmailField()
    admission_year = models.IntegerField(null=True, blank=True)
    current_semester = models.IntegerField(null=True, blank=True)
    token = models.CharField(max_length=64, unique=True, default=uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_registration_invites')
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_usable(self):
        if self.used_at:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    def __str__(self):
        return f"{self.invited_email} - {self.college.code}"


class HelpDeskTicket(models.Model):
    ISSUE_TYPES = (
        ('ACCESS', 'Access / Login'),
        ('ACADEMIC', 'Academic'),
        ('FEES', 'Fees'),
        ('TECHNICAL', 'Technical'),
        ('GENERAL', 'General'),
    )

    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    )

    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True, related_name='helpdesk_tickets')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='helpdesk_tickets')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    issue_type = models.CharField(max_length=20, choices=ISSUE_TYPES, default='GENERAL')
    subject = models.CharField(max_length=150)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} - {self.email}"

class TicketComment(models.Model):
    ticket = models.ForeignKey(HelpDeskTicket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_admin_reply = models.BooleanField(default=False)

    def __str__(self):
        return f"Comment on {self.ticket.subject} by {self.author.username}"


# ACTIVITY LOGS (SECURITY 🔐)
class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"




# PAYMENT SYSTEM 💰
class Payment(models.Model):
    PAYMENT_STATUS = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fee = models.ForeignKey('Fee', on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=50)  # tuition, exam fee

    transaction_id = models.CharField(max_length=100, unique=True)

    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='PENDING')

    payment_method = models.CharField(max_length=50)  # UPI, Card, NetBanking

    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount}"


# PAYMENT RECEIPT
class PaymentReceipt(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)

    receipt_file = models.FileField(upload_to='receipts/')
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt {self.payment.transaction_id}"


# SYSTEM REPORTS
class SystemReport(models.Model):
    REPORT_TYPES = (
        ('ATTENDANCE', 'Attendance'),
        ('RESULT', 'Result'),
        ('PAYMENT', 'Payment'),
    )

    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)

    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='reports/')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.report_type


# SYSTEM SETTINGS
class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


# ROLE PERMISSIONS (ADVANCED 🔥)
class Permission(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.IntegerField(choices=UserRole.ROLE_CHOICES)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"Role {self.role} - {self.permission.name}"
    



class HOD(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    employee_id = models.CharField(max_length=50, unique=True)

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='hods'
    )
    is_active = models.BooleanField(default=True)

    phone_number = models.CharField(max_length=15)
    qualification = models.CharField(max_length=100)
    experience_years = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['department'],
                condition=models.Q(is_active=True),
                name='unique_active_hod_per_department'
            )
        ]

    def __str__(self):
        return f"HOD - {self.user.username}"
    

class Principal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    college = models.OneToOneField(College, on_delete=models.CASCADE, related_name='principal')
    employee_id = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=15)
    qualification = models.CharField(max_length=100)
    experience_years = models.IntegerField()

    def __str__(self):
        return f"Principal - {self.user.username}"
    

    
# FACULTY MODEL
class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    employee_id = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    designation = models.CharField(max_length=100)  # Assistant Prof, etc.
    qualification = models.CharField(max_length=100)
    experience_years = models.IntegerField()

    phone_number = models.CharField(max_length=15)
    is_deleted = models.BooleanField(default=False)

    joined_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class FacultyAvailability(models.Model):
    DAYS = (
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
    )

    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week = models.CharField(max_length=3, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('faculty', 'day_of_week', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.faculty} - {self.day_of_week} {self.start_time}-{self.end_time}"


# SUBJECT MODEL
class Subject(models.Model):
    CATEGORY_CHOICES = [
        ('PC',    'Program Core'),
        ('PE',    'Program Elective'),
        ('OE',    'Open Elective'),
        ('BS',    'Basic Science'),
        ('PC/BS', 'Program Core / Basic Science'),
        ('MC',    'Mandatory Course'),
        ('PW',    'Project Work'),
        ('AC',    'Audit Course'),
        ('HS',    'Humanities & Social Science'),
        ('ES',    'Engineering Science'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)  # unique per department, not globally

    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.IntegerField()
    weekly_hours = models.IntegerField(default=3)

    # Syllabus structure fields (L-T-P-C format used by Indian universities)
    lecture_hours   = models.IntegerField(default=3, help_text="Lecture hours per week (L)")
    tutorial_hours  = models.IntegerField(default=0, help_text="Tutorial hours per week (T)")
    practical_hours = models.IntegerField(default=0, help_text="Practical/Lab hours per week (P)")
    credits         = models.IntegerField(default=3, help_text="Credits (C)")
    category        = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='PC', help_text="Subject category")

    class Meta:
        # Two departments can have the same subject code (e.g. MATH101 in CSE and ECE)
        # but within a department each code must be unique per semester
        unique_together = ('department', 'code')

    def __str__(self):
        return self.name


# FACULTY SUBJECT ASSIGNMENT
class FacultySubject(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.faculty} - {self.subject}"


# HOD APPROVAL SYSTEM
class HODApproval(models.Model):
    APPROVAL_TYPE = (
        ('LEAVE', 'Leave Request'),
        ('EVENT', 'Event Approval'),
        ('COURSE', 'Course Approval'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    approval_type = models.CharField(max_length=20, choices=APPROVAL_TYPE)
    description = models.TextField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hod_reviews')

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.approval_type} - {self.status}"


# FACULTY ATTENDANCE MANAGEMENT
class FacultyAttendance(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    date = models.DateField()

    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LEAVE', 'Leave'),
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.faculty} - {self.date}"


# FACULTY PERFORMANCE TRACKING
class FacultyPerformance(models.Model):
    faculty = models.OneToOneField(Faculty, on_delete=models.CASCADE)

    rating = models.FloatField()  # out of 5
    feedback = models.TextField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.faculty} - {self.rating}"
    


class CourseSubject(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    semester = models.IntegerField()

    def __str__(self):
        return f"{self.course.name} - {self.subject.name}"

class Classroom(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='classrooms', null=True)
    room_number = models.CharField(max_length=20)
    building = models.CharField(max_length=100, blank=True, default='')
    capacity = models.IntegerField()

    class Meta:
        unique_together = ('college', 'room_number')

    def __str__(self):
        if self.building:
            return f"{self.building} - {self.room_number}"
        return f"{self.room_number} ({self.college.code if self.college else 'Global'})"

class Timetable(models.Model):
    DAYS = (
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
    )

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    day_of_week = models.CharField(max_length=3, choices=DAYS)

    start_time = models.TimeField()
    end_time = models.TimeField()

    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)

    # Section support — e.g. "A", "B", "C" for same subject taught by different faculty
    section = models.CharField(max_length=10, blank=True, default='',
                               help_text="Section label e.g. A, B, C. Leave blank if no sections.")

    def __str__(self):
        sec = f" [{self.section}]" if self.section else ""
        return f"{self.subject.name}{sec} - {self.day_of_week}"

class Substitution(models.Model):
    timetable_slot = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='substitutions')
    original_faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='original_slots')
    substitute_faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='substitute_slots')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('timetable_slot', 'date')

    def __str__(self):
        return f"Sub: {self.substitute_faculty} for {self.original_faculty} on {self.date}"


class TimetableBreak(models.Model):
    """A named break slot (lunch, tea, etc.) shown in timetable views."""
    DAYS = Timetable.DAYS

    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='timetable_breaks')
    label = models.CharField(max_length=50, default='Break')  # e.g. "Lunch Break", "Tea Break"
    day_of_week = models.CharField(max_length=3, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    applies_to_all = models.BooleanField(default=True)  # college-wide vs dept-specific

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.label} ({self.day_of_week} {self.start_time}–{self.end_time})"

class Semester(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='semesters', null=True)
    number = models.IntegerField()
    year = models.IntegerField()

    def __str__(self):
        return f"Sem {self.number}"
class AttendanceSession(models.Model):

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('subject', 'date')

    def __str__(self):
        return f"{self.subject} - {self.date}"

class Attendance(models.Model):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('session', 'student')  # ✅ CORRECT PLACE

    def __str__(self):
        return f"{self.student} - {self.status}"
    
class Exam(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True, related_name='exams')
    name = models.CharField(max_length=100)
    semester = models.IntegerField()

    start_date = models.DateField()
    end_date = models.DateField()

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class Marks(models.Model):
    class Meta:
        unique_together = ('student', 'subject', 'exam')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)

    marks_obtained = models.FloatField()
    max_marks = models.FloatField()

    grade = models.CharField(max_length=5, null=True, blank=True)

    def __str__(self):
        return f"{self.student} - {self.subject}"
    
class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    semester = models.IntegerField()
    gpa = models.FloatField()

    total_marks = models.FloatField()
    percentage = models.FloatField()

    published_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - Sem {self.semester}"
class Assignment(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    description = models.TextField()

    deadline = models.DateTimeField()
    is_published = models.BooleanField(default=False)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    file = models.FileField(upload_to='assignments/')
    submitted_at = models.DateTimeField(auto_now_add=True)

    marks = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.student} - {self.assignment}"
    
class FeeStructure(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.IntegerField()
    total_fees = models.FloatField()

    class Meta:
        unique_together = ('college', 'department', 'semester')

    def __str__(self):
        return f"{self.department.code} Sem {self.semester}: {self.total_fees}"


class FeeBreakdown(models.Model):
    """Per-category fee amounts linked to a FeeStructure."""
    FEE_CATEGORY_CHOICES = (
        ('TUITION',   'Tuition Fee'),
        ('EXAM',      'Exam Fee'),
        ('LAB',       'Lab Fee'),
        ('LIBRARY',   'Library Fee'),
        ('SPORTS',    'Sports & Cultural Fee'),
        ('MISC',      'Miscellaneous'),
        # Per-occurrence fees (set college-wide, not per semester)
        ('SUPPLY_PER_SUBJECT', 'Supply Exam Fee (per subject)'),
        ('REVAL_PER_SUBJECT',  'Revaluation Fee (per subject)'),
        ('PHOTOCOPY',          'Photocopy of Answer Script'),
    )
    structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='breakdowns')
    category  = models.CharField(max_length=30, choices=FEE_CATEGORY_CHOICES)
    amount    = models.FloatField()

    class Meta:
        unique_together = ('structure', 'category')

    def __str__(self):
        return f"{self.structure} | {self.category}: {self.amount}"


class SupplyExamRegistration(models.Model):
    """Student registers for a supply/backlog exam for specific failed subjects."""
    STATUS_CHOICES = (
        ('PENDING',  'Payment Pending'),
        ('PAID',     'Paid & Registered'),
        ('REJECTED', 'Rejected'),
    )
    student    = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='supply_registrations')
    exam       = models.ForeignKey('Exam', on_delete=models.CASCADE, related_name='supply_registrations')
    subjects   = models.ManyToManyField('Subject', related_name='supply_registrations')
    total_fee  = models.FloatField(default=0)
    payment    = models.OneToOneField('Payment', on_delete=models.SET_NULL, null=True, blank=True, related_name='supply_registration')
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'exam')

    def __str__(self):
        return f"{self.student.roll_number} — Supply {self.exam.name} [{self.status}]"

class Fee(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    total_amount = models.FloatField()
    paid_amount = models.FloatField(default=0)

    # Track which semester and academic year this fee belongs to
    semester = models.IntegerField(null=True, blank=True)
    academic_year = models.CharField(max_length=20, blank=True, default='')  # e.g. "2024-25"

    STATUS = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partial'),
    )

    status = models.CharField(max_length=10, choices=STATUS, default='PENDING')

    def __str__(self):
        return f"{self.student} - Sem {self.semester or '?'} - {self.status}"

    @property
    def balance_due(self):
        return max(self.total_amount - self.paid_amount, 0)


# ── QUIZ SYSTEM ──────────────────────────────────────────────────────────────

class Quiz(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='quizzes')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.IntegerField(default=30)
    total_marks = models.FloatField(default=10)
    is_active = models.BooleanField(default=False)   # faculty activates when ready
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} — {self.subject.code}"


class QuizQuestion(models.Model):
    QUESTION_TYPES = (
        ('MCQ', 'Multiple Choice'),
        ('TF', 'True / False'),
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=5, choices=QUESTION_TYPES, default='MCQ')
    marks = models.FloatField(default=1)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.text[:60]}"


class QuizOption(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('quiz', 'student')

    def __str__(self):
        return f"{self.student.roll_number} — {self.quiz.title}"


class QuizAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuizOption, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('attempt', 'question')

    def __str__(self):
        return f"{self.attempt} — Q{self.question.order}"


# ── INTERNAL MARKS ───────────────────────────────────────────────────────────

class InternalMark(models.Model):
    """Stores IA1, IA2, assignment, and attendance components per student per subject."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='internal_marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='internal_marks')
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    ia1 = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(30)], help_text='Internal Assessment 1 (out of 30)')
    ia2 = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(30)], help_text='Internal Assessment 2 (out of 30)')
    assignment_marks = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(20)], help_text='Assignment component (out of 20)')
    attendance_marks = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)], help_text='Attendance component (out of 5)')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'subject')

    @property
    def total(self):
        parts = [self.ia1 or 0, self.ia2 or 0, self.assignment_marks or 0, self.attendance_marks or 0]
        return round(sum(parts), 2)

    def __str__(self):
        return f"{self.student.roll_number} — {self.subject.code} internal"


# ── LESSON PLAN ──────────────────────────────────────────────────────────────

class LessonPlan(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('REVISION', 'Needs Revision'),
    )
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='lesson_plans')
    faculty = models.ForeignKey('Faculty', on_delete=models.CASCADE, related_name='lesson_plans')
    unit_number = models.IntegerField(default=1)
    unit_title = models.CharField(max_length=200)
    topics = models.TextField(help_text='Comma-separated or detailed list of topics')
    planned_hours = models.IntegerField(default=1)
    planned_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    remarks = models.TextField(blank=True)
    file = models.FileField(upload_to='lesson_plans/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['unit_number', 'planned_date']

    def __str__(self):
        return f"{self.subject.code} — Unit {self.unit_number}: {self.unit_title}"


# ── LEAVE APPLICATION ─────────────────────────────────────────────────────────

class LeaveApplication(models.Model):
    LEAVE_TYPES = (
        ('CL', 'Casual Leave'),
        ('ML', 'Medical Leave'),
        ('EL', 'Earned Leave'),
        ('OD', 'On Duty'),
        ('OTHER', 'Other'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    faculty = models.ForeignKey('Faculty', on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.CharField(max_length=10, choices=LEAVE_TYPES)
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField()
    suggested_substitute = models.ForeignKey(
        'Faculty', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='substitute_requests'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='leave_reviews')
    hod_remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    @property
    def days(self):
        return (self.to_date - self.from_date).days + 1

    def __str__(self):
        return f"{self.faculty} — {self.get_leave_type_display()} ({self.from_date} to {self.to_date})"


# ── COLLEGE BRANDING ─────────────────────────────────────────────────────────

class CollegeBranding(models.Model):
    college = models.OneToOneField(College, on_delete=models.CASCADE, related_name='branding')
    tagline = models.CharField(max_length=200, blank=True, default='')
    primary_color = models.CharField(max_length=7, default='#0d7377', help_text='Hex color e.g. #0d7377')
    accent_color = models.CharField(max_length=7, default='#e6a817', help_text='Hex color e.g. #e6a817')
    sidebar_deep = models.CharField(max_length=7, default='#071e26', help_text='Sidebar background hex color')
    sidebar_dark = models.BooleanField(default=True, help_text='Dark sidebar (default) or light')
    show_college_name_in_sidebar = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Branding — {self.college.name}"


# ── EXAMINATION DEPARTMENT ────────────────────────────────────────────────────

class ExamStaff(models.Model):
    """
    Multiple exam department personnel per college, each with a specific sub-role.
    Replaces the single ExamController model.
    """
    EXAM_ROLE_CHOICES = (
        ('COE',        'Controller of Examinations'),
        ('DEPUTY_COE', 'Deputy Controller'),
        ('SECTION_OFFICER', 'Section Officer'),
        ('VALUATION_OFFICER', 'Valuation Officer'),
        ('DATA_ENTRY',  'Data Entry Operator'),
        ('COORDINATOR', 'Exam Coordinator'),
    )

    user       = models.OneToOneField(User, on_delete=models.CASCADE)
    college    = models.ForeignKey(College, on_delete=models.CASCADE, related_name='exam_staff')
    exam_role  = models.CharField(max_length=20, choices=EXAM_ROLE_CHOICES, default='COORDINATOR')
    employee_id = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    # Section officers are scoped to specific departments
    departments = models.ManyToManyField(Department, blank=True, related_name='exam_section_officers',
                                         help_text='Departments this staff member is responsible for (leave blank for all)')
    is_active  = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Exam Staff'
        verbose_name_plural = 'Exam Staff'

    def __str__(self):
        return f"{self.user.get_full_name()} [{self.get_exam_role_display()}] — {self.college.code}"

    @property
    def can_publish(self):
        return self.exam_role in ('COE', 'DEPUTY_COE')

    @property
    def can_verify(self):
        return self.exam_role in ('COE', 'DEPUTY_COE', 'SECTION_OFFICER')

    @property
    def can_manage_schedule(self):
        return self.exam_role in ('COE', 'DEPUTY_COE', 'COORDINATOR', 'SECTION_OFFICER')

    @property
    def can_manage_hall_tickets(self):
        return self.exam_role in ('COE', 'DEPUTY_COE', 'SECTION_OFFICER', 'COORDINATOR')


# Keep ExamController as a thin alias so migration 0017 data isn't broken
# New code should use ExamStaff everywhere
class ExamController(models.Model):
    """Legacy single-controller model — superseded by ExamStaff. Kept for migration compatibility."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='exam_controllers')
    employee_id = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    designation = models.CharField(max_length=100, default='Exam Controller')

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.college.code}"


class ExamType(models.Model):
    """CIE (internal) or SEE (semester end) or custom."""
    CATEGORY_CHOICES = (
        ('CIE', 'Continuous Internal Evaluation'),
        ('SEE', 'Semester End Examination'),
        ('PRACTICAL', 'Practical / Lab'),
        ('VIVA', 'Viva Voce'),
        ('OTHER', 'Other'),
    )
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='exam_types')
    name = models.CharField(max_length=100)           # e.g. "CIE-1", "SEE Nov 2025"
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='CIE')
    max_marks = models.FloatField(default=100)
    passing_marks = models.FloatField(default=40)
    weightage_percent = models.FloatField(default=100, help_text='% contribution to final result')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('college', 'name')

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class EvaluationScheme(models.Model):
    """
    Per-department (optionally per-semester) evaluation pattern.
    Defines how CIE and SEE components combine into a final result,
    how many CIEs are conducted, whether best-of rules apply, etc.

    Examples:
      - VTU: CIE 50 (best 2 of 3 tests × 20 each) + SEE 50
      - Anna Univ: CIE 20 + SEE 80
      - Autonomous: CIE 40 + SEE 60, with practical 25 internal + 25 external
    """
    GRADING_CHOICES = (
        ('ABSOLUTE', 'Absolute (fixed cutoffs)'),
        ('RELATIVE', 'Relative (based on class performance)'),
        ('CREDIT',   'Credit-based (CGPA)'),
    )
    college     = models.ForeignKey(College, on_delete=models.CASCADE, related_name='evaluation_schemes')
    department  = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='evaluation_schemes',
                                    help_text='Leave blank to apply to all departments in this college')
    name        = models.CharField(max_length=150, help_text='e.g. "VTU B.E. Scheme 2021"')
    description = models.TextField(blank=True)

    # CIE configuration
    cie_count           = models.IntegerField(default=2, help_text='How many CIE tests are conducted')
    cie_best_of         = models.IntegerField(default=2, help_text='Best N CIE scores are counted (0 = all)')
    cie_max_per_test    = models.FloatField(default=30, help_text='Max marks per CIE test')
    cie_total_max       = models.FloatField(default=50, help_text='Total CIE contribution to final marks')

    # SEE configuration
    see_max             = models.FloatField(default=100, help_text='SEE question paper max marks')
    see_scaled_to       = models.FloatField(default=50,  help_text='SEE scaled contribution to final marks')
    see_passing_min     = models.FloatField(default=35,  help_text='Minimum marks in SEE to pass')

    # Practical / Viva (optional)
    has_practical       = models.BooleanField(default=False)
    practical_internal_max = models.FloatField(default=25, null=True, blank=True)
    practical_external_max = models.FloatField(default=25, null=True, blank=True)

    # Overall passing
    overall_passing_min = models.FloatField(default=40, help_text='Minimum % to pass overall')
    grading_type        = models.CharField(max_length=10, choices=GRADING_CHOICES, default='ABSOLUTE')
    is_active           = models.BooleanField(default=True)

    class Meta:
        unique_together = ('college', 'department', 'name')

    def __str__(self):
        dept_str = self.department.code if self.department else 'All Depts'
        return f"{self.name} [{dept_str}]"

    @property
    def total_max_marks(self):
        base = self.cie_total_max + self.see_scaled_to
        if self.has_practical:
            base += (self.practical_internal_max or 0) + (self.practical_external_max or 0)
        return base


class ExamSchedule(models.Model):
    """Per-subject exam slot — date, time, room, invigilator."""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='schedule')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exam_schedules')
    exam_type = models.ForeignKey(ExamType, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=100, blank=True)
    invigilator = models.ForeignKey(
        Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='invigilated_exams'
    )
    max_marks = models.FloatField(default=100)
    passing_marks = models.FloatField(default=40)

    class Meta:
        unique_together = ('exam', 'subject')

    def __str__(self):
        return f"{self.exam.name} — {self.subject.code} on {self.date}"


class HallTicket(models.Model):
    """Eligibility record + hall ticket for a student for an exam."""
    STATUS_CHOICES = (
        ('ELIGIBLE', 'Eligible'),
        ('DETAINED', 'Detained — Low Attendance'),
        ('WITHHELD', 'Withheld — Fee Dues'),
        ('ISSUED', 'Hall Ticket Issued'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='hall_tickets')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='hall_tickets')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ELIGIBLE')
    attendance_pct = models.FloatField(default=0)
    has_fee_dues = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'exam')

    def __str__(self):
        return f"{self.student.roll_number} — {self.exam.name} [{self.status}]"


class ExamResult(models.Model):
    """
    Consolidated result per student per exam (across all subjects).
    Separate from the existing Result model which stores GPA per semester.
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('VERIFIED', 'Verified'),
        ('PUBLISHED', 'Published'),
        ('WITHHELD', 'Withheld'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_results')
    total_marks_obtained = models.FloatField(default=0)
    total_max_marks = models.FloatField(default=0)
    percentage = models.FloatField(default=0)
    grade = models.CharField(max_length=5, blank=True)
    is_pass = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    published_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_results')
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='published_results')

    class Meta:
        unique_together = ('student', 'exam')

    def __str__(self):
        return f"{self.student.roll_number} — {self.exam.name} [{self.status}]"


class RevaluationRequest(models.Model):
    """Student can request revaluation of a specific subject mark."""
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='revaluation_requests')
    marks = models.ForeignKey(Marks, on_delete=models.CASCADE, related_name='revaluation_requests')
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    revised_marks = models.FloatField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'marks')

    def __str__(self):
        return f"Reval: {self.student.roll_number} — {self.marks.subject.code}"


class ValuationAssignment(models.Model):
    """
    Assigns a faculty member (internal) or external examiner (name only)
    to evaluate answer scripts for a specific subject in an exam.
    Supports double valuation (first + second examiner).
    """
    VALUATION_TYPE = (
        ('FIRST',    'First Valuation'),
        ('SECOND',   'Second Valuation'),
        ('THIRD',    'Third / Arbitration'),
    )
    exam_schedule   = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE, related_name='valuations')
    valuation_type  = models.CharField(max_length=6, choices=VALUATION_TYPE, default='FIRST')
    # Internal faculty valuator
    faculty         = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='valuation_assignments')
    # External examiner (name + institution, no system account needed)
    external_name   = models.CharField(max_length=150, blank=True)
    external_institution = models.CharField(max_length=200, blank=True)
    assigned_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_at     = models.DateTimeField(auto_now_add=True)
    completed       = models.BooleanField(default=False)
    completed_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('exam_schedule', 'valuation_type')

    def __str__(self):
        who = self.faculty.user.get_full_name() if self.faculty else self.external_name or 'Unassigned'
        return f"{self.exam_schedule} — {self.get_valuation_type_display()} by {who}"


class ExamStaffLog(models.Model):
    """Audit trail for all exam department actions."""
    ACTION_CHOICES = (
        ('SCHEDULE_CREATED',   'Schedule Created'),
        ('HALL_TICKET_ISSUED', 'Hall Ticket Issued'),
        ('MARKS_VERIFIED',     'Marks Verified'),
        ('RESULT_PUBLISHED',   'Result Published'),
        ('REVAL_PROCESSED',    'Revaluation Processed'),
        ('SCHEME_CHANGED',     'Evaluation Scheme Changed'),
        ('STAFF_ADDED',        'Exam Staff Added'),
        ('OTHER',              'Other'),
    )
    staff       = models.ForeignKey(ExamStaff, on_delete=models.SET_NULL, null=True, blank=True)
    action      = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    exam        = models.ForeignKey(Exam, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} by {self.staff} at {self.created_at:%Y-%m-%d %H:%M}"


# ── ATTENDANCE RULE ENGINE ────────────────────────────────────────────────────

class AttendanceRule(models.Model):
    """
    Admin-configurable attendance eligibility rules per college/department/semester.
    Replaces all hardcoded 75% thresholds across the system.

    Precedence (most specific wins):
      department + semester > department only > college-wide (department=None, semester=None)
    """
    college    = models.ForeignKey(College, on_delete=models.CASCADE, related_name='attendance_rules')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='attendance_rules',
                                   help_text='Leave blank to apply to all departments')
    semester   = models.IntegerField(null=True, blank=True,
                                     help_text='Leave blank to apply to all semesters')

    # Core thresholds
    min_overall_pct   = models.FloatField(default=75.0,
                                          help_text='Minimum overall semester attendance % required')
    min_subject_pct   = models.FloatField(default=75.0,
                                          help_text='Minimum per-subject attendance % required')
    require_both      = models.BooleanField(default=True,
                                            help_text='Both overall AND subject-wise must be met')

    # Grace / condonation
    grace_pct         = models.FloatField(default=0.0,
                                          help_text='Condonation grace % (e.g. 5 means 70% is accepted)')
    min_sessions_for_check = models.IntegerField(default=5,
                                                  help_text='Minimum sessions conducted before eligibility check applies')

    # Mandatory subjects — stricter threshold
    mandatory_subject_pct = models.FloatField(default=75.0,
                                               help_text='Stricter threshold for mandatory/core subjects')

    # Special case handling
    allow_medical_exemption  = models.BooleanField(default=True)
    allow_sports_exemption   = models.BooleanField(default=True)
    allow_od_exemption       = models.BooleanField(default=True)
    max_exemption_days       = models.IntegerField(default=15,
                                                    help_text='Max days that can be exempted per semester')

    # Alert thresholds (for notifications, not eligibility)
    alert_below_pct   = models.FloatField(default=75.0,
                                          help_text='Send alert when attendance drops below this %')
    critical_below_pct = models.FloatField(default=65.0,
                                            help_text='Send critical alert below this %')

    is_active  = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('college', 'department', 'semester')
        ordering = ['college', 'department', 'semester']

    def __str__(self):
        dept = self.department.code if self.department else 'All'
        sem  = f'Sem {self.semester}' if self.semester else 'All Sems'
        return f"Rule [{dept} / {sem}] — {self.min_overall_pct}% overall, {self.min_subject_pct}% per subject"

    @property
    def effective_min_overall(self):
        """Threshold after applying grace condonation."""
        return max(0.0, self.min_overall_pct - self.grace_pct)

    @property
    def effective_min_subject(self):
        return max(0.0, self.min_subject_pct - self.grace_pct)


class AttendanceExemption(models.Model):
    """
    Student-specific attendance exemption (medical, sports, OD, etc.).
    Approved absences are excluded from the denominator when computing %.
    """
    EXEMPTION_TYPE = (
        ('MEDICAL', 'Medical Leave'),
        ('SPORTS',  'Sports / Cultural Event'),
        ('OD',      'On Duty'),
        ('OTHER',   'Other Authorized Absence'),
    )
    STATUS_CHOICES = (
        ('PENDING',  'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    student     = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exemptions')
    from_date   = models.DateField()
    to_date     = models.DateField()
    reason_type = models.CharField(max_length=10, choices=EXEMPTION_TYPE)
    reason      = models.TextField()
    document    = models.FileField(upload_to='exemptions/', null=True, blank=True)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_exemptions')
    review_note = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    @property
    def days(self):
        return (self.to_date - self.from_date).days + 1

    def __str__(self):
        return f"{self.student.roll_number} — {self.get_reason_type_display()} ({self.from_date} to {self.to_date})"


class AttendanceCorrection(models.Model):
    """
    Audit trail for any attendance record change.
    Faculty/HOD can correct attendance with a reason; all changes are logged.
    """
    attendance   = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='corrections')
    old_status   = models.CharField(max_length=10)
    new_status   = models.CharField(max_length=10)
    reason       = models.TextField()
    corrected_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_corrections')
    corrected_at = models.DateTimeField(auto_now_add=True)
    approved_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='approved_corrections')

    def __str__(self):
        return f"{self.attendance} changed {self.old_status}→{self.new_status} by {self.corrected_by}"


class EligibilityOverride(models.Model):
    """
    Manual override for a student's exam eligibility (HOD/Principal approval).
    Provides the audit trail required for condonation decisions.
    """
    STATUS_CHOICES = (
        ('PENDING',  'Pending'),
        ('APPROVED', 'Approved — Eligible'),
        ('REJECTED', 'Rejected — Remains Ineligible'),
    )
    student     = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='eligibility_overrides')
    exam        = models.ForeignKey('Exam', on_delete=models.CASCADE, related_name='eligibility_overrides')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='override_requests')
    reason      = models.TextField()
    attendance_pct_at_request = models.FloatField()
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_overrides')
    review_note = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'exam')

    def __str__(self):
        return f"Override: {self.student.roll_number} for {self.exam.name} [{self.status}]"
