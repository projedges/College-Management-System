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
    section_capacity = models.PositiveIntegerField(default=60)

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
    section = models.CharField(max_length=10, blank=True, default='')

    STATUS_CHOICES = (
        ('ACTIVE',     'Active'),
        ('DETAINED',   'Detained'),
        ('SUSPENDED',  'Suspended'),
        ('GRADUATED',  'Graduated'),
        ('DROPPED',    'Dropped'),
        ('TRANSFERRED','Transferred'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    # Point 12 — Lateral entry support
    ADMISSION_TYPE_CHOICES = [
        ('regular',       'Regular'),
        ('lateral_entry', 'Lateral Entry'),
        ('transfer',      'Transfer'),
    ]
    admission_type  = models.CharField(max_length=15, choices=ADMISSION_TYPE_CHOICES,
                                       default='regular')
    entry_semester  = models.IntegerField(default=1,
                                          help_text="Semester student joined (1 for regular, 3 for lateral entry)")

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
    alternate_phone = models.CharField(max_length=15, blank=True, default='', help_text='Alternate/secondary mobile number')

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

    # Email IDs
    college_email = models.EmailField(null=True, blank=True, help_text='Institutional email assigned by college (read-only for student)')
    personal_email = models.EmailField(null=True, blank=True, help_text='Student personal email (read-only for student)')

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
    attachment = models.FileField(upload_to='announcements/', null=True, blank=True,
                                  help_text='Optional PDF or image attachment')
    # Target audience
    TARGET_CHOICES = [
        ('all', 'Everyone (Faculty + Students)'),
        ('faculty', 'Faculty Only'),
        ('students', 'Students Only'),
    ]
    target = models.CharField(max_length=10, choices=TARGET_CHOICES, default='all')
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='dept_announcements',
                                   help_text='Limit to a specific department (leave blank for college-wide)')
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

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_read'], name='notif_user_read_idx'),
            models.Index(fields=['user', '-created_at'], name='notif_user_date_idx'),
        ]

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

    # Professional details (mirrors Faculty)
    designation = models.CharField(
        max_length=100, default='Head of Department',
        help_text='e.g. Professor & Head, Associate Professor & Head'
    )
    specialization = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Research/teaching specialization areas'
    )
    joined_date = models.DateField(null=True, blank=True)
    profile_photo = models.ImageField(
        upload_to='profiles/', null=True, blank=True
    )

    # Teaching role — many HODs also take classes like regular faculty
    can_take_classes = models.BooleanField(
        default=False,
        help_text='Enable if this HOD also teaches subjects like a faculty member'
    )

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

    @property
    def faculty_profile(self):
        """Returns linked Faculty record if HOD also teaches, else None."""
        try:
            return self.user.faculty
        except Exception:
            return None
    

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
    AVAILABILITY_TYPE = (
        ('available', 'Available'),
        ('preferred', 'Preferred'),
        ('blocked',   'Blocked / Unavailable'),
    )

    faculty          = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week      = models.CharField(max_length=3, choices=DAYS)
    start_time       = models.TimeField()
    end_time         = models.TimeField()
    is_available     = models.BooleanField(default=True)

    # Flexibility fields
    availability_type = models.CharField(max_length=10, choices=AVAILABILITY_TYPE, default='available',
                                         help_text="available = can teach, preferred = prefers this slot, blocked = unavailable")
    valid_from        = models.DateField(null=True, blank=True,
                                         help_text="Leave blank for permanent. Set for temporary slots (e.g. leave period).")
    valid_to          = models.DateField(null=True, blank=True,
                                         help_text="Leave blank for permanent.")
    priority_score    = models.IntegerField(default=5,
                                            help_text="1 (low) to 10 (high). Generator prefers higher scores when multiple slots are valid.")
    notes             = models.CharField(max_length=200, blank=True, default='',
                                         help_text="Optional note e.g. 'Can take labs only', 'Unavailable during exams'")

    class Meta:
        unique_together = ('faculty', 'day_of_week', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.faculty} - {self.day_of_week} {self.start_time}-{self.end_time} [{self.availability_type}]"


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

    # Schedule pattern flexibility
    SLOT_TYPE_CHOICES = [
        ('lecture',  'Lecture'),
        ('lab',      'Lab / Practical'),
        ('tutorial', 'Tutorial'),
        ('seminar',  'Seminar'),
    ]
    FREQUENCY_CHOICES = [
        ('daily',      'Daily'),
        ('alternate',  'Alternate Days'),
        ('weekly',     'Once a Week'),
        ('twice',      'Twice a Week'),
        ('thrice',     'Thrice a Week'),
    ]
    slot_type           = models.CharField(max_length=10, choices=SLOT_TYPE_CHOICES, default='lecture',
                                           help_text="Primary slot type for scheduling")
    slot_duration_mins  = models.IntegerField(default=60,
                                              help_text="Duration of each slot in minutes (e.g. 60 for lecture, 120 for lab)")
    frequency_per_week  = models.IntegerField(default=3,
                                              help_text="How many times per week this subject meets")
    scheduling_constraint = models.CharField(max_length=50, blank=True, default='',
                                             choices=[
                                                 ('',                  'None'),
                                                 ('no_consecutive',    'No Consecutive Slots'),
                                                 ('prefer_morning',    'Prefer Morning'),
                                                 ('prefer_afternoon',  'Prefer Afternoon'),
                                                 ('continuous_block',  'Continuous Block (e.g. 3-hr lab)'),
                                                 ('alternate_days',    'Alternate Days Only'),
                                             ],
                                             help_text="Optional scheduling constraint for the generator")

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


# ── SECTION MODEL ─────────────────────────────────────────────────────────────

class Section(models.Model):
    """
    Explicit section record for a department + semester.
    e.g. ISE Sem-5 Section A (60 students).
    Students are linked via Student.section (CharField) matching Section.label.
    """
    department  = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='sections')
    semester    = models.IntegerField()
    label       = models.CharField(max_length=10, help_text='e.g. A, B, C')
    capacity    = models.PositiveIntegerField(default=60)
    academic_year = models.CharField(max_length=10, blank=True, default='',
                                     help_text='e.g. 2023-24')

    # Point 14 — Section formation criteria
    CRITERIA_CHOICES = [
        ('auto',        'Auto — by roll number / count'),
        ('manual',      'Manual — admin assigned'),
        ('merit_based', 'Merit Based'),
        ('gender',      'Gender Based'),
        ('specialization', 'Specialization Based'),
    ]
    criteria = models.CharField(max_length=15, choices=CRITERIA_CHOICES, default='auto')

    class Meta:
        unique_together = ('department', 'semester', 'label')
        ordering = ['department', 'semester', 'label']

    def __str__(self):
        return f"{self.department.code} Sem{self.semester} Sec-{self.label}"

    @property
    def student_count(self):
        return Student.objects.filter(
            department=self.department,
            current_semester=self.semester,
            section=self.label
        ).count()

    @property
    def is_full(self):
        return self.student_count >= self.capacity

    @classmethod
    def auto_create_sections(cls, department, semester, academic_year=''):
        """
        Point 14 — Auto-create sections based on student count vs capacity.
        Called after bulk admission or promotion.
        """
        students = Student.objects.filter(
            department=department,
            current_semester=semester,
            is_deleted=False,
            status='ACTIVE',
        ).order_by('roll_number')

        capacity = department.section_capacity or 60
        labels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        created = []
        for i, chunk_start in enumerate(range(0, students.count(), capacity)):
            label = labels[i] if i < len(labels) else f"S{i+1}"
            sec, _ = cls.objects.get_or_create(
                department=department, semester=semester, label=label,
                defaults={'capacity': capacity, 'academic_year': academic_year}
            )
            chunk = students[chunk_start:chunk_start + capacity]
            chunk.update(section=label)
            created.append(sec)
        return created


