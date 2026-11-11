from django.urls import reverse
from rest_framework import serializers
from .models import (
    Assignment,
    Attendance,
    Department,
    Flyer,
    HomepageBackground,
    Courses,
    Student,
    Submission,
)

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class CoursesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'


class DepartmentDirectoryStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ("id", "full_name")


class DepartmentDirectoryCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = ("id", "course_name")


class DepartmentDirectorySerializer(serializers.ModelSerializer):
    students = DepartmentDirectoryStudentSerializer(source="dept", many=True, read_only=True)
    courses = DepartmentDirectoryCourseSerializer(source="depts", many=True, read_only=True)

    class Meta:
        model = Department
        fields = ("id", "name", "students", "courses")


class FlyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flyer
        fields = ("id", "title", "caption", "image", "link", "created_at")
        read_only_fields = ("id", "created_at")


class HomepageBackgroundSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomepageBackground
        fields = ("image", "updated_at")
        read_only_fields = ("updated_at",)


class StudentProfileSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="depts.name", read_only=True)

    class Meta:
        model = Student
        fields = ("id", "full_name", "age", "depts", "department_name")
        read_only_fields = ("id", "depts", "department_name")


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = Attendance
        fields = ("id", "student", "student_name", "date", "status", "recorded_by", "created_at")
        read_only_fields = ("id", "recorded_by", "created_at")


class AssignmentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.course_name", read_only=True)
    department = serializers.PrimaryKeyRelatedField(
        source="dept_s",
        queryset=Department.objects.all(),
    )
    department_name = serializers.CharField(source="dept_s.name", read_only=True)
    posted_by_name = serializers.CharField(source="posted_by.username", read_only=True)

    class Meta:
        model = Assignment
        fields = (
            "id",
            "course",
            "course_name",
            "department",
            "department_name",
            "title",
            "description",
            "attachment",
            "due_date",
            "posted_by",
            "posted_by_name",
            "created_at",
        )
        read_only_fields = ("id", "posted_by", "created_at")

    def validate(self, attrs):
        course = attrs.get("course", getattr(self.instance, "course", None))
        department = attrs.get("dept_s", getattr(self.instance, "dept_s", None))
        if course and department and course.dept_id != department.pk:
            raise serializers.ValidationError(
                {"department": "The department must match the selected course."}
            )
        return attrs


class SubmissionSerializer(serializers.ModelSerializer):
    assignment_title = serializers.CharField(source="assignment.title", read_only=True)
    course_name = serializers.CharField(source="assignment.course.course_name", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    file_name = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = (
            "id",
            "assignment",
            "assignment_title",
            "course_name",
            "student_name",
            "file",
            "file_name",
            "download_url",
            "comment",
            "submitted_at",
        )
        read_only_fields = (
            "id",
            "assignment_title",
            "course_name",
            "student_name",
            "file_name",
            "download_url",
            "submitted_at",
        )
        extra_kwargs = {"file": {"write_only": True}}

    def get_file_name(self, obj):
        return obj.file.name.rsplit("/", 1)[-1]

    def get_download_url(self, obj):
        return reverse("submission-download", kwargs={"pk": obj.pk})