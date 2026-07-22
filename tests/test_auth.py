from tests.helpers import register


def test_register_creates_workspace_and_owner(client):
    ctx = register(client)
    assert ctx["workspace"]["role"] == "owner"
    assert ctx["workspace"]["plan_tier"] == "free"


def test_register_rejects_short_password(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": "a@b.com", "password": "short", "full_name": "A"},
    )
    assert resp.status_code == 400
    assert "errors" in resp.get_json()


def test_register_rejects_duplicate_email(client):
    ctx = register(client)
    resp = client.post(
        "/api/auth/register",
        json={"email": ctx["email"], "password": "Password123", "full_name": "Dup"},
    )
    assert resp.status_code == 409


def test_login_success_and_failure(client):
    ctx = register(client)
    ok = client.post("/api/auth/login", json={"email": ctx["email"], "password": "Password123"})
    assert ok.status_code == 200
    assert ok.get_json()["access_token"]
    bad = client.post("/api/auth/login", json={"email": ctx["email"], "password": "wrong"})
    assert bad.status_code == 401


def test_profile_requires_auth(client):
    assert client.get("/api/auth/profile").status_code == 401


def test_profile_update(client):
    ctx = register(client)
    resp = client.put("/api/auth/profile", json={"full_name": "New Name"}, headers=ctx["headers"])
    assert resp.status_code == 200
    assert resp.get_json()["user"]["full_name"] == "New Name"