# ── SUBJECT–SECTION–FACULTY MAP ───────────────────────────────────────────────

class SectionSubjectFacultyMap(models.Model):
    """
    The core mapping table: Subject + Section + Faculty.
    One record = "Faculty X teaches Subject Y to Section Z".
    This drives timetable generation and attendance session creation.
    """
    section     = models.ForeignKey(Section, on_delete=models.CASCADE,
                                    related_name='subject_faculty_maps')
    subject     = models.ForeignKey(Subject, on_delete=models.CASCADE,
                                    related_name='section_faculty_maps')
    faculty     = models.ForeignKey(Faculty, on_delete=models.CASCADE,
                                    related_name='section_subject_maps')
    classroom   = models.ForeignKey('Classroom', on_delete=models.SET_NULL,
                                    null=True, blank=True,
                                    help_text='Default classroom for this section')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('section', 'subject')  # one faculty per subject per section
        ordering = ['section__label', 'subject__name']

    def __str__(self):
        return (f"{self.subject.code} | Sec {self.section.label} "
                f"→ {self.faculty.user.get_full_name()}")


# ── PROMOTION SYSTEM (Point 11) ───────────────────────────────────────────────

class PromotionRule(models.Model):
    """
    Defines the rules for promoting students from one semester to the next.
    One rule per college (can be overridden per department).
    """
    college                = models.ForeignKey(College, on_delete=models.CASCADE, related_name='promotion_rules')
    department             = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                               null=True, blank=True, related_name='promotion_rules',
                                               help_text="Leave blank for college-wide rule")
    from_semester          = models.IntegerField(help_text="Semester being completed")
    min_credits_required   = models.IntegerField(default=0,
                                                  help_text="Minimum credits student must have passed to be promoted")
    min_attendance_pct     = models.FloatField(default=75.0,
                                               help_text="Minimum overall attendance % required for promotion")
    allow_backlogs         = models.BooleanField(default=True,
                                                  help_text="If True, students with backlogs can still be promoted to next semester")
    max_backlogs_allowed   = models.IntegerField(default=2,
                                                  help_text="Max number of backlog subjects allowed for promotion (if allow_backlogs=True)")
    is_active              = models.BooleanField(default=True)

    class Meta:
        unique_together = ('college', 'department', 'from_semester')

    def __str__(self):
        dept = self.department.code if self.department else 'All'
        return f"{self.college.code} | {dept} | Sem {self.from_semester} → {self.from_semester + 1}"


class StudentSemesterHistory(models.Model):
    """
    Tracks a student's status at the end of each semester.
    This is the source of truth for who is actually in which semester.
    """
    STATUS_CHOICES = [
        ('promoted',  'Promoted'),
        ('detained',  'Detained — Must Repeat Semester'),
        ('backlog',   'Promoted with Backlog'),
        ('dropped',   'Dropped Out'),
        ('graduated', 'Graduated'),
    ]

    student          = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='semester_history')
    semester         = models.IntegerField()
    academic_year    = models.CharField(max_length=10, blank=True, default='', help_text="e.g. 2023-24")
    status           = models.CharField(max_length=10, choices=STATUS_CHOICES)
    credits_earned   = models.IntegerField(default=0)
    backlogs         = models.ManyToManyField(Subject, blank=True, related_name='backlog_students',
                                              help_text="Subjects the student failed / has backlog in")
    promoted_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='promotions_done')
    promoted_at      = models.DateTimeField(null=True, blank=True)
    notes            = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ('student', 'semester', 'academic_year')
        ordering = ['student', 'semester']

    def __str__(self):
        return f"{self.student.roll_number} | Sem {self.semester} | {self.get_status_display()}"


# ── LATERAL ENTRY (Point 12) ──────────────────────────────────────────────────

class LateralEntryProfile(models.Model):
    """
    Extra profile for lateral entry students who join directly into Sem 3+.
    Tracks their entry semester and any bridge courses they need.
    """
    student         = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='lateral_entry_profile')
    entry_semester  = models.IntegerField(default=3, help_text="Semester the student joined (usually 3 for LE)")
    previous_qualification = models.CharField(max_length=200, blank=True, default='',
                                               help_text="e.g. Diploma in Computer Science")
    previous_institution   = models.CharField(max_length=200, blank=True, default='')
    bridge_courses  = models.ManyToManyField(Subject, blank=True, related_name='bridge_course_students',
                                              help_text="Additional subjects LE student must complete")
    notes           = models.TextField(blank=True, default='')

    def __str__(self):
        return f"LE: {self.student.roll_number} (joined Sem {self.entry_semester})"


# ── ADMISSION CYCLE (Point 13) ────────────────────────────────────────────────

class AdmissionCycle(models.Model):
    """
    Represents one admission cycle (year + round).
    e.g. "2024-25 Round 1", "2024-25 Lateral Entry Round"
    """
    college       = models.ForeignKey(College, on_delete=models.CASCADE, related_name='admission_cycles')
    academic_year = models.CharField(max_length=10, help_text="e.g. 2024-25")
    round_number  = models.IntegerField(default=1, help_text="1 = first round, 2 = second round, etc.")
    round_name    = models.CharField(max_length=60, blank=True, default='',
                                     help_text="e.g. 'Regular', 'Lateral Entry', 'NRI', 'Management Quota'")
    start_date    = models.DateField(null=True, blank=True)
    end_date      = models.DateField(null=True, blank=True)
    is_active     = models.BooleanField(default=False)

    class Meta:
        unique_together = ('college', 'academic_year', 'round_number')
        ordering = ['academic_year', 'round_number']

    def __str__(self):
        return f"{self.college.code} | {self.academic_year} Round {self.round_number}"


class Admission(models.Model):
    """
    Tracks a student's admission record — which cycle, when, and current status.
    Supports late admissions and multiple rounds.
    """
    ADMISSION_TYPE = [
        ('regular',       'Regular'),
        ('lateral_entry', 'Lateral Entry'),
        ('nri',           'NRI'),
        ('management',    'Management Quota'),
        ('transfer',      'Transfer'),
    ]
    STATUS_CHOICES = [
        ('applied',    'Applied'),
        ('confirmed',  'Confirmed'),
        ('enrolled',   'Enrolled'),
        ('cancelled',  'Cancelled'),
        ('withdrawn',  'Withdrawn'),
    ]

    student        = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='admission')
    cycle          = models.ForeignKey(AdmissionCycle, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='admissions')
    admission_type = models.CharField(max_length=15, choices=ADMISSION_TYPE, default='regular')
    admission_date = models.DateField(null=True, blank=True)
    status         = models.CharField(max_length=10, choices=STATUS_CHOICES, default='enrolled')
    category       = models.CharField(max_length=20, blank=True, default='',
                                      help_text="e.g. GEN, OBC, SC, ST, EWS")
    notes          = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.student.roll_number} | {self.get_admission_type_display()} | {self.get_status_display()}"


# ── BACKLOG REGISTRATION (Point 15) ───────────────────────────────────────────

