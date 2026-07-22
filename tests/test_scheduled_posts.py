from tests.helpers import connect_demo


def _account(auth, client):
    return connect_demo(client, auth["headers"], "instagram", "@sched")


def test_create_and_list_scheduled_post(auth, client):
    account = _account(auth, client)
    resp = client.post(
        "/api/scheduled-posts",
        json={
            "social_account_id": account["id"],
            "caption": "Launch day!",
            "scheduled_at": "2026-09-01T09:00:00Z",
        },
        headers=auth["headers"],
    )
    assert resp.status_code == 201
    listing = client.get("/api/scheduled-posts", headers=auth["headers"]).get_json()
    assert len(listing["scheduled_posts"]) == 1


def test_update_and_cancel(auth, client):
    account = _account(auth, client)
    post = client.post(
        "/api/scheduled-posts",
        json={
            "social_account_id": account["id"],
            "caption": "Draft",
            "scheduled_at": "2026-09-01T09:00:00Z",
        },
        headers=auth["headers"],
    ).get_json()["scheduled_post"]
    up = client.put(
        f"/api/scheduled-posts/{post['id']}",
        json={"caption": "Final"},
        headers=auth["headers"],
    )
    assert up.get_json()["scheduled_post"]["caption"] == "Final"
    cancel = client.patch(f"/api/scheduled-posts/{post['id']}/cancel", headers=auth["headers"])
    assert cancel.get_json()["scheduled_post"]["status"] == "cancelled"


def test_create_requires_valid_account(auth, client):
    resp = client.post(
        "/api/scheduled-posts",
        json={"social_account_id": 9999, "caption": "x", "scheduled_at": "2026-09-01T09:00:00Z"},
        headers=auth["headers"],
    )
    assert resp.status_code == 404
