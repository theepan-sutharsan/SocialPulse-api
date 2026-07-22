def test_create_and_list_referral(auth, client):
    resp = client.post(
        "/api/referrals", json={"referred_email": "friend@test.com"}, headers=auth["headers"]
    )
    assert resp.status_code == 201
    listing = client.get("/api/referrals", headers=auth["headers"]).get_json()
    assert len(listing["referrals"]) == 1


def test_duplicate_referral_rejected(auth, client):
    client.post("/api/referrals", json={"referred_email": "dup@test.com"}, headers=auth["headers"])
    resp = client.post("/api/referrals", json={"referred_email": "dup@test.com"}, headers=auth["headers"])
    assert resp.status_code == 409
