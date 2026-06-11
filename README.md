# WAD_project — TaskNest Web Application

TaskNest is a responsive task management web application built for the **Web Application Development** course assignment. It includes authentication, user roles, persistent storage, asynchronous CRUD operations, filtering, sorting, light/dark mode, Docker support, seeded test data, and automated tests.

## Main features

- User registration and login
- Password hashing with Werkzeug
- Session-based authentication
- CSRF protection for all mutating requests
- Two roles: `admin` and `user`
- User-specific task data
- Admin panel for user and role management
- CRUD operations for tasks
- Search, filtering, and sorting for tasks
- Asynchronous frontend communication with `fetch()`
- Modal-based create/edit workflow
- Light/dark theme switch with `localStorage`
- Responsive UI with Bootstrap and custom CSS
- SQLite database with automatic seed data
- Dockerized app runnable with `docker-compose up`
- Pytest tests for unit/API and end-to-end user flows

## Technology stack

- Frontend: HTML, CSS, JavaScript, Bootstrap 5
- Backend: Python, Flask
- Database: SQLite
- Tests: Pytest
- Containerization: Docker and Docker Compose

## How to run with Docker

If you downloaded the ZIP file, extract it first:

```bash
unzip WAD_project.zip
cd WAD_project
```

Then:

1. Install Docker Desktop or Docker Engine.
2. Open a terminal in the `WAD_project` folder.
3. Run:

```bash
docker-compose up --build
```

4. Open the application in your browser:

```text
http://localhost:5000
```

The database is created automatically in the Docker volume `wad_project_data`. Seed users and tasks are inserted automatically when the database is empty.

## Demo login accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@tasknest.test` | `Admin123!` |
| User | `mia@tasknest.test` | `User123!` |
| User | `leo@tasknest.test` | `User123!` |

You can also register a new regular user from the registration page.

## How to use the app

1. Log in using one of the demo accounts or create a new account.
2. On the dashboard, create a new task with the **New task** button.
3. Use the search box to search by title, description, or owner.
4. Use the status and priority dropdowns to filter tasks.
5. Use the sort and order controls to sort the task list.
6. Click **Edit** to update a task in a modal window.
7. Click **Delete** to remove a task.
8. Use the **Theme** button in the navigation bar to switch between light and dark mode.
9. Log in as admin to open the **Admin** page and manage user roles or delete user accounts.

## How data access works

- Regular users only see and manage their own tasks.
- Admin users can see all tasks and manage users.
- Deleting a user also deletes that user's tasks through a database foreign key cascade.

## Validation and security notes

The application includes:

- Client-side form validation using HTML validation attributes and JavaScript.
- Server-side validation for registration, task creation, task updates, filters, roles, and dates.
- Parameterized SQL queries to prevent SQL injection.
- Jinja escaping and safe DOM rendering with `textContent` to reduce XSS risk.
- CSRF token checks on `POST`, `PUT`, `PATCH`, and `DELETE` requests.
- Basic security headers, including `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and a Content Security Policy.
- Passwords are stored as hashes, not as plain text.

## Running locally without Docker

Use Python 3.12 or a recent Python 3 version.

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows PowerShell
pip install -r requirements.txt
flask --app app run --debug
```

Then open:

```text
http://localhost:5000
```

## Running tests

```bash
pytest
```

The tests create their own temporary SQLite database and do not modify the development database.

## Project structure

```text
.
├── app.py                    # Flask app, routes, API, database setup, seed data
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile                # Docker image definition
├── requirements.txt          # Python dependencies
├── templates/                # Jinja HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── admin.html
├── static/
│   ├── css/styles.css        # Custom responsive styles and theme variables
│   └── js/
│       ├── common.js         # Theme toggle, CSRF helper, API helper
│       ├── dashboard.js      # Async task CRUD, filtering, sorting
│       └── admin.js          # Async user management
├── tests/test_app.py         # Unit/API/end-to-end tests
└── data/                     # SQLite database location at runtime
```

## Git repository instructions

The assignment requires development using a Git server. To publish this project:

```bash
cd WAD_project
git init
git add .
git commit -m "Initial commit - WAD_project"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

If your repository is private, give your teacher access to it.

## Requirement checklist

### Level C

- Desktop and mobile usable UI: yes
- CRUD operations: yes, tasks can be created, read, updated, and deleted
- Persistent storage: yes, SQLite database
- Login-only section: yes, dashboard and API require login
- Input validation on client and server: yes
- Protection against SQL injection and XSS: yes, parameterized SQL and safe rendering

### Level B

- CSS framework: yes, Bootstrap 5
- Docker: yes, Dockerfile and docker-compose.yml
- User-specific data: yes, regular users see only their own tasks
- At least two roles: yes, admin and user
- Filtering/searching/sorting: yes

### Level A

- Responsive design: yes, Bootstrap grid and custom responsive CSS
- Light/dark theme: yes
- Thoughtful UI/UX: yes, dashboard, modal editing, stats, admin panel
- Docker with automatic test data import: yes, seed data is inserted automatically on empty database
- Asynchronous communication: yes, `fetch()` API calls without full page reloads
- In-place/modal editing: yes, task creation and editing are done in a Bootstrap modal
- Tests: yes, Pytest tests cover API and end-to-end workflows
- Filtering/searching/sorting all task data: yes
