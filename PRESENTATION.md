# TaskNest presentation plan, 10–15 minutes

## 1. Introduction, 1 minute

TaskNest is a personal task management web application. The goal is to help users organize tasks, filter and sort them, and manage their work through a responsive web interface. The project was created for the Web Application Development course and targets the Level A requirements.

## 2. Technologies, 1 minute

The frontend uses HTML, CSS, JavaScript, and Bootstrap. The backend uses Flask in Python. Data is stored in SQLite. The app is containerized with Docker and Docker Compose. Automated tests are written with Pytest.

## 3. User-side demo, 4–5 minutes

1. Open `http://localhost:5000`.
2. Show the login page and demo accounts.
3. Log in as `mia@tasknest.test` with password `User123!`.
4. Show the dashboard and existing tasks.
5. Create a new task using the modal.
6. Edit the task in the modal and save it.
7. Search for the task.
8. Filter by status and priority.
9. Sort by due date or title.
10. Delete the task.
11. Switch between light and dark theme.
12. Log out.

## 4. Admin-side demo, 2–3 minutes

1. Log in as `admin@tasknest.test` with password `Admin123!`.
2. Explain that the admin can see tasks from all users.
3. Open the Admin page.
4. Show the user list with roles and task counts.
5. Demonstrate changing a user's role.
6. Explain that deleting a user also deletes their tasks because of database cascade rules.

## 5. Technical explanation, 3–4 minutes

- Flask routes render the main pages.
- API routes under `/api/tasks` and `/api/users` return JSON.
- JavaScript uses `fetch()` to create, read, update, and delete data without reloading the page.
- SQLite stores users and tasks persistently.
- The database is initialized automatically when the app starts.
- Seed users and sample tasks are inserted if the database is empty.
- Regular users can only access their own tasks.
- Admin users can access all tasks and manage users.

## 6. Security and validation, 1–2 minutes

- Passwords are hashed using Werkzeug.
- SQL queries use parameterized statements to prevent SQL injection.
- CSRF tokens protect mutating requests.
- User-generated text is rendered safely with Jinja escaping or JavaScript `textContent`.
- Both client-side and server-side validation are implemented.
- Basic security headers are added to responses.

## 7. Tests and Docker, 1 minute

Show how to run:

```bash
docker-compose up --build
```

Then explain that tests can be run with:

```bash
pytest
```

The tests cover login, seeded data, CRUD operations, validation, role permissions, admin actions, and a full register-login-create-update-delete user flow.

## 8. Conclusion, 30 seconds

TaskNest fulfills the assignment requirements for Level A: responsive design, roles, persistent storage, Docker, automatic seed data, asynchronous communication, modal editing, filtering, sorting, dark mode, and tests.
