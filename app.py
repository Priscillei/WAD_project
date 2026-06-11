import hmac
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_STATUSES = {"todo", "in_progress", "done"}
VALID_PRIORITIES = {"low", "medium", "high"}
TASK_SORT_COLUMNS = {
    "title": "t.title",
    "status": "t.status",
    "priority": "t.priority",
    "due_date": "t.due_date",
    "created_at": "t.created_at",
    "updated_at": "t.updated_at",
    "owner": "u.name",
}


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-this-secret-key"),
        DATABASE=os.environ.get("DATABASE_PATH", str(Path(__file__).parent / "data" / "wad_project.db")),
        TESTING=False,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    @app.before_request
    def load_logged_in_user_and_check_csrf():
        user_id = session.get("user_id")
        g.user = get_user(user_id) if user_id else None

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            expected = session.get("csrf_token")
            sent = request.headers.get("X-CSRFToken") or request.form.get("csrf_token")
            if not expected or not sent or not hmac.compare_digest(expected, sent):
                abort(400, description="Invalid CSRF token")

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' https://cdn.jsdelivr.net; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; img-src 'self' data:; font-src 'self' https://cdn.jsdelivr.net"
        )
        return response

    @app.context_processor
    def inject_globals():
        return {"csrf_token": get_csrf_token(), "current_year": datetime.now(timezone.utc).year}

    @app.route("/")
    def index():
        return redirect(url_for("dashboard" if g.user else "login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if g.user:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            errors = validate_registration(name, email, password)
            db = get_db()
            if not errors and db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
                errors.append("This email is already registered.")
            if errors:
                for error in errors:
                    flash(error, "danger")
                return render_template("register.html", name=name, email=email), 400
            db.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'user')",
                (name, email, generate_password_hash(password)),
            )
            db.commit()
            flash("Account created. You can log in now.", "success")
            return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if user is None or not check_password_hash(user["password_hash"], password):
                flash("Invalid email or password.", "danger")
                return render_template("login.html", email=email), 401
            session.clear()
            session["user_id"] = user["id"]
            session["csrf_token"] = secrets.token_urlsafe(32)
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/admin")
    @admin_required
    def admin_panel():
        return render_template("admin.html")

    @app.route("/api/me")
    @login_required
    def api_me():
        return jsonify({"user": public_user(g.user)})

    @app.route("/api/tasks", methods=["GET"])
    @login_required
    def api_list_tasks():
        search = request.args.get("search", "").strip()
        status = request.args.get("status", "").strip()
        priority = request.args.get("priority", "").strip()
        sort = request.args.get("sort", "updated_at")
        order = request.args.get("order", "desc").lower()

        if status and status not in VALID_STATUSES:
            return jsonify({"error": "Invalid status filter."}), 400
        if priority and priority not in VALID_PRIORITIES:
            return jsonify({"error": "Invalid priority filter."}), 400
        sort_sql = TASK_SORT_COLUMNS.get(sort, "t.updated_at")
        order_sql = "ASC" if order == "asc" else "DESC"

        where = []
        params = []
        if g.user["role"] != "admin":
            where.append("t.user_id = ?")
            params.append(g.user["id"])
        if search:
            where.append("(t.title LIKE ? OR t.description LIKE ? OR u.name LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like, like])
        if status:
            where.append("t.status = ?")
            params.append(status)
        if priority:
            where.append("t.priority = ?")
            params.append(priority)

        where_sql = "WHERE " + " AND ".join(where) if where else ""
        rows = get_db().execute(
            f"""
            SELECT t.*, u.name AS owner_name, u.email AS owner_email
            FROM tasks t
            JOIN users u ON u.id = t.user_id
            {where_sql}
            ORDER BY {sort_sql} {order_sql}, t.id DESC
            """,
            params,
        ).fetchall()
        return jsonify({"tasks": [dict(row) for row in rows]})

    @app.route("/api/tasks", methods=["POST"])
    @login_required
    def api_create_task():
        data = request.get_json(silent=True) or {}
        values, errors = validate_task_payload(data)
        if errors:
            return jsonify({"errors": errors}), 400
        now = utc_now()
        cursor = get_db().execute(
            """
            INSERT INTO tasks (user_id, title, description, status, priority, due_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                g.user["id"],
                values["title"],
                values["description"],
                values["status"],
                values["priority"],
                values["due_date"],
                now,
                now,
            ),
        )
        get_db().commit()
        task = get_task_for_response(cursor.lastrowid)
        return jsonify({"task": task}), 201

    @app.route("/api/tasks/<int:task_id>", methods=["PUT"])
    @login_required
    def api_update_task(task_id):
        task = find_task_if_allowed(task_id)
        if task is None:
            return jsonify({"error": "Task not found."}), 404
        data = request.get_json(silent=True) or {}
        values, errors = validate_task_payload(data)
        if errors:
            return jsonify({"errors": errors}), 400
        get_db().execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, status = ?, priority = ?, due_date = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                values["title"],
                values["description"],
                values["status"],
                values["priority"],
                values["due_date"],
                utc_now(),
                task_id,
            ),
        )
        get_db().commit()
        return jsonify({"task": get_task_for_response(task_id)})

    @app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
    @login_required
    def api_delete_task(task_id):
        task = find_task_if_allowed(task_id)
        if task is None:
            return jsonify({"error": "Task not found."}), 404
        get_db().execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        get_db().commit()
        return jsonify({"deleted": True})

    @app.route("/api/users", methods=["GET"])
    @admin_required
    def api_users():
        users = get_db().execute(
            """
            SELECT u.id, u.name, u.email, u.role, u.created_at, COUNT(t.id) AS task_count
            FROM users u
            LEFT JOIN tasks t ON t.user_id = u.id
            GROUP BY u.id
            ORDER BY u.created_at DESC
            """
        ).fetchall()
        return jsonify({"users": [dict(row) for row in users]})

    @app.route("/api/users/<int:user_id>", methods=["PATCH"])
    @admin_required
    def api_update_user(user_id):
        data = request.get_json(silent=True) or {}
        role = data.get("role")
        if role not in {"admin", "user"}:
            return jsonify({"error": "Role must be admin or user."}), 400
        user = get_user(user_id)
        if user is None:
            return jsonify({"error": "User not found."}), 404
        get_db().execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        get_db().commit()
        return jsonify({"user": public_user(get_user(user_id))})

    @app.route("/api/users/<int:user_id>", methods=["DELETE"])
    @admin_required
    def api_delete_user(user_id):
        if user_id == g.user["id"]:
            return jsonify({"error": "You cannot delete your own account."}), 400
        user = get_user(user_id)
        if user is None:
            return jsonify({"error": "User not found."}), 404
        get_db().execute("DELETE FROM users WHERE id = ?", (user_id,))
        get_db().commit()
        return jsonify({"deleted": True})

    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    return app


def get_db():
    if "db" not in g:
        db_path = current_app_config("DATABASE")
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def current_app_config(key):
    from flask import current_app

    return current_app.config[key]


def close_db(_=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL CHECK(length(name) BETWEEN 2 AND 80),
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL CHECK(length(title) BETWEEN 3 AND 120),
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL CHECK(status IN ('todo', 'in_progress', 'done')),
            priority TEXT NOT NULL CHECK(priority IN ('low', 'medium', 'high')),
            due_date TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    if db.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"] == 0:
        seed_database(db)
    db.commit()


def seed_database(db):
    now = utc_now()
    users = [
        ("Admin Demo", "admin@tasknest.test", generate_password_hash("Admin123!"), "admin"),
        ("Mia Student", "mia@tasknest.test", generate_password_hash("User123!"), "user"),
        ("Leo Maker", "leo@tasknest.test", generate_password_hash("User123!"), "user"),
    ]
    db.executemany("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)", users)
    user_rows = db.execute("SELECT id, email FROM users").fetchall()
    ids = {row["email"]: row["id"] for row in user_rows}
    tasks = [
        (ids["mia@tasknest.test"], "Prepare web project presentation", "Create a 10 minute demo script and screenshots.", "in_progress", "high", "2026-06-20", now, now),
        (ids["mia@tasknest.test"], "Finish database validation", "Check all API endpoints for invalid inputs.", "todo", "medium", "2026-06-14", now, now),
        (ids["leo@tasknest.test"], "Collect recipe ideas", "Add five easy dinner recipes to the task list.", "todo", "low", "2026-06-18", now, now),
        (ids["admin@tasknest.test"], "Review user accounts", "Verify that roles and task ownership work correctly.", "done", "medium", "2026-06-12", now, now),
    ]
    db.executemany(
        """
        INSERT INTO tasks (user_id, title, description, status, priority, due_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        tasks,
    )


def get_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def get_user(user_id):
    if not user_id:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def public_user(user):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user["created_at"],
    }


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped_view(**kwargs):
        if g.user["role"] != "admin":
            abort(403)
        return view(**kwargs)

    return wrapped_view


def validate_registration(name, email, password):
    errors = []
    if not (2 <= len(name) <= 80):
        errors.append("Name must be between 2 and 80 characters.")
    if not EMAIL_RE.match(email):
        errors.append("Enter a valid email address.")
    if len(password) < 8:
        errors.append("Password must contain at least 8 characters.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        errors.append("Password must contain at least one letter and one number.")
    return errors


def validate_task_payload(data):
    errors = []
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    status = str(data.get("status", "todo")).strip()
    priority = str(data.get("priority", "medium")).strip()
    due_date = str(data.get("due_date", "")).strip() or None

    if not (3 <= len(title) <= 120):
        errors.append("Title must be between 3 and 120 characters.")
    if len(description) > 1000:
        errors.append("Description can have at most 1000 characters.")
    if status not in VALID_STATUSES:
        errors.append("Status must be To do, In progress, or Done.")
    if priority not in VALID_PRIORITIES:
        errors.append("Priority must be Low, Medium, or High.")
    if due_date:
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            errors.append("Due date must use YYYY-MM-DD format.")

    return (
        {
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "due_date": due_date,
        },
        errors,
    )


def find_task_if_allowed(task_id):
    params = [task_id]
    owner_filter = ""
    if g.user["role"] != "admin":
        owner_filter = "AND user_id = ?"
        params.append(g.user["id"])
    return get_db().execute(f"SELECT * FROM tasks WHERE id = ? {owner_filter}", params).fetchone()


def get_task_for_response(task_id):
    row = get_db().execute(
        """
        SELECT t.*, u.name AS owner_name, u.email AS owner_email
        FROM tasks t
        JOIN users u ON u.id = t.user_id
        WHERE t.id = ?
        """,
        (task_id,),
    ).fetchone()
    return dict(row) if row else None


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_DEBUG") == "1")