class BacklogRegistration(models.Model):
    """
    Tracks a student re-registering for a subject they failed.
    Enables cross-semester scheduling — the student attends a class
    in a different semester/section for the backlog subject.
    """
    STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('attending',  'Attending'),
        ('cleared',    'Cleared / Passed'),
        ('failed',     'Failed Again'),
        ('withdrawn',  'Withdrawn'),
    ]

    student             = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='backlog_registrations')
    subject             = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='backlog_registrations')
    original_semester   = models.IntegerField(help_text="Semester the student originally failed this subject")
    semester_registered = models.IntegerField(help_text="Semester in which the student is re-attending this subject")
    academic_year       = models.CharField(max_length=10, blank=True, default='')
    timetable_slot      = models.ForeignKey('Timetable', on_delete=models.SET_NULL,
                                             null=True, blank=True, related_name='backlog_students',
                                             help_text="The specific timetable slot the student is attending for this backlog")
    status              = models.CharField(max_length=10, choices=STATUS_CHOICES, default='registered')
    registered_at       = models.DateTimeField(auto_now_add=True)
    notes               = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ('student', 'subject', 'semester_registered', 'academic_year')
        ordering = ['student', 'subject']

    def __str__(self):
        return f"{self.student.roll_number} | Backlog: {self.subject.code} | Sem {self.semester_registered}"


# ── REGULATION & CURRICULUM ───────────────────────────────────────────────────

class Regulation(models.Model):
    """
    Academic regulation / scheme defined by the college or university.
    e.g. "VTU 2021 Scheme", "Anna Univ R2019", "Autonomous 2022"
    All curriculum entries and evaluation schemes are tied to a regulation.
    """
    college     = models.ForeignKey(College, on_delete=models.CASCADE, related_name='regulations')
    name        = models.CharField(max_length=100, help_text='e.g. "VTU 2021 Scheme"')
    code        = models.CharField(max_length=30, help_text='Short code e.g. "VTU21", "R2019"')
    description = models.TextField(blank=True)
    effective_from_year = models.IntegerField(
        help_text='Admission year from which this regulation applies (e.g. 2021)'
    )
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('college', 'code')

    def __str__(self):
        return f"{self.name} ({self.college.code})"


class CurriculumEntry(models.Model):
    """
    Maps a Subject into a Regulation's curriculum for a specific
    department and semester. This is the official syllabus record.

    Fixed subjects (PC, BS, MC, HS, ES) are auto-enrolled to all students.
    Elective subjects (PE, OE) go through ElectivePool → ElectiveSelection.
    """
    regulation  = models.ForeignKey(Regulation, on_delete=models.CASCADE, related_name='curriculum_entries')
    department  = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='curriculum_entries')
    subject     = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='curriculum_entries')
    semester    = models.IntegerField()

    ELECTIVE_TYPES = [
        ('FIXED',    'Fixed / Compulsory'),
        ('PE',       'Program Elective'),
        ('OE',       'Open Elective'),
    ]
    elective_type = models.CharField(max_length=10, choices=ELECTIVE_TYPES, default='FIXED')

    # Prerequisite subjects (informational + enforced at elective selection)
    prerequisites = models.ManyToManyField(
        Subject, blank=True, related_name='required_for',
        help_text='Subjects that must be passed before taking this subject'
    )

    class Meta:
        unique_together = ('regulation', 'department', 'subject', 'semester')

    def __str__(self):
        return f"{self.regulation.code} | {self.department.code} Sem{self.semester} | {self.subject.code}"

    @property
    def is_elective(self):
        return self.elective_type in ('PE', 'OE')


# ── ELECTIVE SELECTION ────────────────────────────────────────────────────────

class ElectivePool(models.Model):
    """
    Admin opens an elective slot for a batch to choose from.
    e.g. "Sem 5 PE-1 — choose one from: AI, ML, IoT" with quota per subject.
    """
    STATUS_CHOICES = [
        ('DRAFT',  'Draft'),
        ('OPEN',   'Open for Selection'),
        ('CLOSED', 'Closed'),
    ]
    regulation   = models.ForeignKey(Regulation, on_delete=models.CASCADE, related_name='elective_pools')
    department   = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='elective_pools')
    semester     = models.IntegerField()
    slot_name    = models.CharField(max_length=60, help_text='e.g. "PE-1", "Open Elective"')
    elective_type = models.CharField(max_length=10, choices=CurriculumEntry.ELECTIVE_TYPES[1:], default='PE')
    subjects     = models.ManyToManyField(Subject, related_name='elective_pools',
                                          help_text='Subjects students can choose from in this slot')
    quota_per_subject = models.PositiveIntegerField(default=60,
                                                     help_text='Max students per elective subject (for section/faculty planning)')
    min_students_per_subject = models.PositiveIntegerField(default=10,
                                                            help_text='Min students needed to run this elective (below this, subject may be cancelled)')
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    deadline     = models.DateTimeField(null=True, blank=True,
                                        help_text='Last date/time for students to submit their choice')
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('regulation', 'department', 'semester', 'slot_name')

    def __str__(self):
        return f"{self.department.code} Sem{self.semester} {self.slot_name} [{self.get_status_display()}]"

    def seats_remaining(self, subject):
        taken = ElectiveSelection.objects.filter(pool=self, subject=subject, status='CONFIRMED').count()
        return max(0, self.quota_per_subject - taken)


class ElectiveSelection(models.Model):
    """
    A student's elective choice for a specific pool slot.
    One record per student per pool.
    """
    STATUS_CHOICES = [
        ('PENDING',   'Pending Admin Confirmation'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED',  'Rejected — Quota Full'),
        ('CHANGED',   'Changed by Admin'),
    ]
    student  = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='elective_selections')
    pool     = models.ForeignKey(ElectivePool, on_delete=models.CASCADE, related_name='selections')
    subject  = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='elective_selections')
    status   = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    selected_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    note     = models.CharField(max_length=200, blank=True,
                                help_text='Admin note if changed/rejected')

    class Meta:
        unique_together = ('student', 'pool')  # one choice per pool per student

    def __str__(self):
        return f"{self.student.roll_number} → {self.subject.code} [{self.get_status_display()}]"


# ── ELECTIVE GROUP (Point 6 & 7) ──────────────────────────────────────────────

class ElectiveGroup(models.Model):
    """
    A group of students who chose the same elective subject from a pool.
    Acts as a virtual section for timetable scheduling and conflict detection.
    e.g. "Sem5 PE-1 AI Group", "Sem5 PE-1 ML Group"
    """
    pool        = models.ForeignKey(ElectivePool, on_delete=models.CASCADE, related_name='elective_groups')
    subject     = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='elective_groups')
    group_label = models.CharField(max_length=20, default='',
                                   help_text="Auto-assigned label e.g. EG-A, EG-B")
    students    = models.ManyToManyField(Student, blank=True, related_name='elective_groups',
                                         help_text="Students in this elective group (populated from confirmed ElectiveSelections)")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('pool', 'subject')

    def __str__(self):
        return f"{self.pool} | {self.subject.code} [{self.group_label}]"

    def sync_students(self):
        """Sync students from confirmed ElectiveSelections into this group."""
        confirmed = ElectiveSelection.objects.filter(
            pool=self.pool, subject=self.subject, status='CONFIRMED'
        ).values_list('student_id', flat=True)
        self.students.set(confirmed)


class StudentGroupConflict(models.Model):
    """
    Tracks which (student_group, day, time_slot) combinations are already occupied.
    Used by the timetable generator to prevent a student from having two classes at the same time.
    group_type: 'section' (regular dept section) or 'elective' (ElectiveGroup)
    """
    GROUP_TYPE = [
        ('section',  'Department Section'),
        ('elective', 'Elective Group'),
    ]
    college        = models.ForeignKey(College, on_delete=models.CASCADE, related_name='student_group_conflicts')
    group_type     = models.CharField(max_length=10, choices=GROUP_TYPE)
    group_id       = models.IntegerField(help_text="PK of Section or ElectiveGroup")
    day_of_week    = models.CharField(max_length=3, choices=Timetable.DAYS if 'Timetable' in dir() else [])
    start_time     = models.TimeField()
    end_time       = models.TimeField()
    timetable_slot = models.ForeignKey('Timetable', on_delete=models.CASCADE,
                                        related_name='student_group_conflicts', null=True, blank=True)

    class Meta:
        unique_together = ('group_type', 'group_id', 'day_of_week', 'start_time')

    def __str__(self):
        return f"{self.group_type}:{self.group_id} — {self.day_of_week} {self.start_time}"



