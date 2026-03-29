from django.contrib import admin
from .models import (
    UserRole, College, Department, Student, StudentProfile,
    Address, Parent, EmergencyContact, UserSecurity,
    Course, Enrollment, AdminProfile, Announcement,
    Notification, ActivityLog, Payment, PaymentReceipt,
    SystemReport, SystemSetting, Permission, RolePermission,
    RegistrationRequest, RegistrationInvite, HelpDeskTicket,
    Principal,
    HOD, Faculty, Subject, FacultySubject, HODApproval,
    FacultyAttendance, FacultyPerformance, FacultyAvailability, CourseSubject,
    Classroom, Timetable, Semester, AttendanceSession,
    Attendance, Exam, Marks, Result, Assignment,
    AssignmentSubmission, Fee
)

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'city', 'state')
    search_fields = ('name', 'code')

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'college')
    list_filter = ('role', 'college')
    search_fields = ('user__username', 'college__name')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'college', 'established_year')
    list_filter = ('college',)
    search_fields = ('name', 'code', 'college__name')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'user', 'department', 'current_semester', 'status')
    list_filter = ('status', 'department')
    search_fields = ('roll_number', 'user__username')

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'department', 'designation')
    search_fields = ('user__username', 'employee_id')

@admin.register(HOD)
class HODAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'department')
    search_fields = ('user__username', 'employee_id')

@admin.register(Principal)
class PrincipalAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'college')
    search_fields = ('user__username', 'employee_id', 'college__name')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department', 'semester')
    list_filter = ('department__college', 'department', 'semester')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'status')
    list_filter = ('status',)

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'college', 'semester', 'start_date', 'end_date')
    list_filter = ('college', 'semester')

@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'exam', 'marks_obtained', 'max_marks', 'grade')

@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'total_amount', 'paid_amount', 'status')
    list_filter = ('status',)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'college', 'created_by', 'created_at')
    list_filter = ('college',)

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('subject', 'faculty', 'day_of_week', 'start_time', 'end_time', 'classroom')
    list_filter = ('day_of_week',)

# Register remaining models simply
for model in [
    StudentProfile, Address, Parent, EmergencyContact, UserSecurity,
    Course, Enrollment, AdminProfile, Notification, ActivityLog,
    Payment, PaymentReceipt, SystemReport, SystemSetting,
    Permission, RolePermission, FacultySubject, HODApproval,
    FacultyAttendance, FacultyPerformance, FacultyAvailability, CourseSubject,
    Classroom, Semester, AttendanceSession, Result, RegistrationRequest,
    RegistrationInvite, HelpDeskTicket,
    Assignment, AssignmentSubmission
]:
    admin.site.register(model)
