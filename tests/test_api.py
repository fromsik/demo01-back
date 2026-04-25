from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_user():
    res = client.post(
        "/api/auth/mock-login",
        json={
            "providerType": "GOOGLE",
            "providerUserId": "p1",
            "email": "u@example.com",
            "nickname": "user",
        },
    )
    assert res.status_code == 200
    return res.json()["id"]


def test_auth_required():
    res = client.get("/api/templates")
    assert res.status_code == 401


def test_template_crud_and_default():
    user_id = create_user()
    headers = {"x-user-id": user_id}

    create_res = client.post(
        "/api/templates",
        headers=headers,
        json={
            "name": "weekday",
            "description": "work",
            "isDefault": True,
            "blocks": [
                {
                    "startTime": "07:00",
                    "endTime": "07:30",
                    "title": "morning",
                    "memo": "stretch",
                    "sortOrder": 0,
                },
                {
                    "startTime": "07:30",
                    "endTime": "09:00",
                    "title": "deep work",
                    "sortOrder": 1,
                },
            ],
        },
    )
    assert create_res.status_code == 200
    template_id = create_res.json()["id"]

    list_res = client.get("/api/templates", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["isDefault"] is True

    copy_res = client.post(f"/api/templates/{template_id}/copy", headers=headers)
    assert copy_res.status_code == 200
    assert copy_res.json()["name"].endswith("(copy)")


def test_daily_plan_validation():
    user_id = create_user()
    headers = {"x-user-id": user_id}

    bad = client.post(
        "/api/daily-plans",
        headers=headers,
        json={
            "planDate": "2026-04-24",
            "goals": [{"content": "a", "sortOrder": 0}],
            "timeBlocks": [
                {
                    "startTime": "07:00",
                    "endTime": "08:00",
                    "title": "a",
                    "sortOrder": 0,
                },
                {
                    "startTime": "07:30",
                    "endTime": "09:00",
                    "title": "b",
                    "sortOrder": 1,
                },
            ],
        },
    )
    assert bad.status_code == 400

    good = client.post(
        "/api/daily-plans",
        headers=headers,
        json={
            "planDate": "2026-04-24",
            "goals": [{"content": "important", "sortOrder": 0}],
            "timeBlocks": [
                {
                    "startTime": "07:00",
                    "endTime": "07:30",
                    "title": "a",
                    "sortOrder": 0,
                },
                {
                    "startTime": "07:30",
                    "endTime": "09:00",
                    "title": "b",
                    "sortOrder": 1,
                },
            ],
        },
    )
    assert good.status_code == 200
    assert good.json()["planDate"] == "2026-04-24"