class HODApproval(models.Model):
    APPROVAL_TYPE = (
        ('LEAVE',    'Leave Request'),
        ('EVENT',    'Event Approval'),
        ('COURSE',   'Course Approval'),
        ('CE_MARKS', 'CE Marks Submission'),
    )

    STATUS_CHOICES = (
        ('PENDING',  'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    department   = models.ForeignKey(Department, on_delete=models.CASCADE)
    subject      = models.ForeignKey('Subject', on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='hod_approvals')

    approval_type = models.CharField(max_length=20, choices=APPROVAL_TYPE)
    description   = models.TextField()

    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='hod_reviews')

    created_at  = models.DateTimeField(auto_now_add=True)
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
    


class FacultyFeedbackCycle(models.Model):
    """College admin creates feedback windows for students to review faculty."""
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='faculty_feedback_cycles')
    title = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='faculty_feedback_cycles')
    semester = models.IntegerField(null=True, blank=True)
    subject = models.ForeignKey('Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_cycles')
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_cycles')
    questions = models.TextField(default="Clarity of teaching\nSubject knowledge\nPunctuality and preparation\nStudent engagement\nDoubt clarification")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_feedback_cycles')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date', '-created_at']

    def __str__(self):
        return self.title

    @property
    def question_list(self):
        return [q.strip() for q in self.questions.splitlines() if q.strip()]


class FacultyFeedbackResponse(models.Model):
    cycle = models.ForeignKey(FacultyFeedbackCycle, on_delete=models.CASCADE, related_name='responses')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='faculty_feedback_responses')
    ratings = models.JSONField(default=dict)
    comments = models.TextField(blank=True, default='')
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cycle', 'student')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.roll_number} - {self.cycle.title}"

    @property
    def average_rating(self):
        values = []
        for value in self.ratings.values():
            try:
                values.append(float(value))
            except (TypeError, ValueError):
                continue
        return round(sum(values) / len(values), 2) if values else 0


class CourseSubject(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    semester = models.IntegerField()

    def __str__(self):
        return f"{self.course.name} - {self.subject.name}"

class Classroom(models.Model):
    ROOM_TYPE_CHOICES = [
        ('lecture',  'Lecture Hall'),
        ('lab',      'Lab'),
        ('seminar',  'Seminar Hall'),
        ('tutorial', 'Tutorial Room'),
        ('other',    'Other'),
    ]

    college     = models.ForeignKey(College, on_delete=models.CASCADE, related_name='classrooms', null=True)
    room_number = models.CharField(max_length=20)
    building    = models.CharField(max_length=100, blank=True, default='')
    capacity    = models.IntegerField()
    room_type   = models.CharField(max_length=10, choices=ROOM_TYPE_CHOICES, default='lecture',
                                   help_text="Type of room — used by generator to match subject slot type")
    features    = models.CharField(max_length=200, blank=True, default='',
                                   help_text="Comma-separated features e.g. projector,computers,ac,smartboard")

    class Meta:
        unique_together = ('college', 'room_number')

    def __str__(self):
        if self.building:
            return f"{self.building} - {self.room_number}"
        return f"{self.room_number} ({self.college.code if self.college else 'Global'})"

    def features_list(self):
        return [f.strip() for f in self.features.split(',') if f.strip()]

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

    # Point 10 — Version link
    version = models.ForeignKey('TimetableVersion', on_delete=models.CASCADE,
                                null=True, blank=True, related_name='timetable_entries',
                                help_text="Link to timetable version (regular/exam/backup/draft)")

    # Section support — e.g. "A", "B", "C" for same subject taught by different faculty
    section = models.CharField(max_length=10, blank=True, default='',
                               help_text="Section label e.g. A, B, C. Leave blank if no sections.")

    # Elective group link (Point 6) — set when this slot belongs to an elective group
    elective_group = models.ForeignKey('ElectiveGroup', on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='timetable_slots',
                                        help_text="Set for elective group slots to enable student-level conflict detection")

    # Point 8 — Manual override lock
    is_locked = models.BooleanField(default=False,
                                    help_text="Locked slots are skipped by auto-generator. Admin must unlock to allow changes.")

    # Generation strategy that created this entry
    GENERATION_MODE_CHOICES = [
        ('manual',           'Manual / CSV Upload'),
        ('strict',           'Auto — Strict'),
        ('balanced',         'Auto — Balanced'),
        ('faculty_priority', 'Auto — Faculty Priority'),
    ]
    generation_mode = models.CharField(max_length=20, choices=GENERATION_MODE_CHOICES,
                                       default='manual', blank=True)

    def __str__(self):
        sec = f" [{self.section}]" if self.section else ""
        return f"{self.subject.name}{sec} - {self.day_of_week}"

class Substitution(models.Model):
    STATUS_CHOICES = (
        ('PENDING',  'Pending Acceptance'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    )
    timetable_slot     = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='substitutions')
    original_faculty   = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='original_slots')
    substitute_faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='substitute_slots')
    date               = models.DateField()
    status             = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    rejection_reason   = models.CharField(max_length=200, blank=True, default='')
    responded_at       = models.DateTimeField(null=True, blank=True)
    # Topic the substitute must enter before marking attendance
    topic_covered      = models.CharField(max_length=300, blank=True, default='',
                                          help_text='Topic covered — required before marking attendance')
    # Optional note from the requesting faculty explaining why they need a substitute
    note               = models.CharField(max_length=500, blank=True, default='',
                                          help_text='Optional reason/note shown to the substitute faculty')
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('timetable_slot', 'date')
        indexes = [
            models.Index(fields=['original_faculty', 'date', 'status'], name='sub_orig_date_status_idx'),
            models.Index(fields=['substitute_faculty', 'date', 'status'], name='sub_sub_date_status_idx'),
        ]

    def __str__(self):
        return f"Sub: {self.substitute_faculty} for {self.original_faculty} on {self.date} [{self.status}]"


class TimetableBreak(models.Model):
    """A named break slot (lunch, tea, event, exam) shown in timetable views."""
    DAYS = Timetable.DAYS

    BREAK_TYPE_CHOICES = [
        ('regular', 'Regular Break'),
        ('exam',    'Exam / Test'),
        ('event',   'College Event / Fest'),
        ('holiday', 'Holiday'),
        ('other',   'Other'),
    ]
    APPLIES_TO_CHOICES = [
        ('college',    'Entire College'),
        ('department', 'Department Only'),
        ('section',    'Specific Section'),
    ]

    college        = models.ForeignKey(College, on_delete=models.CASCADE, related_name='timetable_breaks')
    department     = models.ForeignKey('Department', on_delete=models.CASCADE, null=True, blank=True,
                                       related_name='timetable_breaks',
                                       help_text="Set only when applies_to = department or section")
    label          = models.CharField(max_length=50, default='Break')
    day_of_week    = models.CharField(max_length=3, choices=DAYS)
    start_time     = models.TimeField()
    end_time       = models.TimeField()

    # Legacy field kept for backward compat
    applies_to_all = models.BooleanField(default=True)

    # New flexibility fields
    break_type     = models.CharField(max_length=10, choices=BREAK_TYPE_CHOICES, default='regular')
    applies_to     = models.CharField(max_length=10, choices=APPLIES_TO_CHOICES, default='college',
                                      help_text="Scope of this break")
    section        = models.CharField(max_length=10, blank=True, default='',
                                      help_text="Section label if applies_to = section")
    valid_from     = models.DateField(null=True, blank=True,
                                      help_text="Start date for temporary breaks (events, exams). Leave blank for recurring.")
    valid_to       = models.DateField(null=True, blank=True,
                                      help_text="End date for temporary breaks.")

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.label} ({self.day_of_week} {self.start_time}–{self.end_time})"


