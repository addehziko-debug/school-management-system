(() => {
    const api = {
        assignments: "/portal/assignments/",
        attendance: "/portal/attendance/",
        courses: "/portal/Courses/",
        departments: "/portal/Depts/",
        flyers: "/portal/flyers/",
        homepageBackground: "/portal/homepage-background/",
        students: "/portal/Students/",
        login: "/auth/login/",
        currentUser: "/auth/me/",
        logout: "/auth/logout/",
        staffSubmissions: "/portal/staff/submissions/",
    };
    const tokenKey = "campusPortalToken";
    let token = sessionStorage.getItem(tokenKey);

    const elements = {
        assignmentList: document.querySelector("#assignment-list"),
        homepageFlyers: document.querySelector("#homepage-flyers"),
        homepageFlyerList: document.querySelector("#homepage-flyer-list"),
        assignmentCount: document.querySelector("#assignment-count"),
        courseCount: document.querySelector("#course-count"),
        studentCount: document.querySelector("#student-count"),
        assignmentCourse: document.querySelector("#assignment-course"),
        assignmentDepartment: document.querySelector("#assignment-department"),
        courseDepartment: document.querySelector("#course-department"),
        attendanceStudent: document.querySelector("#attendance-student"),
        attendanceList: document.querySelector("#attendance-list"),
        attendanceCount: document.querySelector("#attendance-record-count"),
        attendanceDate: document.querySelector("#attendance-date"),
        sessionLabel: document.querySelector("#session-label"),
        logoutButton: document.querySelector("#logout-button"),
        catalog: document.querySelector("#catalog"),
        catalogNavLink: document.querySelector("#catalog-nav-link"),
        removeHomepageBackground: document.querySelector("#remove-homepage-background"),
    };
    let isSuperuser = false;
    let isStaff = false;
    let hasHomepageBackground = Boolean(document.querySelector(".site-background img"));
    let assignments = [];
    let staffSubmissions = [];
    let staffRefreshTimer = null;

    const readResponse = async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const detail = data.detail || Object.values(data).flat().join(" ");
            throw new Error(detail || `Request failed (${response.status}).`);
        }
        return data;
    };

    const request = async (url, options = {}) => {
        const headers = new Headers(options.headers || {});
        if (token) headers.set("Authorization", `Token ${token}`);
        const response = await fetch(url, { ...options, headers });
        return readResponse(response);
    };

    const showMessage = (element, text, kind = "") => {
        element.textContent = text;
        element.className = `form-message ${kind}`.trim();
    };

    const make = (tag, className, text) => {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    };

    const renderAssignments = (assignments) => {
        elements.assignmentList.replaceChildren();
        elements.assignmentCount.textContent = assignments.length;
        if (!assignments.length) {
            elements.assignmentList.append(make("div", "empty-card", "No assignments have been posted yet."));
            return;
        }

        assignments.forEach((assignment) => {
            const card = make("article", "assignment-card");
            const meta = make("div", "assignment-meta");
            meta.append(
                make(
                    "span",
                    "course-pill",
                    `${assignment.course_name || `Course #${assignment.course}`} · ${assignment.department_name}`,
                ),
                make("span", "due-date", `Due ${assignment.due_date}`),
            );
            card.append(meta, make("h3", "", assignment.title));
            if (assignment.description) card.append(make("p", "", assignment.description));

            const footer = make("div", "assignment-footer");
            footer.append(make("span", "", `Posted by ${assignment.posted_by_name || "staff"}`));
            if (assignment.attachment) {
                const link = make("a", "file-link", "Download file");
                link.href = assignment.attachment;
                link.target = "_blank";
                link.rel = "noopener noreferrer";
                footer.append(link);
            } else {
                footer.append(make("span", "", "Course assignment"));
            }
            card.append(footer);

            if (isStaff) {
                const submissions = staffSubmissions.filter(
                    (submission) => Number(submission.assignment) === Number(assignment.id),
                );
                const submissionSection = make("section", "assignment-submissions");
                submissionSection.append(
                    make("h4", "", `Student submissions (${submissions.length})`),
                );
                if (!submissions.length) {
                    submissionSection.append(make("p", "empty-submissions", "No student submissions yet."));
                } else {
                    const submissionList = make("div", "staff-submission-list");
                    submissions.forEach((submission) => {
                        const row = make("article", "staff-submission-row");
                        const details = make("div", "staff-submission-details");
                        details.append(
                            make("strong", "", submission.student_name),
                            make("time", "", new Date(submission.submitted_at).toLocaleString()),
                        );
                        if (submission.comment) {
                            details.append(make("p", "staff-submission-comment", submission.comment));
                        }
                        const actions = make("div", "staff-submission-actions");
                        const downloadMessage = make("span", "form-message");
                        const download = make("button", "button button-quiet", "Download");
                        download.type = "button";
                        download.addEventListener("click", async () => {
                            download.disabled = true;
                            try {
                                const response = await fetch(submission.download_url, {
                                    headers: { Authorization: `Token ${token}` },
                                });
                                if (!response.ok) {
                                    const data = await response.json().catch(() => ({}));
                                    throw new Error(data.detail || "Could not download this submission.");
                                }
                                const blob = await response.blob();
                                const url = URL.createObjectURL(blob);
                                const link = document.createElement("a");
                                link.href = url;
                                link.download = submission.file_name;
                                document.body.append(link);
                                link.click();
                                link.remove();
                                window.setTimeout(() => URL.revokeObjectURL(url), 1000);
                            } catch (error) {
                                showMessage(downloadMessage, error.message, "error");
                            } finally {
                                download.disabled = false;
                            }
                        });
                        actions.append(
                            make("span", "staff-submission-file", submission.file_name),
                            download,
                        );
                        row.append(details, actions, downloadMessage);
                        submissionList.append(row);
                    });
                    submissionSection.append(submissionList);
                }
                card.append(submissionSection);
            }
            elements.assignmentList.append(card);
        });
    };

    const renderFlyers = (flyers) => {
        elements.homepageFlyerList.replaceChildren();
        elements.homepageFlyers.hidden = flyers.length === 0;
        flyers.forEach((flyer) => {
            const card = make("article", "flyer-card");
            const content = make("div", "flyer-card-content");
            const image = make("img", "", "");
            image.src = flyer.image;
            image.alt = flyer.title;
            image.loading = "lazy";
            card.append(image);
            content.append(make("h3", "", flyer.title));
            if (flyer.caption) content.append(make("p", "", flyer.caption));
            const actions = make("div", "flyer-actions");
            if (flyer.link) {
                const link = make("a", "file-link", "Learn more");
                link.href = flyer.link;
                link.target = "_blank";
                link.rel = "noopener noreferrer";
                actions.append(link);
            }
            if (isSuperuser) {
                const remove = make("button", "button button-quiet", "Remove flyer");
                remove.type = "button";
                remove.addEventListener("click", async () => {
                    remove.disabled = true;
                    try {
                        await request(`${api.flyers}${flyer.id}/`, { method: "DELETE" });
                        await loadFlyers();
                    } catch (error) {
                        remove.disabled = false;
                        showMessage(elements.sessionLabel, error.message, "error");
                    }
                });
                actions.append(remove);
            }
            content.append(actions);
            card.append(content);
            elements.homepageFlyerList.append(card);
        });
    };

    const fillSelect = (select, items, labelFor, placeholder) => {
        select.replaceChildren(new Option(placeholder, ""));
        items.forEach((item) => select.add(new Option(labelFor(item), item.id)));
    };

    const loadAssignments = async () => {
        assignments = await request(api.assignments);
        renderAssignments(assignments);
    };

    const loadStaffSubmissions = async () => {
        staffSubmissions = await request(api.staffSubmissions);
        renderAssignments(assignments);
    };

    const refreshStaffAssignments = async () => {
        await Promise.all([loadAssignments(), loadStaffSubmissions()]);
    };

    const loadCourses = async () => {
        const courses = await request(api.courses);
        elements.courseCount.textContent = courses.length;
        fillSelect(
            elements.assignmentCourse,
            courses,
            (course) => course.course_name,
            courses.length ? "Choose a course" : "No courses available",
        );
    };

    const loadDepartments = async () => {
        const departments = await request(api.departments);
        fillSelect(
            elements.assignmentDepartment,
            departments,
            (department) => department.name,
            departments.length ? "Choose a department" : "No departments available",
        );
        fillSelect(
            elements.courseDepartment,
            departments,
            (department) => department.name,
            departments.length ? "Choose a department" : "Add a department first",
        );
    };

    const loadFlyers = async () => {
        const flyers = await request(api.flyers);
        renderFlyers(flyers);
    };

    const renderHomepageBackground = (url) => {
        let container = document.querySelector(".site-background");
        if (!url) {
            container?.remove();
            hasHomepageBackground = false;
            syncSession();
            return;
        }
        if (!container) {
            container = make("div", "site-background");
            container.setAttribute("aria-hidden", "true");
            document.body.prepend(container);
        }
        let image = container.querySelector("img");
        if (!image) {
            image = document.createElement("img");
            image.alt = "";
            container.append(image);
        }
        image.src = url;
        hasHomepageBackground = true;
        syncSession();
    };

    const loadHomepageBackground = async () => {
        const background = await request(api.homepageBackground);
        renderHomepageBackground(background.image);
    };

    const loadStudents = async () => {
        const students = await request(api.students);
        elements.studentCount.textContent = students.length;
        fillSelect(
            elements.attendanceStudent,
            students,
            (student) => student.full_name,
            students.length ? "Choose a student" : "No students available",
        );
    };

    const loadAttendance = async () => {
        if (!token) {
            elements.attendanceCount.textContent = "Sign in to view";
            elements.attendanceList.replaceChildren(
                make("div", "empty-card", "Sign in with a staff account to view attendance records."),
            );
            return;
        }

        try {
            const records = await request(api.attendance);
            elements.attendanceCount.textContent = `${records.length} record${records.length === 1 ? "" : "s"}`;
            elements.attendanceList.replaceChildren();
            if (!records.length) {
                elements.attendanceList.append(make("div", "empty-card", "No attendance has been recorded yet."));
                return;
            }
            records.slice(0, 8).forEach((record) => {
                const row = make("div", "attendance-row");
                row.append(
                    make("span", "attendance-student", record.student_name || `Student #${record.student}`),
                    make("time", "", record.date),
                    make("span", `status-badge ${record.status}`, record.status),
                );
                elements.attendanceList.append(row);
            });
        } catch (error) {
            elements.attendanceCount.textContent = "Staff access required";
            elements.attendanceList.replaceChildren(make("div", "empty-card", error.message));
        }
    };

    const syncSession = () => {
        elements.sessionLabel.textContent = token ? "Signed in" : "Guest session";
        elements.logoutButton.hidden = !token;
        document.querySelector("#login").hidden = Boolean(token);
        document.querySelector("#attendance").classList.toggle("staff-session", Boolean(token));
        elements.catalog.hidden = !isSuperuser;
        elements.catalogNavLink.hidden = !isSuperuser;
        elements.removeHomepageBackground.hidden = !isSuperuser || !hasHomepageBackground;
        document.querySelector("#staff-submission-hint").hidden = !isStaff;
    };

    const loadCurrentUser = async () => {
        const user = token ? await request(api.currentUser) : {};
        isSuperuser = Boolean(user.is_superuser);
        isStaff = Boolean(user.is_staff);
        syncSession();
        await loadHomepageBackground();
        await loadFlyers();
        if (isStaff) {
            await refreshStaffAssignments();
            if (!staffRefreshTimer) {
                staffRefreshTimer = window.setInterval(() => {
                    refreshStaffAssignments().catch((error) => console.error(error));
                }, 30000);
            }
        } else {
            staffSubmissions = [];
            renderAssignments(assignments);
        }
    };

    document.querySelectorAll("[data-toggle='assignment-form']").forEach((button) => {
        button.addEventListener("click", () => {
            const panel = document.querySelector("#assignment-form-panel");
            panel.hidden = !panel.hidden;
            if (!panel.hidden) panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
        });
    });

    document.querySelector("#login-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const message = document.querySelector("#login-message");
        const values = Object.fromEntries(new FormData(form));
        try {
            const result = await request(api.login, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(values),
            });
            token = result.token;
            sessionStorage.setItem(tokenKey, token);
            await loadCurrentUser();
            form.reset();
            showMessage(
                message,
                isSuperuser
                    ? "Signed in as a superuser. Department and course management is available."
                    : "Signed in. Staff-only actions are checked by the server.",
                "success",
            );
            await loadAttendance();
        } catch (error) {
            showMessage(message, error.message, "error");
        }
    });

    elements.logoutButton.addEventListener("click", async () => {
        try {
            await request(api.logout, { method: "POST" });
            token = null;
            isSuperuser = false;
            isStaff = false;
            staffSubmissions = [];
            if (staffRefreshTimer) {
                window.clearInterval(staffRefreshTimer);
                staffRefreshTimer = null;
            }
            sessionStorage.removeItem(tokenKey);
            syncSession();
            renderAssignments(assignments);
            await loadFlyers();
            await loadAttendance();
        } catch (error) {
            elements.sessionLabel.textContent = error.message;
        }
    });

    document.querySelector("#assignment-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const message = document.querySelector("#assignment-message");
        try {
            await request(api.assignments, { method: "POST", body: new FormData(form) });
            form.reset();
            showMessage(message, "Assignment posted successfully.", "success");
            await loadAssignments();
        } catch (error) {
            showMessage(message, error.message, "error");
        }
    });

    document.querySelector("#attendance-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const message = document.querySelector("#attendance-message");
        const values = Object.fromEntries(new FormData(form));
        try {
            await request(api.attendance, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(values),
            });
            showMessage(message, "Attendance saved.", "success");
            await loadAttendance();
        } catch (error) {
            showMessage(message, error.message, "error");
        }
    });

    document.querySelector("#department-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const message = document.querySelector("#department-message");
        const values = Object.fromEntries(new FormData(form));
        try {
            await request(api.departments, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ...values, date: values.date || null }),
            });
            form.reset();
            showMessage(message, "Department added.", "success");
            await Promise.all([loadDepartments(), loadCourses()]);
        } catch (error) {
            showMessage(message, error.message, "error");
        }
    });

    document.querySelector("#course-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const message = document.querySelector("#course-message");
        const values = Object.fromEntries(new FormData(form));
        try {
            await request(api.courses, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ...values, dept: Number(values.dept) }),
            });
            form.reset();
            showMessage(message, "Course added to the selected department.", "success");
            await loadCourses();
        } catch (error) {
            showMessage(message, error.message, "error");
        }
    });

    document.querySelector("#flyer-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const message = document.querySelector("#flyer-message");
        try {
            await request(api.flyers, { method: "POST", body: new FormData(form) });
            form.reset();
            showMessage(message, "Flyer published on the homepage.", "success");
            await loadFlyers();
        } catch (error) {
            showMessage(message, error.message, "error");
        }
    });

    document.querySelector("#homepage-background-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const message = document.querySelector("#homepage-background-message");
        try {
            const background = await request(api.homepageBackground, {
                method: "POST",
                body: new FormData(form),
            });
            renderHomepageBackground(background.image);
            form.reset();
            showMessage(message, "Homepage background saved.", "success");
        } catch (error) {
            showMessage(message, error.message, "error");
        }
    });

    elements.removeHomepageBackground.addEventListener("click", async () => {
        const message = document.querySelector("#homepage-background-message");
        try {
            await request(api.homepageBackground, { method: "DELETE" });
            renderHomepageBackground(null);
            showMessage(message, "Homepage background removed.", "success");
        } catch (error) {
            showMessage(message, error.message, "error");
        }
    });

    const today = new Date();
    today.setMinutes(today.getMinutes() - today.getTimezoneOffset());
    elements.attendanceDate.value = today.toISOString().slice(0, 10);
    syncSession();
    Promise.allSettled([
        loadAssignments(),
        loadCourses(),
        loadDepartments(),
        loadStudents(),
        loadFlyers(),
        loadHomepageBackground(),
    ]).then((results) => {
        results.forEach((result) => {
            if (result.status === "rejected") console.error(result.reason);
        });
    });
    if (token) {
        loadCurrentUser().catch((error) => {
            isSuperuser = false;
            isStaff = false;
            syncSession();
            elements.sessionLabel.textContent = error.message;
        });
    }
    loadAttendance();
})();
