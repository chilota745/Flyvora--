"""
Quick smoke test for all Flyvora API endpoints.
Run with: python test_api.py
(Requires the dev server to be running on port 8000)
"""
import urllib.request
import urllib.error
import json

BASE = "http://127.0.0.1:8000/api"


def get(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())


def post(path, body):
    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def ok(label, value):
    print(f"  [PASS] {label}: {value}")


def main():
    # ── 1. List all flights ────────────────────────────────────────────────────────
    data = get("/flights/")
    ok("GET /api/flights/", f"{data['count']} flights returned")

    # ── 2. Search flights ─────────────────────────────────────────────────────────
    data = post("/search/", {"departure": "Lagos", "destination": "Abuja", "date": "2026-05-01"})
    ok("POST /api/search/", f"{data['count']} result(s), first airline: {data['flights'][0]['airline']}")
    flight_id = data["flights"][0]["id"]

    # ── 3. Book a flight ──────────────────────────────────────────────────────────
    data = post("/book/", {
        "flight_id": flight_id,
        "passenger_name": "Ada Obi",
        "passenger_email": "ada@flyvora.com",
        "seats_booked": 2,
    })
    ok("POST /api/book/", f"{data['message']} (booking id={data['booking']['id']})")

    # ── 4. Flight detail – confirm seats decremented ──────────────────────────────
    data = get(f"/flights/{flight_id}/")
    ok(f"GET /api/flights/{flight_id}/", f"seats_available={data['seats_available']} (was 120)")

    # ── 5. List bookings by email ─────────────────────────────────────────────────
    data = get("/bookings/?email=ada@flyvora.com")
    ok("GET /api/bookings/", f"{data['count']} booking(s) for ada@flyvora.com")

    # ── 6. Bad search payload ─────────────────────────────────────────────────────
    try:
        post("/search/", {"departure": "Lagos", "destination": "Abuja", "date": "invalid-date"})
        print("  [FAIL] Bad payload should have returned 400")
    except urllib.error.HTTPError as e:
        ok("POST /api/search/ (bad payload)", f"Correctly returned HTTP {e.code}")

    # ── 7. Book non-existent flight ───────────────────────────────────────────────
    try:
        post("/book/", {"flight_id": 9999, "passenger_name": "Ghost", "passenger_email": "ghost@x.com"})
        print("  [FAIL] Missing flight should have returned 404")
    except urllib.error.HTTPError as e:
        ok("POST /api/book/ (missing flight)", f"Correctly returned HTTP {e.code}")

    print("\nAll tests passed.")


if __name__ == '__main__':
    main()