# ── SCHEDULING CONSTRAINT (Point 9) ───────────────────────────────────────────

class SchedulingConstraint(models.Model):
    """
    Defines a constraint for the timetable generator with priority and weight.
    Hard constraints MUST be satisfied. Soft constraints are preferences.
    """
    CONSTRAINT_TYPE = [
        ('faculty_clash',       'Faculty Clash'),
        ('room_clash',          'Room Clash'),
        ('student_group_clash', 'Student Group Clash'),
        ('faculty_availability','Faculty Availability'),
        ('time_distribution',   'Time Distribution'),
        ('room_type_match',     'Room Type Match'),
        ('slot_duration_match', 'Slot Duration Match'),
    ]
    PRIORITY = [
        ('hard', 'Hard — Must Satisfy'),
        ('soft', 'Soft — Preference'),
    ]

    college         = models.ForeignKey(College, on_delete=models.CASCADE, related_name='scheduling_constraints')
    constraint_type = models.CharField(max_length=30, choices=CONSTRAINT_TYPE)
    priority        = models.CharField(max_length=10, choices=PRIORITY, default='hard')
    weight          = models.IntegerField(default=10,
                                          help_text="1 (low) to 100 (high). Used for soft constraint optimization.")
    is_active       = models.BooleanField(default=True)
    description     = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        unique_together = ('college', 'constraint_type')

    def __str__(self):
        return f"{self.college.code} | {self.get_constraint_type_display()} [{self.priority.upper()}]"


# ── TIMETABLE VERSION (Point 10) ──────────────────────────────────────────────

class TimetableVersion(models.Model):
    """
    Allows multiple timetable versions (regular, exam, backup, draft).
    Only one version per type can be active at a time per college.
    """
    VERSION_TYPE = [
        ('regular', 'Regular Timetable'),
        ('exam',    'Exam Timetable'),
        ('backup',  'Backup Timetable'),
        ('draft',   'Draft / Proposed'),
    ]

    college      = models.ForeignKey(College, on_delete=models.CASCADE, related_name='timetable_versions')
    version_type = models.CharField(max_length=10, choices=VERSION_TYPE, default='regular')
    version_name = models.CharField(max_length=100,
                                    help_text="e.g. 'Regular 2024-25 Odd', 'Exam Dec 2024', 'Backup Rainy Day'")
    is_active    = models.BooleanField(default=False,
                                       help_text="Only one version per type can be active. Activating this deactivates others of same type.")
    valid_from   = models.DateField(null=True, blank=True)
    valid_to     = models.DateField(null=True, blank=True)
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    notes        = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ('college', 'version_name')
        ordering = ['-created_at']

    def __str__(self):
        active = " [ACTIVE]" if self.is_active else ""
        return f"{self.college.code} | {self.version_name}{active}"

    def activate(self):
        """Activate this version and deactivate all others of the same type."""
        TimetableVersion.objects.filter(
            college=self.college, version_type=self.version_type
        ).update(is_active=False)
        self.is_active = True
        self.save(update_fields=['is_active'])


class Semester(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='semesters', null=True)
    number = models.IntegerField()
    year = models.IntegerField()

    def __str__(self):
        return f"Sem {self.number}"
class AttendanceSession(models.Model):

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    section = models.CharField(max_length=10, blank=True, default='',
                               help_text='Section label e.g. A, B, C')
    timetable_slot = models.ForeignKey(
        'Timetable', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='attendance_sessions',
        help_text='Timetable slot this session was generated from'
    )
    date = models.DateField()
    # Topic covered in this session — required before saving attendance
    topic_covered = models.CharField(max_length=300, blank=True, default='',
                                     help_text='Topic taught in this session')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('subject', 'date', 'section')  # one session per subject+section per day
        indexes = [
            models.Index(fields=['faculty', 'date'], name='attsess_faculty_date_idx'),
            models.Index(fields=['subject', 'date'], name='attsess_subject_date_idx'),
        ]

    def __str__(self):
        sec = f" [{self.section}]" if self.section else ""
        return f"{self.subject}{sec} - {self.date}"

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
    exam    = models.ForeignKey(Exam, on_delete=models.CASCADE)

    marks_obtained = models.FloatField()
    max_marks      = models.FloatField()
    grade          = models.CharField(max_length=5, null=True, blank=True)
    grade_point    = models.FloatField(default=0.0,
                                       help_text='Grade point on 10-point scale (O=10, A+=9, A=8, B+=7, B=6, C=5, F=0)')

    def __str__(self):
        return f"{self.student} - {self.subject}"
    
class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    semester    = models.IntegerField()
    gpa         = models.FloatField()   # kept for backward compat (= sgpa)
    sgpa        = models.FloatField(default=0.0, help_text='Semester GPA (credit-weighted)')
    total_marks = models.FloatField()
    percentage  = models.FloatField()
    total_credits = models.IntegerField(default=0, help_text='Total credits for this semester')

    published_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - Sem {self.semester}"
class Assignment(models.Model):
    SUBMISSION_TYPE = (
        ('ONLINE',  'Online — students upload file'),
        ('OFFLINE', 'Offline — physical submission'),
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateTimeField()
    is_published = models.BooleanField(default=False)
    submission_type = models.CharField(max_length=10, choices=SUBMISSION_TYPE, default='ONLINE')
    max_marks = models.FloatField(default=10)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    file = models.FileField(upload_to='assignments/', null=True, blank=True)
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
    is_active = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    # Question pool settings
    questions_per_student = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='How many questions each student gets (random from pool). Leave blank = all questions.'
    )
    access_password = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Optional password students must enter before starting the quiz.'
    )
    template_file = models.FileField(
        upload_to='quiz_templates/', null=True, blank=True,
        help_text='Upload a CSV/Excel with questions to bulk-import into the pool.'
    )
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

    class Meta:
        indexes = [
            models.Index(fields=['faculty', 'status'], name='leave_faculty_status_idx'),
            models.Index(fields=['faculty', 'from_date'], name='leave_faculty_date_idx'),
        ]

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
    def designation(self):
        return self.get_exam_role_display()

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
    # Seating arrangement
    room_number = models.CharField(max_length=50, blank=True)
    seat_number = models.CharField(max_length=20, blank=True)
    row_number = models.CharField(max_length=10, blank=True)

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


# ── AUDIT LOG ─────────────────────────────────────────────────────────────────

