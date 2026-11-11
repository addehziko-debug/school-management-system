(() => {
    const storageKey = "campusPortalTheme";
    const root = document.documentElement;
    const toggles = document.querySelectorAll("[data-theme-toggle]");

    const applyTheme = (theme) => {
        const isDark = theme === "dark";
        root.dataset.theme = isDark ? "dark" : "light";
        toggles.forEach((toggle) => {
            toggle.textContent = isDark ? "Light mode" : "Dark mode";
            toggle.setAttribute("aria-pressed", String(isDark));
        });
    };

    let theme = "light";
    try {
        theme = localStorage.getItem(storageKey) === "dark" ? "dark" : "light";
    } catch (error) {
        console.warn("Could not load the saved color theme.", error);
    }
    applyTheme(theme);

    toggles.forEach((toggle) => {
        toggle.addEventListener("click", () => {
            theme = root.dataset.theme === "dark" ? "light" : "dark";
            applyTheme(theme);
            try {
                localStorage.setItem(storageKey, theme);
            } catch (error) {
                console.warn("Could not save the selected color theme.", error);
            }
        });
    });
})();
