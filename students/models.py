from datetime import timedelta
from uuid import uuid4

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# USER ROLE MODEL

class UserRole(models.Model):
    ROLE_CHOICES = (
        (1, 'College Admin'),
        (2, 'HOD'),
        (3, 'Faculty'),
        (4, 'Student'),
        (5, 'Lab Staff'),
        (6, 'Principal'),
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

    def __str__(self):
        return self.user.username

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
        ('PENDING', 'Pending'),
        ('REVIEWED', 'Reviewed'),
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

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
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
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.IntegerField()
    weekly_hours = models.IntegerField(default=3) # Based on Credits

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
    capacity = models.IntegerField()

    class Meta:
        unique_together = ('college', 'room_number')

    def __str__(self):
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
    def __str__(self):
        return f"{self.subject.name} - {self.day_of_week}"

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

class Fee(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    total_amount = models.FloatField()
    paid_amount = models.FloatField(default=0)

    STATUS = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partial'),
    )

    status = models.CharField(max_length=10, choices=STATUS, default='PENDING')

    def __str__(self):
        return f"{self.student} - {self.status}"


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

    ia1 = models.FloatField(null=True, blank=True, help_text='Internal Assessment 1 (out of 30)')
    ia2 = models.FloatField(null=True, blank=True, help_text='Internal Assessment 2 (out of 30)')
    assignment_marks = models.FloatField(null=True, blank=True, help_text='Assignment component (out of 20)')
    attendance_marks = models.FloatField(null=True, blank=True, help_text='Attendance component (out of 5)')

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