class AuditLog(models.Model):
    """
    Unified audit trail for every critical action in the system.
    Covers: marks changes, attendance edits, fee updates, override approvals,
    elective changes, timetable edits — anything that needs a paper trail.
    """
    ACTION_TYPES = (
        # Marks
        ('MARKS_ENTERED',     'Marks Entered'),
        ('MARKS_UPDATED',     'Marks Updated'),
        ('MARKS_REVAL',       'Revaluation Applied'),
        # Attendance
        ('ATT_MARKED',        'Attendance Marked'),
        ('ATT_CORRECTED',     'Attendance Corrected'),
        ('ATT_EXEMPTION',     'Exemption Granted'),
        ('ATT_OVERRIDE',      'Eligibility Override'),
        # Fee
        ('FEE_PAYMENT',       'Fee Payment'),
        ('FEE_WAIVER',        'Fee Waiver Applied'),
        ('FEE_PENALTY',       'Late Fee Penalty Added'),
        ('FEE_INSTALLMENT',   'Installment Updated'),
        # Elective
        ('ELECTIVE_SELECTED', 'Elective Selected'),
        ('ELECTIVE_CHANGED',  'Elective Changed by Admin'),
        # Timetable
        ('TT_GENERATED',      'Timetable Generated'),
        ('TT_SUBSTITUTION',   'Substitution Assigned'),
        # User / Admin
        ('USER_CREATED',      'User Created'),
        ('USER_PROMOTED',     'Student Promoted'),
        ('RESULT_PUBLISHED',  'Result Published'),
        ('OTHER',             'Other'),
    )

    action_type  = models.CharField(max_length=30, choices=ACTION_TYPES)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     related_name='audit_actions')
    # Target — at least one of these will be set
    student      = models.ForeignKey('Student', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='audit_logs')
    faculty      = models.ForeignKey('Faculty', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='audit_logs')
    college      = models.ForeignKey('College', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='audit_logs')

    description  = models.TextField(help_text='Human-readable summary of what changed')
    old_value    = models.TextField(blank=True, help_text='Previous value (JSON or plain text)')
    new_value    = models.TextField(blank=True, help_text='New value (JSON or plain text)')
    ip_address   = models.GenericIPAddressField(null=True, blank=True)
    timestamp    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes  = [
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['student', 'timestamp']),
            models.Index(fields=['college', 'timestamp']),
        ]

    def __str__(self):
        actor = self.performed_by.username if self.performed_by else 'system'
        return f"[{self.get_action_type_display()}] by {actor} at {self.timestamp:%Y-%m-%d %H:%M}"


# ── FEE INSTALLMENT & WAIVER ──────────────────────────────────────────────────

class FeeInstallmentPlan(models.Model):
    """
    Splits a Fee record into N installments with due dates.
    Admin creates the plan; system tracks payment per installment.
    """
    fee         = models.OneToOneField('Fee', on_delete=models.CASCADE, related_name='installment_plan')
    num_installments = models.PositiveIntegerField(default=2)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    note        = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Installment plan for {self.fee.student.roll_number} Sem {self.fee.semester}"


class FeeInstallment(models.Model):
    """One installment within a FeeInstallmentPlan."""
    STATUS = (
        ('PENDING', 'Pending'),
        ('PAID',    'Paid'),
        ('OVERDUE', 'Overdue'),
    )
    plan        = models.ForeignKey(FeeInstallmentPlan, on_delete=models.CASCADE,
                                    related_name='installments')
    number      = models.PositiveIntegerField(help_text='1, 2, 3…')
    amount      = models.FloatField()
    due_date    = models.DateField()
    paid_date   = models.DateField(null=True, blank=True)
    status      = models.CharField(max_length=10, choices=STATUS, default='PENDING')
    payment     = models.OneToOneField('Payment', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='installment')

    class Meta:
        unique_together = ('plan', 'number')
        ordering = ['number']

    def __str__(self):
        return f"Installment {self.number} — {self.plan.fee.student.roll_number} [{self.status}]"


class LateFeeRule(models.Model):
    """
    Configurable late fee penalty per college.
    e.g. Rs 50/day after due date, max Rs 500.
    """
    college         = models.OneToOneField('College', on_delete=models.CASCADE,
                                           related_name='late_fee_rule')
    penalty_per_day = models.FloatField(default=50.0, help_text='Rs per day after due date')
    max_penalty     = models.FloatField(default=500.0, help_text='Maximum penalty cap (Rs)')
    grace_days      = models.IntegerField(default=7, help_text='Days after due date before penalty starts')
    is_active       = models.BooleanField(default=False)

    def __str__(self):
        return f"Late fee rule — {self.college.code} (Rs {self.penalty_per_day}/day)"


class FeeWaiver(models.Model):
    """
    Admin grants a partial or full fee waiver to a student.
    Reduces the effective total_amount on the Fee record.
    """
    WAIVER_TYPES = (
        ('MERIT',       'Merit Scholarship'),
        ('NEED',        'Need-based'),
        ('SPORTS',      'Sports Quota'),
        ('MANAGEMENT',  'Management Discretion'),
        ('OTHER',       'Other'),
    )
    fee         = models.ForeignKey('Fee', on_delete=models.CASCADE, related_name='waivers')
    waiver_type = models.CharField(max_length=20, choices=WAIVER_TYPES)
    amount      = models.FloatField(help_text='Amount waived (Rs)')
    reason      = models.TextField()
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='approved_waivers')
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Waiver Rs {self.amount} for {self.fee.student.roll_number} [{self.waiver_type}]"


# ── GRACE MARKS (EvaluationScheme extension) ──────────────────────────────────
# Added as a separate model to avoid breaking the existing EvaluationScheme.
# Links to EvaluationScheme and defines grace marks rules.

class GraceMarksRule(models.Model):
    """
    Grace marks policy linked to an EvaluationScheme.
    e.g. up to 5 grace marks per subject to help borderline students pass.
    """
    scheme          = models.OneToOneField('EvaluationScheme', on_delete=models.CASCADE,
                                           related_name='grace_rule')
    max_grace_per_subject = models.FloatField(default=5.0,
                                               help_text='Max grace marks per subject')
    max_grace_total       = models.FloatField(default=10.0,
                                               help_text='Max total grace marks across all subjects')
    apply_only_if_failing = models.BooleanField(default=True,
                                                 help_text='Only apply grace to failing subjects')
    requires_approval     = models.BooleanField(default=True,
                                                 help_text='Exam controller must approve each application')
    is_active             = models.BooleanField(default=True)

    def __str__(self):
        return f"Grace rule for {self.scheme.name}"


class GraceMarksApplication(models.Model):
    """
    Records when grace marks are applied to a specific student's marks record.
    Full audit trail: who applied, how much, why.
    """
    STATUS = (
        ('PENDING',   'Pending Approval'),
        ('APPROVED',  'Approved'),
        ('REJECTED',  'Rejected'),
        ('APPLIED',   'Applied to Marks'),
    )
    marks       = models.ForeignKey('Marks', on_delete=models.CASCADE,
                                    related_name='grace_applications')
    rule        = models.ForeignKey(GraceMarksRule, on_delete=models.CASCADE)
    grace_amount = models.FloatField(help_text='Grace marks to add')
    reason      = models.TextField(blank=True)
    status      = models.CharField(max_length=10, choices=STATUS, default='PENDING')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     related_name='grace_requests')
    approved_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='grace_approvals')
    applied_at   = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Grace {self.grace_amount} for {self.marks.student.roll_number} — {self.marks.subject.code}"


# ── REGULATION VERSIONING & STUDENT ASSIGNMENT ───────────────────────────────

class StudentRegulation(models.Model):
    """
    Assigns a specific Regulation to a student.
    Immutable once set — changing requires explicit migration record.
    Supports lateral entry (different regulation than batch default).
    """
    student    = models.OneToOneField(Student, on_delete=models.CASCADE,
                                      related_name='regulation_assignment')
    regulation = models.ForeignKey(Regulation, on_delete=models.PROTECT,
                                   related_name='student_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_lateral  = models.BooleanField(default=False,
                                       help_text='True for lateral entry students')
    note        = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.student.roll_number} → {self.regulation.code}"


