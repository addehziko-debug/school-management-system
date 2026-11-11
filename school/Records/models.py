from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.deconstruct import deconstructible

# Create your models here.

@deconstructible
class PrivateSubmissionStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT)


class Department(models.Model):
    name = models.CharField(max_length=30)
    date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name
    

class Flyer(models.Model):
    title = models.CharField(max_length=100)
    caption = models.CharField(max_length=300, blank=True)
    image = models.FileField(
        upload_to="flyers/",
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "gif", "webp"])],
    )
    link = models.URLField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="posted_flyers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title


class HomepageBackground(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    image = models.FileField(
        upload_to="homepage/",
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "gif", "webp"])],
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Homepage background"


class Courses(models.Model):
    dept = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='depts')
    course_name = models.CharField(max_length=50)
    start_date = models.DateField(auto_now=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.course_name

class Student(models.Model):
    depts = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='dept')
    full_name = models.CharField(max_length=20)
    age = models.PositiveIntegerField(default=15)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
    )

    def __str__(self):
        return self.full_name


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"
        EXCUSED = "excused", "Excused"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    status = models.CharField(max_length=8, choices=Status.choices)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recorded_attendance",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("student", "date"), name="unique_student_attendance_date"),
        ]
        ordering = ("-date", "student__full_name")

    def __str__(self):
        return f"{self.student} - {self.date}: {self.status}"


class Assignment(models.Model):
    dept_s = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    course = models.ForeignKey(Courses, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    attachment = models.FileField(upload_to="assignments/", blank=True)
    due_date = models.DateField()
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="posted_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("due_date", "title")

    def __str__(self):
        return self.title


class Submission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="submissions")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    file = models.FileField(upload_to="submissions/", storage=PrivateSubmissionStorage())
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-submitted_at",)

    def __str__(self):
        return f"{self.student} - {self.assignment}"
