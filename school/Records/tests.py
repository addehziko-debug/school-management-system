from datetime import date
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    Assignment,
    Attendance,
    Courses,
    Department,
    Flyer,
    HomepageBackground,
    Student,
    Submission,
)


class StudentPortalApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="admin",
            password="admin-password",
            is_staff=True,
        )
        self.student_user = user_model.objects.create_user(
            username="student-user",
            password="student-password",
        )
        department = Department.objects.create(name="Science")
        self.course = Courses.objects.create(dept=department, course_name="Biology")
        self.student = Student.objects.create(depts=department, full_name="Alex Student")
        self.student.user = self.student_user
        self.student.save(update_fields=["user"])

    def test_portal_page_renders_template_and_static_assets(self):
        response = self.client.get("/portal/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Learning, in one place.")
        self.assertContains(response, "Records/portal.css")
        self.assertContains(response, "Records/theme.css")
        self.assertContains(response, "Records/theme.js")
        self.assertContains(response, "data-theme-toggle")
        self.assertContains(response, "Records/portal.js")
        self.assertNotContains(response, 'id="department-directory"')
        self.assertContains(response, 'href="/portal/departments/"')

    def test_department_directory_is_on_its_own_page(self):
        response = self.client.get("/portal/departments/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Departments")
        self.assertContains(response, self.student.full_name)
        self.assertContains(response, self.course.course_name)
        self.assertContains(response, "data-theme-toggle")
        self.assertContains(response, "Records/theme.js")

    def test_student_portal_page_renders(self):
        response = self.client.get("/portal/student/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Student space")
        self.assertContains(response, "student_portal.js")
        self.assertContains(response, "data-theme-toggle")
        self.assertContains(response, "Records/theme.js")

    def test_only_superusers_can_create_departments_and_courses(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/portal/Depts/", {"name": "Arts"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.post(
            "/portal/Courses/",
            {"dept": self.student.depts_id, "course_name": "History"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Department.objects.filter(name="Arts").exists())
        self.assertFalse(Courses.objects.filter(course_name="History").exists())

        superuser = get_user_model().objects.create_superuser(
            username="superuser",
            password="Secure-test-password-2026",
        )
        self.client.force_authenticate(user=superuser)
        response = self.client.post(
            "/portal/Depts/",
            {"name": "Arts", "date": None},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        department_id = response.data["id"]
        response = self.client.post(
            "/portal/Courses/",
            {"dept": department_id, "course_name": "History"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Courses.objects.get(course_name="History").dept_id, department_id)

    def test_catalog_reads_remain_public_and_superuser_status_is_reported(self):
        self.assertEqual(self.client.get("/portal/Depts/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get("/portal/Courses/").status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_superuser"])

        superuser = get_user_model().objects.create_superuser(
            username="superuser",
            password="Secure-test-password-2026",
        )
        self.client.force_authenticate(user=superuser)
        response = self.client.get("/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_superuser"])

    def test_department_directory_groups_students_and_courses_by_department(self):
        arts = Department.objects.create(name="Arts")
        arts_student = Student.objects.create(depts=arts, full_name="Jamie Artist")
        arts_course = Courses.objects.create(dept=arts, course_name="Painting")

        response = self.client.get("/portal/department-directory/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        departments = {item["name"]: item for item in response.data}
        self.assertEqual(
            departments["Science"]["students"],
            [{"id": self.student.pk, "full_name": self.student.full_name}],
        )
        self.assertEqual(
            departments["Science"]["courses"],
            [{"id": self.course.pk, "course_name": self.course.course_name}],
        )
        self.assertEqual(
            departments["Arts"]["students"],
            [{"id": arts_student.pk, "full_name": arts_student.full_name}],
        )
        self.assertEqual(
            departments["Arts"]["courses"],
            [{"id": arts_course.pk, "course_name": arts_course.course_name}],
        )

    def test_only_superusers_can_publish_and_remove_homepage_flyers(self):
        uploaded_image = SimpleUploadedFile(
            "campus-flyer.png",
            b"not an actual image, only a file upload test",
            content_type="image/png",
        )
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.assertEqual(self.client.get("/portal/flyers/").status_code, status.HTTP_200_OK)
            self.client.force_authenticate(user=self.admin)
            response = self.client.post(
                "/portal/flyers/",
                {"title": "Campus event", "image": uploaded_image},
                format="multipart",
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertFalse(Flyer.objects.exists())

            superuser = get_user_model().objects.create_superuser(
                username="flyer-admin",
                password="Secure-test-password-2026",
            )
            self.client.force_authenticate(user=superuser)
            response = self.client.post(
                "/portal/flyers/",
                {
                    "title": "Campus event",
                    "caption": "Join us",
                    "image": SimpleUploadedFile(
                        "campus-flyer.png",
                        b"not an actual image, only a file upload test",
                        content_type="image/png",
                    ),
                },
                format="multipart",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
            flyer = Flyer.objects.get()
            self.addCleanup(lambda: flyer.image.delete(save=False))
            self.assertEqual(response.data["title"], "Campus event")
            self.assertIn("flyers/", response.data["image"])

            self.client.force_authenticate(user=None)
            response = self.client.get("/portal/flyers/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 1)

            self.client.force_authenticate(user=superuser)
            response = self.client.delete(f"/portal/flyers/{flyer.pk}/")
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            self.assertFalse(Flyer.objects.exists())

    def test_only_superusers_can_set_or_remove_the_homepage_background(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.get("/portal/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertNotContains(response, "site-background")
            self.assertEqual(
                self.client.get("/portal/homepage-background/").data,
                {"image": None},
            )

            upload = SimpleUploadedFile(
                "campus-background.png",
                b"not an actual image, only a file upload test",
                content_type="image/png",
            )
            self.client.force_authenticate(user=self.admin)
            response = self.client.post(
                "/portal/homepage-background/",
                {"image": upload},
                format="multipart",
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertFalse(HomepageBackground.objects.exists())

            superuser = get_user_model().objects.create_superuser(
                username="background-admin",
                password="test-password",
            )
            self.client.force_authenticate(user=superuser)
            response = self.client.post(
                "/portal/homepage-background/",
                {
                    "image": SimpleUploadedFile(
                        "campus-background.png",
                        b"not an actual image, only a file upload test",
                        content_type="image/png",
                    ),
                },
                format="multipart",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
            background = HomepageBackground.objects.get()
            self.addCleanup(lambda: background.image.delete(save=False))
            self.assertIn("homepage/", background.image.name)

            response = self.client.get("/portal/")
            self.assertContains(response, "site-background")
            self.assertContains(response, background.image.url)
            self.client.force_authenticate(user=None)
            self.assertEqual(
                self.client.get("/portal/homepage-background/").status_code,
                status.HTTP_200_OK,
            )

            self.client.force_authenticate(user=superuser)
            response = self.client.delete("/portal/homepage-background/")
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            self.assertFalse(HomepageBackground.objects.exists())

    def test_student_can_view_and_edit_only_editable_profile_fields(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get("/portal/student/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["department_name"], "Science")

        response = self.client.patch(
            "/portal/student/profile/",
            {"full_name": "Alex Updated", "age": 17, "depts": 999},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student.refresh_from_db()
        self.assertEqual(self.student.full_name, "Alex Updated")
        self.assertEqual(self.student.age, 17)
        self.assertEqual(self.student.depts.name, "Science")

    def test_student_profile_requires_authentication_and_ownership(self):
        response = self.client.get("/portal/student/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        other_user = get_user_model().objects.create_user(
            username="other-student",
            password="student-password",
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.get("/portal/student/profile/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_can_post_assignment(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/portal/assignments/",
            {
                "course": self.course.pk,
                "department": self.student.depts_id,
                "title": "Lab report",
                "description": "Complete the report.",
                "due_date": "2026-12-01",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assignment = Assignment.objects.get()
        self.assertEqual(assignment.posted_by, self.admin)
        self.assertEqual(response.data["course_name"], self.course.course_name)
        self.assertEqual(response.data["department"], self.student.depts_id)
        self.assertEqual(response.data["department_name"], "Science")
        self.assertEqual(response.data["posted_by_name"], self.admin.username)

    def test_staff_cannot_target_assignment_to_department_other_than_course(self):
        other_department = Department.objects.create(name="Arts")
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/portal/assignments/",
            {
                "course": self.course.pk,
                "department": other_department.pk,
                "title": "Incorrectly targeted assignment",
                "due_date": "2026-12-01",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Assignment.objects.exists())

    def test_staff_can_upload_an_assignment_attachment(self):
        self.client.force_authenticate(user=self.admin)
        uploaded_file = SimpleUploadedFile(
            "instructions.txt",
            b"Complete questions 1-5.",
            content_type="text/plain",
        )

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                "/portal/assignments/",
                {
                    "course": self.course.pk,
                    "department": self.student.depts_id,
                    "title": "Lab report",
                    "description": "Complete the report.",
                    "due_date": "2026-12-01",
                    "attachment": uploaded_file,
                },
                format="multipart",
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            assignment = Assignment.objects.get()
            self.assertTrue(assignment.attachment.name.startswith("assignments/"))
            self.assertIn("/media/assignments/", response.data["attachment"])

    def test_non_staff_cannot_post_assignment(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.post(
            "/portal/assignments/",
            {"course": self.course.pk, "title": "Lab report", "due_date": "2026-12-01"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Assignment.objects.exists())

    def test_assignment_list_is_readable_without_admin_access(self):
        Assignment.objects.create(
            course=self.course,
            dept_s=self.student.depts,
            title="Lab report",
            due_date=date(2026, 12, 1),
            posted_by=self.admin,
        )

        response = self.client.get("/portal/assignments/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_staff_assignment_list_shows_only_assignments_they_posted(self):
        own_assignment = Assignment.objects.create(
            course=self.course,
            dept_s=self.student.depts,
            title="My assignment",
            due_date=date(2026, 12, 1),
            posted_by=self.admin,
        )
        other_staff = get_user_model().objects.create_user(
            username="other-staff",
            password="Secure-test-password-2026",
            is_staff=True,
        )
        other_assignment = Assignment.objects.create(
            course=self.course,
            dept_s=self.student.depts,
            title="Another staff assignment",
            due_date=date(2026, 12, 2),
            posted_by=other_staff,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/portal/assignments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [own_assignment.pk])

        self.client.force_authenticate(user=other_staff)
        response = self.client.get("/portal/assignments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [other_assignment.pk])

        self.client.force_authenticate(user=self.student_user)
        response = self.client.get("/portal/assignments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {item["id"] for item in response.data},
            {own_assignment.pk, other_assignment.pk},
        )

    def test_student_only_sees_assignments_for_their_department(self):
        own_assignment = Assignment.objects.create(
            course=self.course,
            dept_s=self.student.depts,
            title="Science assignment",
            due_date=date(2026, 12, 1),
            posted_by=self.admin,
        )
        other_department = Department.objects.create(name="Arts")
        other_course = Courses.objects.create(dept=other_department, course_name="History")
        Assignment.objects.create(
            course=other_course,
            dept_s=other_department,
            title="Arts assignment",
            due_date=date(2026, 12, 2),
            posted_by=self.admin,
        )
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get("/portal/student/assignments/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [own_assignment.pk])
        self.assertEqual(response.data[0]["department_name"], "Science")

    def test_student_assignment_list_requires_a_linked_student_profile(self):
        unlinked_user = get_user_model().objects.create_user(
            username="unlinked",
            password="student-password",
        )
        self.client.force_authenticate(user=unlinked_user)

        response = self.client.get("/portal/student/assignments/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_submit_and_only_download_their_own_work(self):
        assignment = Assignment.objects.create(
            course=self.course,
            dept_s=self.student.depts,
            title="Lab report",
            due_date=date(2026, 12, 1),
            posted_by=self.admin,
        )
        self.client.force_authenticate(user=self.student_user)
        response = self.client.post(
            "/portal/student/submissions/",
            {
                "assignment": assignment.pk,
                "file": SimpleUploadedFile("report.txt", b"my work", content_type="text/plain"),
                "comment": "Please see my answer.",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission = Submission.objects.get(student=self.student, assignment=assignment)
        self.addCleanup(lambda: submission.file.delete(save=False))
        self.assertTrue(str(submission.file.path).startswith(str(settings.PRIVATE_MEDIA_ROOT)))
        self.assertEqual(response.data["assignment_title"], assignment.title)
        self.assertEqual(response.data["file_name"], "report.txt")
        self.assertNotIn("private_media", response.data["download_url"])
        student_download_url = response.data["download_url"]

        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/portal/staff/submissions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["student_name"], self.student.full_name)
        self.assertEqual(response.data[0]["assignment"], assignment.pk)
        staff_download_url = response.data[0]["download_url"]

        self.client.force_authenticate(user=self.student_user)
        self.assertEqual(
            self.client.get("/portal/staff/submissions/").status_code,
            status.HTTP_403_FORBIDDEN,
        )

        other_staff = get_user_model().objects.create_user(
            username="other-staff",
            password="Secure-test-password-2026",
            is_staff=True,
        )
        self.client.force_authenticate(user=other_staff)
        self.assertEqual(self.client.get("/portal/staff/submissions/").data, [])
        self.assertEqual(
            self.client.get(staff_download_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(staff_download_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(b"".join(response.streaming_content), b"my work")

        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(student_download_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(b"".join(response.streaming_content), b"my work")

        other_user = get_user_model().objects.create_user(
            username="other-student",
            password="student-password",
        )
        Student.objects.create(
            user=other_user,
            depts=self.student.depts,
            full_name="Other Student",
        )
        self.client.force_authenticate(user=other_user)
        self.assertEqual(
            self.client.get("/portal/student/submissions/").data,
            [],
        )
        response = self.client.get(f"/portal/student/submissions/{submission.pk}/download/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_submit_assignment_for_another_department(self):
        other_department = Department.objects.create(name="Arts")
        other_course = Courses.objects.create(dept=other_department, course_name="History")
        assignment = Assignment.objects.create(
            course=other_course,
            dept_s=other_department,
            title="Arts assignment",
            due_date=date(2026, 12, 2),
            posted_by=self.admin,
        )
        self.client.force_authenticate(user=self.student_user)

        response = self.client.post(
            "/portal/student/submissions/",
            {
                "assignment": assignment.pk,
                "file": SimpleUploadedFile("work.txt", b"work"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Submission.objects.exists())

    def test_unlinked_account_cannot_submit_work(self):
        Assignment.objects.create(
            course=self.course,
            dept_s=self.student.depts,
            title="Lab report",
            due_date=date(2026, 12, 1),
            posted_by=self.admin,
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/portal/student/submissions/",
            {
                "assignment": 1,
                "file": SimpleUploadedFile("report.txt", b"work"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_record_attendance(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/portal/attendance/",
            {"student": self.student.pk, "date": "2026-11-09", "status": "present"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record = Attendance.objects.get()
        self.assertEqual(record.recorded_by, self.admin)
        self.assertEqual(response.data["student_name"], self.student.full_name)

    def test_non_staff_cannot_record_or_read_attendance(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.post(
            "/portal/attendance/",
            {"student": self.student.pk, "date": "2026-11-09", "status": "present"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Attendance.objects.exists())

    def test_duplicate_attendance_for_student_and_date_is_rejected(self):
        Attendance.objects.create(
            student=self.student,
            date=date(2026, 11, 9),
            status=Attendance.Status.PRESENT,
            recorded_by=self.admin,
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/portal/attendance/",
            {"student": self.student.pk, "date": "2026-11-09", "status": "absent"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Attendance.objects.count(), 1)
