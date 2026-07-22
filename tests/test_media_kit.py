def test_update_and_public_media_kit(auth, client):
    up = client.put(
        "/api/media-kit",
        json={"bio": "We grow creators", "tagline": "Grow with us", "brand_color": "#4f46e5"},
        headers=auth["headers"],
    )
    assert up.status_code == 200
    slug = auth["workspace"]["slug"]
    pub = client.get(f"/api/media-kit/{slug}")
    assert pub.status_code == 200
    assert pub.get_json()["media_kit"]["bio"] == "We grow creators"


def test_white_label_requires_agency(auth, client):
    resp = client.put("/api/media-kit", json={"is_white_label": True}, headers=auth["headers"])
    assert resp.status_code == 403


def test_public_media_kit_missing(client):
    assert client.get("/api/media-kit/does-not-exist").status_code == 404
