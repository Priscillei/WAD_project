import re

import pytest

from app import create_app, get_db


def extract_csrf(response):
    html = response.get_data(as_text=True)
    match = re.search(r'name="csrf-token" content="([^"]+)"', html)
    assert match, "CSRF token not found in rendered page"
    return match.group(1)


@pytest.fixture()
def app(tmp_path):
    test_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(tmp_path / "tasknest-test.db"),
        }
    )
    yield test_app


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email="mia@tasknest.test", password="User123!"):
    response = client.get("/login")
    token = extract_csrf(response)
    response = client.post(
        "/login",
        data={"email": email, "password": password, "csrf_token": token},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with client.session_transaction() as session:
        return session["csrf_token"]


def test_seed_data_and_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "admin@tasknest.test" in response.get_data(as_text=True)


def test_user_task_crud_search_and_delete(client):
    token = login(client)

    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert all(task["owner_email"] == "mia@tasknest.test" for task in response.json["tasks"])

    response = client.post(
        "/api/tasks",
        json={
            "title": "Write automated tests",
            "description": "Cover task creation and updating.",
            "status": "todo",
            "priority": "high",
            "due_date": "2026-06-22",
        },
        headers={"X-CSRFToken": token},
    )
    assert response.status_code == 201
    task_id = response.json["task"]["id"]

    response = client.get("/api/tasks?search=automated&sort=title&order=asc")
    assert response.status_code == 200
    assert any(task["id"] == task_id for task in response.json["tasks"])

    response = client.put(
        f"/api/tasks/{task_id}",
        json={
            "title": "Write automated tests now",
            "description": "Updated through the API.",
            "status": "done",
            "priority": "medium",
            "due_date": "2026-06-23",
        },
        headers={"X-CSRFToken": token},
    )
    assert response.status_code == 200
    assert response.json["task"]["status"] == "done"

    response = client.delete(f"/api/tasks/{task_id}", headers={"X-CSRFToken": token})
    assert response.status_code == 200
    assert response.json["deleted"] is True


def test_server_side_validation_rejects_invalid_task(client):
    token = login(client)
    response = client.post(
        "/api/tasks",
        json={"title": "x", "status": "bad", "priority": "urgent", "due_date": "tomorrow"},
        headers={"X-CSRFToken": token},
    )
    assert response.status_code == 400
    assert "errors" in response.json


def test_user_cannot_delete_other_users_task(client, app):
    token = login(client)
    with app.app_context():
        other_task = get_db().execute(
            """
            SELECT t.id FROM tasks t
            JOIN users u ON u.id = t.user_id
            WHERE u.email = ?
            LIMIT 1
            """,
            ("leo@tasknest.test",),
        ).fetchone()["id"]
    response = client.delete(f"/api/tasks/{other_task}", headers={"X-CSRFToken": token})
    assert response.status_code == 404


def test_admin_can_view_all_tasks_and_change_role(client):
    token = login(client, "admin@tasknest.test", "Admin123!")
    response = client.get("/api/tasks")
    assert response.status_code == 200
    owners = {task["owner_email"] for task in response.json["tasks"]}
    assert "mia@tasknest.test" in owners
    assert "leo@tasknest.test" in owners

    users = client.get("/api/users").json["users"]
    leo = next(user for user in users if user["email"] == "leo@tasknest.test")
    response = client.patch(
        f"/api/users/{leo['id']}",
        json={"role": "admin"},
        headers={"X-CSRFToken": token},
    )
    assert response.status_code == 200
    assert response.json["user"]["role"] == "admin"


def test_end_to_end_register_login_create_update_delete(client):
    register_page = client.get("/register")
    token = extract_csrf(register_page)
    response = client.post(
        "/register",
        data={
            "name": "End User",
            "email": "enduser@example.test",
            "password": "EndUser123",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Account created" in response.get_data(as_text=True)

    token = login(client, "enduser@example.test", "EndUser123")
    created = client.post(
        "/api/tasks",
        json={
            "title": "E2E task",
            "description": "Created during full user flow.",
            "status": "todo",
            "priority": "low",
            "due_date": "2026-07-01",
        },
        headers={"X-CSRFToken": token},
    )
    assert created.status_code == 201
    task_id = created.json["task"]["id"]

    updated = client.put(
        f"/api/tasks/{task_id}",
        json={
            "title": "E2E task updated",
            "description": "Updated during full user flow.",
            "status": "in_progress",
            "priority": "medium",
            "due_date": "2026-07-02",
        },
        headers={"X-CSRFToken": token},
    )
    assert updated.status_code == 200
    assert updated.json["task"]["title"] == "E2E task updated"

    deleted = client.delete(f"/api/tasks/{task_id}", headers={"X-CSRFToken": token})
    assert deleted.status_code == 200
