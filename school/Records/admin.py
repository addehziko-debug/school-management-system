from django.contrib import admin
from .models import Assignment, Attendance, Department, Flyer, Courses, Student

# Register your models here.
@admin.register(Department)
class DepartAdmin(admin.ModelAdmin):
    list_display = ['name', 'date']
    search_fields = ['name']


@admin.register(Flyer)
class FlyerAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at']
    search_fields = ['title', 'caption']
    readonly_fields = ['created_by', 'created_at']

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Courses)
class CoursesAdmin(admin.ModelAdmin):
    list_display = ['course_name', 'start_date', 'end_date', 'dept']
    search_fields = ['course_name']

@admin.register(Student)
class Student(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'age', 'depts']
    list_filter = ['depts']
    search_fields = ['full_name', 'user__username']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'recorded_by']
    list_filter = ['status', 'date']
    search_fields = ['student__full_name']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'dept_s', 'course', 'due_date', 'posted_by']
    list_filter = ['dept_s', 'course', 'due_date']
    search_fields = ['title', 'description']
    readonly_fields = ['posted_by', 'created_at']

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.posted_by = request.user
        super().save_model(request, obj, form, change)