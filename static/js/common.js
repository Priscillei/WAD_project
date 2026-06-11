(function () {
    'use strict';

    function csrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : '';
    }

    function setTheme(theme) {
        const normalized = theme === 'dark' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-bs-theme', normalized);
        localStorage.setItem('tasknest-theme', normalized);
        const button = document.getElementById('themeToggle');
        if (button) {
            button.textContent = normalized === 'dark' ? '☀️ Theme' : '🌙 Theme';
        }
    }

    async function apiFetch(url, options) {
        const opts = options || {};
        const headers = new Headers(opts.headers || {});
        if (!headers.has('Content-Type') && opts.body) {
            headers.set('Content-Type', 'application/json');
        }
        headers.set('X-CSRFToken', csrfToken());
        const response = await fetch(url, Object.assign({}, opts, { headers }));
        let payload = {};
        try {
            payload = await response.json();
        } catch (error) {
            payload = {};
        }
        if (!response.ok) {
            const message = payload.error || (payload.errors ? payload.errors.join(' ') : 'Request failed.');
            throw new Error(message);
        }
        return payload;
    }

    function enableBootstrapValidation(form) {
        if (!form) return;
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        setTheme(localStorage.getItem('tasknest-theme') || 'light');
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', function () {
                const current = document.documentElement.getAttribute('data-bs-theme');
                setTheme(current === 'dark' ? 'light' : 'dark');
            });
        }
        enableBootstrapValidation(document.getElementById('loginForm'));
        enableBootstrapValidation(document.getElementById('registerForm'));
    });

    window.TaskNest = {
        apiFetch: apiFetch,
        csrfToken: csrfToken
    };
})();
