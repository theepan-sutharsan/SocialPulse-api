from tests.helpers import connect_demo


def test_history_ranges(auth, client):
    account = connect_demo(client, auth["headers"], "instagram", "@grow")
    for rng, minimum in [("7d", 7), ("30d", 30)]:
        resp = client.get(
            f"/api/social-accounts/{account['id']}/history?range={rng}", headers=auth["headers"]
        )
        assert resp.status_code == 200
        assert len(resp.get_json()["history"]) >= minimum


def test_grade_and_milestone(auth, client):
    account = connect_demo(client, auth["headers"], "instagram", "@grade")
    resp = client.get(f"/api/social-accounts/{account['id']}/grade", headers=auth["headers"])
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["grade"] in ("A++", "A+", "A", "B+", "B", "C", "D", "F", "N/A")
    assert body["milestone"]["target"] > body["current_followers"]