class RegulationMigration(models.Model):
    """
    Records when a student is moved from one regulation to another
    (e.g. mid-year regulation update, re-admission).
    Full audit trail — old regulation preserved.
    """
    student         = models.ForeignKey(Student, on_delete=models.CASCADE,
                                        related_name='regulation_migrations')
    from_regulation = models.ForeignKey(Regulation, on_delete=models.PROTECT,
                                        related_name='migrations_from')
    to_regulation   = models.ForeignKey(Regulation, on_delete=models.PROTECT,
                                        related_name='migrations_to')
    reason          = models.TextField()
    migrated_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    migrated_at     = models.DateTimeField(auto_now_add=True)
    backlog_subjects = models.ManyToManyField(Subject, blank=True,
                                              related_name='backlog_migrations',
                                              help_text='Subjects carried over as backlogs from old regulation')

    def __str__(self):
        return f"{self.student.roll_number}: {self.from_regulation.code} → {self.to_regulation.code}"


# ── PER-SUBJECT EVALUATION SCHEME OVERRIDE ───────────────────────────────────

class SubjectSchemeOverride(models.Model):
    """
    Overrides the default EvaluationScheme for a specific subject.
    e.g. a lab subject uses 100% internal, a project uses different weightage.
    Takes precedence over the department-level scheme.
    """
    subject     = models.OneToOneField(Subject, on_delete=models.CASCADE,
                                       related_name='scheme_override')
    scheme      = models.ForeignKey(EvaluationScheme, on_delete=models.CASCADE,
                                    related_name='subject_overrides')
    reason      = models.CharField(max_length=200)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject.code} → {self.scheme.name}"


# ── RESULT VERSIONING & FREEZE ────────────────────────────────────────────────

class ResultVersion(models.Model):
    """
    Snapshot of a Result at a point in time.
    Created before any modification (reval, moderation, correction).
    Enables full result history and rollback.
    """
    result      = models.ForeignKey(Result, on_delete=models.CASCADE,
                                    related_name='versions')
    version_no  = models.PositiveIntegerField(default=1)
    sgpa        = models.FloatField()
    total_marks = models.FloatField()
    percentage  = models.FloatField()
    snapshot_reason = models.CharField(max_length=100,
                                        help_text='e.g. "Before revaluation", "Before moderation"')
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('result', 'version_no')
        ordering = ['-version_no']

    def __str__(self):
        return f"{self.result.student.roll_number} Sem{self.result.semester} v{self.version_no}"


class ResultFreeze(models.Model):
    """
    Freezes results for a semester — no further edits allowed without unfreeze.
    Exam controller freezes after publication; unfreeze requires reason + approval.
    """
    college     = models.ForeignKey(College, on_delete=models.CASCADE,
                                    related_name='result_freezes')
    exam        = models.ForeignKey(Exam, on_delete=models.CASCADE,
                                    related_name='freeze_records')
    is_frozen   = models.BooleanField(default=False)
    frozen_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='frozen_results')
    frozen_at   = models.DateTimeField(null=True, blank=True)
    unfrozen_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='unfrozen_results')
    unfreeze_reason = models.TextField(blank=True)

    class Meta:
        unique_together = ('college', 'exam')

    def __str__(self):
        state = 'FROZEN' if self.is_frozen else 'OPEN'
        return f"{self.exam.name} [{state}]"


class MarksModeration(models.Model):
    """
    Bulk scaling of marks for a subject in an exam.
    e.g. add 5 marks to all students, or scale by 1.1x.
    Full audit trail — original marks preserved in ResultVersion.
    """
    MODERATION_TYPES = (
        ('ADD',   'Add flat marks to all'),
        ('SCALE', 'Scale by multiplier'),
        ('CAP',   'Cap at maximum'),
    )
    exam            = models.ForeignKey(Exam, on_delete=models.CASCADE,
                                        related_name='moderations')
    subject         = models.ForeignKey(Subject, on_delete=models.CASCADE,
                                        related_name='moderations')
    moderation_type = models.CharField(max_length=10, choices=MODERATION_TYPES)
    value           = models.FloatField(help_text='Marks to add, multiplier, or cap value')
    reason          = models.TextField()
    applied         = models.BooleanField(default=False)
    applied_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='applied_moderations')
    applied_at      = models.DateTimeField(null=True, blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                        related_name='created_moderations')
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Moderation: {self.subject.code} {self.exam.name} [{self.get_moderation_type_display()} {self.value}]"


# ── COMPOSITE ELIGIBILITY RULE ENGINE ────────────────────────────────────────

class ExamEligibilityConfig(models.Model):
    """
    Configurable eligibility criteria per college/exam.
    Defines which factors are checked and their thresholds.
    eligibility = f(attendance, fee, internal_marks, disciplinary_status)
    """
    college             = models.ForeignKey(College, on_delete=models.CASCADE,
                                            related_name='eligibility_configs')
    exam                = models.ForeignKey(Exam, on_delete=models.CASCADE,
                                            null=True, blank=True,
                                            related_name='eligibility_configs',
                                            help_text='Leave blank for college-wide default')
    # Attendance gate
    check_attendance    = models.BooleanField(default=True)
    min_attendance_pct  = models.FloatField(default=75.0)
    # Fee gate
    check_fee_clearance = models.BooleanField(default=True)
    allow_partial_fee   = models.BooleanField(default=False,
                                               help_text='Allow if at least partial payment made')
    # Internal marks gate
    check_internal_marks = models.BooleanField(default=False)
    min_internal_marks_pct = models.FloatField(default=0.0,
                                                help_text='Min % of internal marks to be eligible')
    # Disciplinary gate
    check_disciplinary  = models.BooleanField(default=False,
                                               help_text='Block if student has active disciplinary action')
    # Logic
    require_all_gates   = models.BooleanField(default=True,
                                               help_text='True = AND logic; False = OR logic')
    is_active           = models.BooleanField(default=True)

    class Meta:
        unique_together = ('college', 'exam')

    def __str__(self):
        exam_str = self.exam.name if self.exam else 'Default'
        return f"Eligibility config — {self.college.code} / {exam_str}"


# ── STUDENT LIFECYCLE ─────────────────────────────────────────────────────────

class StudentLifecycleEvent(models.Model):
    """
    Records every state transition in a student's lifecycle.
    Enables full history: Active → Detained → Active → Graduated
    """
    EVENT_TYPES = (
        ('ENROLLED',     'Enrolled'),
        ('PROMOTED',     'Promoted to next semester'),
        ('DETAINED',     'Detained — failed to meet criteria'),
        ('REINSTATED',   'Reinstated after detention'),
        ('SUSPENDED',    'Suspended — disciplinary action'),
        ('UNSUSPENDED',  'Suspension lifted'),
        ('DROPPED',      'Dropped out'),
        ('READMITTED',   'Re-admitted'),
        ('GRADUATED',    'Graduated'),
        ('TRANSFERRED',  'Transferred to another institution'),
    )
    student     = models.ForeignKey(Student, on_delete=models.CASCADE,
                                    related_name='lifecycle_events')
    event_type  = models.CharField(max_length=20, choices=EVENT_TYPES)
    from_status = models.CharField(max_length=20, blank=True)
    to_status   = models.CharField(max_length=20)
    from_semester = models.IntegerField(null=True, blank=True)
    to_semester   = models.IntegerField(null=True, blank=True)
    reason      = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.roll_number}: {self.event_type} at {self.created_at:%Y-%m-%d}"


class DisciplinaryRecord(models.Model):
    """
    Active disciplinary actions against a student.
    Blocks exam eligibility when check_disciplinary is enabled.
    """
    STATUS = (
        ('ACTIVE',   'Active'),
        ('RESOLVED', 'Resolved'),
        ('APPEALED', 'Under Appeal'),
    )
    student     = models.ForeignKey(Student, on_delete=models.CASCADE,
                                    related_name='disciplinary_records')
    description = models.TextField()
    status      = models.CharField(max_length=10, choices=STATUS, default='ACTIVE')
    raised_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='raised_disciplinary')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='resolved_disciplinary')
    resolution_note = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.roll_number} — {self.status}"


