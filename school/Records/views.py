from pathlib import Path

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import (
    DestroyAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import (
    SAFE_METHODS,
    AllowAny,
    BasePermission,
    IsAdminUser,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

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
from .serializers import (
    AssignmentSerializer,
    AttendanceSerializer,
    DepartmentSerializer,
    DepartmentDirectorySerializer,
    FlyerSerializer,
    HomepageBackgroundSerializer,
    CoursesSerializer,
    StudentProfileSerializer,
    StudentSerializer,
    SubmissionSerializer,
)
# Create your views here.

class IsSuperUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class PortalHome(TemplateView):
    template_name = "Records/portal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["homepage_background"] = HomepageBackground.objects.filter(pk=1).first()
        return context


class HomepageBackgroundView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsSuperUserOrReadOnly]
    parser_classes = [FormParser, MultiPartParser]

    def get(self, request):
        background = HomepageBackground.objects.filter(pk=1).first()
        if background is None:
            return Response({"image": None})
        return Response(HomepageBackgroundSerializer(background, context={"request": request}).data)

    def post(self, request):
        background = HomepageBackground.objects.filter(pk=1).first()
        old_image = background.image if background else None
        serializer = HomepageBackgroundSerializer(
            background,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        background = serializer.save()
        if old_image and old_image.name != background.image.name:
            old_image.delete(save=False)
        return Response(
            HomepageBackgroundSerializer(background, context={"request": request}).data,
            status=200 if old_image else 201,
        )

    def delete(self, request):
        background = HomepageBackground.objects.filter(pk=1).first()
        if background is None:
            return Response(status=404)
        background.image.delete(save=False)
        background.delete()
        return Response(status=204)


class DepartmentDirectoryPage(TemplateView):
    template_name = "Records/departments.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["departments"] = Department.objects.prefetch_related("dept", "depts")
        return context


class StudentPortal(TemplateView):
    template_name = "Records/student_portal.html"


class Depts(ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsSuperUserOrReadOnly]


class DepartmentDirectory(ListAPIView):
    queryset = Department.objects.prefetch_related("dept", "depts").all()
    serializer_class = DepartmentDirectorySerializer


class Flyers(ListCreateAPIView):
    serializer_class = FlyerSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsSuperUserOrReadOnly]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_queryset(self):
        return Flyer.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FlyerDelete(DestroyAPIView):
    queryset = Flyer.objects.all()
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsSuperUserOrReadOnly]

    def perform_destroy(self, instance):
        instance.image.delete(save=False)
        instance.delete()


class Dept(RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsSuperUserOrReadOnly]

class Course(RetrieveUpdateDestroyAPIView):
    queryset = Courses.objects.all()
    serializer_class= CoursesSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsSuperUserOrReadOnly]

class Courses(ListCreateAPIView):
    queryset = Courses.objects.all()
    serializer_class= CoursesSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsSuperUserOrReadOnly]

class Student_i(RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    serializer_class= StudentSerializer

class Students(ListCreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class Assignments(ListCreateAPIView):
    queryset = Assignment.objects.select_related("course", "posted_by").all()
    serializer_class = AssignmentSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return queryset.filter(posted_by=self.request.user)
        return queryset

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)


class AttendanceRecords(ListCreateAPIView):
    queryset = Attendance.objects.select_related("student", "recorded_by").all()
    serializer_class = AttendanceSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


class StudentProfile(RetrieveUpdateAPIView):
    serializer_class = StudentProfileSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "put", "head", "options"]

    def get_queryset(self):
        return Student.objects.select_related("depts").filter(user=self.request.user)

    def get_object(self):
        student = self.get_queryset().first()
        if student is None:
            raise Http404
        self.check_object_permissions(self.request, student)
        return student


class StudentAssignments(ListAPIView):
    serializer_class = AssignmentSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        student = Student.objects.filter(user=self.request.user).first()
        if student is None:
            raise PermissionDenied("This account is not linked to a student profile.")
        return Assignment.objects.select_related(
            "course",
            "course__dept",
            "dept_s",
            "posted_by",
        ).filter(dept_s_id=student.depts_id)


class StudentSubmissions(ListCreateAPIView):
    serializer_class = SubmissionSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_student(self):
        student = Student.objects.filter(user=self.request.user).first()
        if student is None:
            raise PermissionDenied("This account is not linked to a student profile.")
        return student

    def get_queryset(self):
        return Submission.objects.select_related(
            "assignment__course",
            "student",
        ).filter(student=self.get_student())

    def perform_create(self, serializer):
        student = self.get_student()
        assignment = serializer.validated_data["assignment"]
        if assignment.dept_s_id != student.depts_id:
            raise ValidationError(
                {"assignment": "You can only submit assignments for your department."}
            )
        serializer.save(student=student)


class StaffSubmissions(ListAPIView):
    serializer_class = SubmissionSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Submission.objects.select_related(
            "assignment__course",
            "assignment__posted_by",
            "student",
        ).filter(assignment__posted_by=self.request.user)


class SubmissionDownload(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        submission = get_object_or_404(
            Submission.objects.select_related("student", "assignment__posted_by"),
            pk=pk,
        )
        if not request.user.is_staff and submission.student.user_id != request.user.pk:
            raise PermissionDenied("You can only download your own submissions.")
        if (
            request.user.is_staff
            and not request.user.is_superuser
            and submission.assignment.posted_by_id != request.user.pk
        ):
            raise PermissionDenied("You can only download submissions for your assignments.")

        return FileResponse(
            submission.file.open("rb"),
            as_attachment=True,
            filename=Path(submission.file.name).name,
        )