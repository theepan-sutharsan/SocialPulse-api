from tests.helpers import register


def test_list_workspaces(auth, client):
    resp = client.get("/api/workspaces", headers=auth["headers"])
    assert resp.status_code == 200
    assert len(resp.get_json()["workspaces"]) == 1


def test_create_additional_workspace(auth, client):
    resp = client.post("/api/workspaces", json={"name": "Second WS", "is_agency": True}, headers=auth["headers"])
    assert resp.status_code == 201
    assert resp.get_json()["workspace"]["is_agency"] is True


def test_get_and_update_workspace(auth, client):
    ws_id = auth["workspace"]["id"]
    assert client.get(f"/api/workspaces/{ws_id}", headers=auth["headers"]).status_code == 200
    resp = client.put(f"/api/workspaces/{ws_id}", json={"name": "Renamed"}, headers=auth["headers"])
    assert resp.status_code == 200
    assert resp.get_json()["workspace"]["name"] == "Renamed"


def test_cannot_access_foreign_workspace(auth, client):
    other = register(client)
    resp = client.get(f"/api/workspaces/{other['workspace']['id']}", headers=auth["headers"])
    assert resp.status_code == 403