# ── ELECTIVE WAITLIST ─────────────────────────────────────────────────────────

class ElectiveWaitlist(models.Model):
    """
    When a student's first-choice elective is full, they go on the waitlist.
    Auto-allocation promotes from waitlist when a seat opens.
    """
    student     = models.ForeignKey(Student, on_delete=models.CASCADE,
                                    related_name='elective_waitlist')
    pool        = models.ForeignKey(ElectivePool, on_delete=models.CASCADE,
                                    related_name='waitlist')
    subject     = models.ForeignKey(Subject, on_delete=models.CASCADE,
                                    related_name='waitlist_entries')
    position    = models.PositiveIntegerField(help_text='Position in queue (1 = next to be allocated)')
    cgpa        = models.FloatField(default=0.0,
                                    help_text='CGPA at time of waitlisting — used for priority sorting')
    added_at    = models.DateTimeField(auto_now_add=True)
    promoted    = models.BooleanField(default=False)
    promoted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'pool', 'subject')
        ordering = ['position']

    def __str__(self):
        return f"Waitlist #{self.position}: {self.student.roll_number} → {self.subject.code}"


# ── COLLEGE FEATURE FLAGS ─────────────────────────────────────────────────────

class CollegeFeatureConfig(models.Model):
    """
    Per-college feature toggles and workflow customizations.
    Enables/disables modules and configures behavior without code changes.
    """
    college = models.OneToOneField(College, on_delete=models.CASCADE,
                                   related_name='feature_config')
    # Module toggles
    enable_electives        = models.BooleanField(default=True)
    enable_online_payment   = models.BooleanField(default=True)
    enable_quiz_module      = models.BooleanField(default=True)
    enable_assignment_module = models.BooleanField(default=True)
    enable_lesson_plans     = models.BooleanField(default=True)
    enable_helpdesk         = models.BooleanField(default=True)
    enable_supply_exam      = models.BooleanField(default=True)
    enable_revaluation      = models.BooleanField(default=True)
    enable_grace_marks      = models.BooleanField(default=False)
    enable_fee_installments = models.BooleanField(default=False)
    enable_late_fee_penalty = models.BooleanField(default=False)
    enable_disciplinary_check = models.BooleanField(default=False)
    # Workflow customizations
    require_hod_for_attendance_correction = models.BooleanField(default=False)
    require_principal_for_result_publish  = models.BooleanField(default=False)
    auto_promote_students               = models.BooleanField(default=False,
                                                               help_text='Auto-promote at semester end if passing')
    elective_allocation_mode = models.CharField(
        max_length=20,
        choices=[('MANUAL', 'Manual (admin confirms)'), ('AUTO_CGPA', 'Auto by CGPA'), ('FCFS', 'First Come First Served')],
        default='MANUAL'
    )
    # Course Registration window — admin opens this per semester to allow students to register
    course_registration_open = models.BooleanField(
        default=False,
        help_text='When True, students can see and submit course registration for the next semester.'
    )
    course_registration_semester = models.IntegerField(
        null=True, blank=True,
        help_text='Which semester the open registration window is for (e.g. 3 means Sem 3 registration is open).'
    )
    # Faculty Leave & Substitution quotas
    max_casual_leaves   = models.IntegerField(default=12, help_text='Max Casual Leave days per faculty per year')
    max_medical_leaves  = models.IntegerField(default=10, help_text='Max Medical Leave days per faculty per year')
    max_earned_leaves   = models.IntegerField(default=15, help_text='Max Earned Leave days per faculty per year')
    max_od_leaves       = models.IntegerField(default=20, help_text='Max On Duty days per faculty per year')
    max_substitutions   = models.IntegerField(default=10, help_text='Max substitution requests per faculty per semester')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Feature config — {self.college.code}"


# ── SEMESTER RESULT BATCH ─────────────────────────────────────────────────────

class SemesterResultBatch(models.Model):
    STATUS_CHOICES = (
        ('UPLOADED',  'Uploaded'),
        ('GENERATED', 'Generated'),
        ('APPROVED',  'Approved'),
    )
    college       = models.ForeignKey(College, on_delete=models.CASCADE, related_name='semester_result_batches')
    department    = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='semester_result_batches')
    academic_year = models.CharField(max_length=20)
    semester      = models.PositiveIntegerField()
    uploaded_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='semester_result_uploads')
    source_file   = models.FileField(upload_to='semester_results/uploads/')
    generated_pdf = models.FileField(upload_to='semester_results/generated/', null=True, blank=True)
    status        = models.CharField(max_length=12, choices=STATUS_CHOICES, default='UPLOADED')
    student_count = models.PositiveIntegerField(default=0)
    subject_count = models.PositiveIntegerField(default=0)
    uploaded_at   = models.DateTimeField(auto_now_add=True)
    generated_at  = models.DateTimeField(null=True, blank=True)
    approved_at   = models.DateTimeField(null=True, blank=True)
    approved_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='approved_semester_result_batches')

    class Meta:
        ordering = ['-uploaded_at', '-id']

    def __str__(self):
        return f"{self.academic_year} - {self.department.code} - Sem {self.semester} - Batch {self.pk}"


class SemesterResultStudent(models.Model):
    STATUS_CHOICES = (
        ('GENERATED', 'Generated'),
        ('APPROVED',  'Approved'),
    )
    batch                 = models.ForeignKey(SemesterResultBatch, on_delete=models.CASCADE, related_name='student_results')
    student               = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='semester_result_transcripts')
    roll_number_snapshot  = models.CharField(max_length=50)
    username_snapshot     = models.CharField(max_length=150)
    full_name_snapshot    = models.CharField(max_length=255, blank=True, default='')
    total_marks_obtained  = models.FloatField(default=0)
    total_max_marks       = models.FloatField(default=0)
    percentage            = models.FloatField(default=0)
    sgpa                  = models.FloatField(default=0)
    cgpa                  = models.FloatField(default=0)
    semester_credits      = models.PositiveIntegerField(default=0)
    overall_credits       = models.PositiveIntegerField(default=0)
    result_status         = models.CharField(max_length=10, default='PASS')
    pdf_file              = models.FileField(upload_to='semester_results/students/', null=True, blank=True)
    status                = models.CharField(max_length=12, choices=STATUS_CHOICES, default='GENERATED')
    generated_at          = models.DateTimeField(auto_now_add=True)
    approved_at           = models.DateTimeField(null=True, blank=True)
    approved_by           = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                              related_name='approved_semester_result_students')

    class Meta:
        unique_together = ('batch', 'student')
        ordering = ['student__roll_number', 'id']

    def __str__(self):
        return f"{self.roll_number_snapshot} - {self.batch.academic_year} Sem {self.batch.semester}"


class SemesterResultSubject(models.Model):
    student_result        = models.ForeignKey(SemesterResultStudent, on_delete=models.CASCADE, related_name='subjects')
    subject               = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='semester_result_subjects')
    subject_code_snapshot = models.CharField(max_length=50)
    subject_name_snapshot = models.CharField(max_length=255)
    marks_obtained        = models.FloatField(default=0)
    max_marks             = models.FloatField(default=100)
    grade                 = models.CharField(max_length=5, blank=True, default='')
    grade_point           = models.FloatField(default=0.0)
    status                = models.CharField(max_length=10, default='PASS')
    credits               = models.PositiveIntegerField(default=0)
    display_order         = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('student_result', 'subject')
        ordering = ['display_order', 'subject_code_snapshot', 'id']

    def __str__(self):
        return f"{self.student_result.roll_number_snapshot} - {self.subject_code_snapshot}"
