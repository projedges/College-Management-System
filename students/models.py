from django.db import models
from django.contrib.auth.models import User


# USER ROLE MODEL

class UserRole(models.Model):
    ROLE_CHOICES = (
        (1, 'Admin'),
        (2, 'HOD'),
        (3, 'Faculty'),
        (4, 'Student'),
        (5, 'Lab Staff'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.IntegerField(choices=ROLE_CHOICES, default=4)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

# DEPARTMENT MODEL
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)

    description = models.TextField(null=True, blank=True)
    established_year = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

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

    def __str__(self):
        return self.roll_number


# STUDENT PROFILE MODEL
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Basic Info
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)

    # Contact
    phone_number = models.CharField(max_length=15)

    # Government ID (handle securely in real apps)
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
        return f"{self.first_name} {self.last_name}"


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
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.IntegerField()
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    def __str__(self):
        return f"Role {self.role} - {self.permission.name}"
    



class HOD(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    employee_id = models.CharField(max_length=50, unique=True)

    department = models.OneToOneField(
        Department,
        on_delete=models.CASCADE,
        related_name='hod'   # 🔥 IMPORTANT FIX
    )

    phone_number = models.CharField(max_length=15)
    qualification = models.CharField(max_length=100)
    experience_years = models.IntegerField()

    def __str__(self):
        return f"HOD - {self.user.username}"
    

    
# FACULTY MODEL
class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    employee_id = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    designation = models.CharField(max_length=100)  # Assistant Prof, etc.
    qualification = models.CharField(max_length=100)
    experience_years = models.IntegerField()

    phone_number = models.CharField(max_length=15)

    joined_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# SUBJECT MODEL
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.IntegerField()

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
    room_number = models.CharField(max_length=20)
    capacity = models.IntegerField()

    def __str__(self):
        return self.room_number
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

class Semester(models.Model):
    number = models.IntegerField()
    year = models.IntegerField()

    def __str__(self):
        return f"Sem {self.number}"
class AttendanceSession(models.Model):

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

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

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    file = models.FileField(upload_to='assignments/')
    submitted_at = models.DateTimeField(auto_now_add=True)

    marks = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.student} - {self.assignment}"
    
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


