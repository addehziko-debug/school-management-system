(() => {
    const api = {
        assignments: "/portal/student/assignments/",
        departments: "/portal/Depts/",
        profile: "/portal/student/profile/",
        submissions: "/portal/student/submissions/",
        login: "/auth/login/",
        signup: "/auth/create/",
        logout: "/auth/logout/",
    };
    const tokenKey = "campusPortalToken";
    let token = sessionStorage.getItem(tokenKey);

    const elements = {
        authSection: document.querySelector("#auth-section"),
        dashboard: document.querySelector("#student-dashboard"),
        logout: document.querySelector("#logout-button"),
        sessionName: document.querySelector("#session-name"),
        assignments: document.querySelector("#student-assignment-list"),
        submissions: document.querySelector("#student-submission-list"),
    };

    const parseResponse = async (response) => {
        const contentType = response.headers.get("content-type") || "";
        const data = contentType.includes("application/json") ? await response.json() : {};
        if (!response.ok) {
            const detail = data.detail || Object.values(data).flat().join(" ");
            throw new Error(detail || `Request failed (${response.status}).`);
        }
        return data;
    };

    const request = async (url, options = {}) => {
        const headers = new Headers(options.headers || {});
        if (token) headers.set("Authorization", `Token ${token}`);
        return parseResponse(await fetch(url, { ...options, headers }));
    };

    const element = (tag, className, text) => {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    };

    const message = (id, text, kind = "") => {
        const node = document.querySelector(id);
        node.textContent = text;
        node.className = `form-message ${kind}`.trim();
    };

    const toggleSession = (signedIn) => {
        elements.authSection.hidden = signedIn;
        elements.dashboard.hidden = !signedIn;
        elements.logout.hidden = !signedIn;
        elements.sessionName.textContent = signedIn ? "Signed in" : "Student space";
    };

    const loadDepartments = async () => {
        const departments = await request(api.departments);
        const select = document.querySelector("#signup-department");
        select.replaceChildren(new Option(
            departments.length ? "Choose your department" : "No departments available",
            "",
        ));
        departments.forEach((department) => {
            select.add(new Option(department.name, department.id));
        });
    };

    const loadProfile = async () => {
        const profile = await request(api.profile);
        const form = document.querySelector("#profile-form");
        form.elements.full_name.value = profile.full_name;
        form.elements.age.value = profile.age;
        document.querySelector("#profile-department").value = profile.department_name;
        document.querySelector("#student-first-name").textContent = profile.full_name.split(/\s+/)[0];
    };

    const renderAssignments = (assignments) => {
        elements.assignments.replaceChildren();
        if (!assignments.length) {
            elements.assignments.append(element("div", "empty-state", "No assignments have been posted yet."));
            return;
        }

        assignments.forEach((assignment) => {
            const card = element("article", "student-assignment");
            const titleRow = element("div", "assignment-title-row");
            const titleGroup = document.createElement("div");
            titleGroup.append(
                element("h4", "", assignment.title),
                element("span", "course-name", `${assignment.course_name} · ${assignment.department_name}`),
            );
            titleRow.append(titleGroup, element("span", "due-label", `Due ${assignment.due_date}`));
            card.append(titleRow);
            if (assignment.description) card.append(element("p", "", assignment.description));
            if (assignment.attachment) {
                const attachment = element("a", "assignment-resource", "Download instructions →");
                attachment.href = assignment.attachment;
                attachment.target = "_blank";
                attachment.rel = "noopener noreferrer";
                card.append(attachment);
            }

            const form = element("form", "submission-form");
            form.enctype = "multipart/form-data";
            const file = document.createElement("input");
            file.type = "file";
            file.name = "file";
            file.required = true;
            file.setAttribute("aria-label", `Submission file for ${assignment.title}`);
            const submit = element("button", "button button-primary", "Submit");
            submit.type = "submit";
            const comment = document.createElement("input");
            comment.className = "submission-comment";
            comment.name = "comment";
            comment.maxLength = 2000;
            comment.placeholder = "Optional note for your teacher";
            comment.setAttribute("aria-label", `Optional comment for ${assignment.title}`);
            const status = element("span", "form-message");
            status.setAttribute("role", "status");
            status.classList.add("submission-status");
            form.append(file, submit, comment, status);
            form.addEventListener("submit", async (event) => {
                event.preventDefault();
                const data = new FormData(form);
                data.append("assignment", assignment.id);
                submit.disabled = true;
                try {
                    await request(api.submissions, { method: "POST", body: data });
                    form.reset();
                    status.textContent = "Submitted successfully.";
                    status.className = "form-message success submission-status";
                    await loadSubmissions();
                } catch (error) {
                    status.textContent = error.message;
                    status.className = "form-message error submission-status";
                } finally {
                    submit.disabled = false;
                }
            });
            card.append(form);
            elements.assignments.append(card);
        });
    };

    const downloadSubmission = async (submission) => {
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
    };

    const loadSubmissions = async () => {
        const submissions = await request(api.submissions);
        elements.submissions.replaceChildren();
        if (!submissions.length) {
            elements.submissions.append(element("div", "empty-state", "Your submitted work will appear here."));
            return;
        }

        submissions.forEach((submission) => {
            const row = element("div", "student-submission");
            const info = document.createElement("div");
            info.append(
                element("strong", "", submission.assignment_title),
                element("span", "", `${submission.course_name} · ${new Date(submission.submitted_at).toLocaleString()}`),
            );
            const download = element("button", "", "Download");
            download.type = "button";
            download.className = "submission-download";
            download.addEventListener("click", async () => {
                download.disabled = true;
                try {
                    await downloadSubmission(submission);
                    message("#submission-message", "Submission downloaded.", "success");
                } catch (error) {
                    message("#submission-message", error.message, "error");
                } finally {
                    download.disabled = false;
                }
            });
            row.append(info, download);
            elements.submissions.append(row);
        });
    };

    const loadDashboard = async () => {
        await loadProfile();
        const [assignmentsResult, submissionsResult] = await Promise.allSettled([
            request(api.assignments),
            loadSubmissions(),
        ]);
        if (assignmentsResult.status === "fulfilled") {
            renderAssignments(assignmentsResult.value);
        } else {
            elements.assignments.replaceChildren(element("div", "empty-state", assignmentsResult.reason.message));
        }
        if (submissionsResult.status === "rejected") {
            elements.submissions.replaceChildren(element("div", "empty-state", submissionsResult.reason.message));
        }
    };

    document.querySelectorAll("[data-auth-tab]").forEach((tab) => {
        tab.addEventListener("click", () => {
            const showSignup = tab.dataset.authTab === "signup";
            document.querySelector("#login-form").hidden = showSignup;
            document.querySelector("#signup-form").hidden = !showSignup;
            document.querySelectorAll("[data-auth-tab]").forEach((item) => {
                const active = item === tab;
                item.classList.toggle("active", active);
                item.setAttribute("aria-selected", String(active));
            });
        });
    });

    document.querySelector("#login-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const values = Object.fromEntries(new FormData(event.currentTarget));
        try {
            const result = await request(api.login, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(values),
            });
            token = result.token;
            sessionStorage.setItem(tokenKey, token);
            toggleSession(true);
            await loadDashboard();
        } catch (error) {
            message("#login-message", error.message, "error");
        }
    });

    document.querySelector("#signup-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const values = Object.fromEntries(new FormData(event.currentTarget));
        try {
            const result = await request(api.signup, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(values),
            });
            token = result.token;
            sessionStorage.setItem(tokenKey, token);
            toggleSession(true);
            await loadDashboard();
        } catch (error) {
            message("#signup-message", error.message, "error");
        }
    });

    document.querySelector("#profile-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const values = {
            full_name: form.elements.full_name.value,
            age: Number(form.elements.age.value),
        };
        try {
            await request(api.profile, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(values),
            });
            message("#profile-message", "Profile updated.", "success");
            await loadProfile();
        } catch (error) {
            message("#profile-message", error.message, "error");
        }
    });

    elements.logout.addEventListener("click", async () => {
        try {
            await request(api.logout, { method: "POST" });
        } catch (error) {
            message("#submission-message", error.message, "error");
        } finally {
            token = null;
            sessionStorage.removeItem(tokenKey);
            toggleSession(false);
        }
    });

    loadDepartments().catch((error) => {
        const select = document.querySelector("#signup-department");
        select.replaceChildren(new Option(error.message, ""));
    });

    if (token) {
        toggleSession(true);
        loadDashboard().catch((error) => {
            token = null;
            sessionStorage.removeItem(tokenKey);
            toggleSession(false);
            message("#login-message", error.message, "error");
        });
    } else {
        toggleSession(false);
    }
})();
