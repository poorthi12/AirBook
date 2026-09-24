import app as app_module
import utils.email as email_utils
from bson import ObjectId


class FakeUsersCollection:
    def __init__(self):
        self.users = []

    def find_one(self, query):
        email = query.get("email")
        for user in self.users:
            if user.get("email") == email:
                return user
        return None

    def insert_one(self, user):
        self.users.append(user)
        return type("Inserted", (), {"inserted_id": "fake-id"})()


def test_register_requires_otp_when_email_is_configured(monkeypatch):
    fake_users = FakeUsersCollection()

    monkeypatch.setattr(app_module, "users_collection", fake_users)
    monkeypatch.setattr(email_utils, "is_mail_configured", lambda: True)
    monkeypatch.setattr(email_utils, "send_otp_email", lambda recipient, otp: True)

    with app_module.app.test_client() as client:
        response = client.post(
            "/register",
            data={
                "name": "Test User",
                "email": "new@example.com",
                "phone": "1234567890",
                "password": "Password123",
                "confirm_password": "Password123",
            },
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/verify")
    assert fake_users.find_one({"email": "new@example.com"}) is None


def test_register_rejects_when_email_provider_is_not_configured(monkeypatch):
    fake_users = FakeUsersCollection()

    monkeypatch.setattr(app_module, "users_collection", fake_users)
    monkeypatch.setattr(email_utils, "is_mail_configured", lambda: False)

    with app_module.app.test_client() as client:
        response = client.post(
            "/register",
            data={
                "name": "Test User",
                "email": "another@example.com",
                "phone": "1234567890",
                "password": "Password123",
                "confirm_password": "Password123",
            },
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/register")
    assert fake_users.find_one({"email": "another@example.com"}) is None


def test_multi_passenger_seat_selection_accepts_two_seats(monkeypatch):
    flight_id = str(ObjectId())
    fake_flights = {"_id": ObjectId(flight_id), "flight_number": "AI101", "from": "Delhi", "to": "Mumbai", "available_seats": 20, "price": 5000}
    fake_bookings = type("FakeBookings", (), {"find": lambda self, query: []})()

    monkeypatch.setattr(app_module, "flights_collection", type("FakeFlights", (), {"find_one": lambda self, query: fake_flights})())
    monkeypatch.setattr(app_module, "bookings_collection", fake_bookings)

    with app_module.app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = "user-1"
            session["booking_passengers"] = 2

        response = client.post(
            f"/seat-selection/{flight_id}",
            data={"seat": "12A,12B"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/passenger-details")

    with client.session_transaction() as session:
        assert session["selected_seats"] == ["12A", "12B"]


def test_register_rejects_when_otp_email_send_fails(monkeypatch):
    fake_users = FakeUsersCollection()

    monkeypatch.setattr(app_module, "users_collection", fake_users)
    monkeypatch.setattr(email_utils, "is_mail_configured", lambda: True)
    monkeypatch.setattr(email_utils, "send_otp_email", lambda recipient, otp: False)

    with app_module.app.test_client() as client:
        response = client.post(
            "/register",
            data={
                "name": "Test User",
                "email": "failed@example.com",
                "phone": "1234567890",
                "password": "Password123",
                "confirm_password": "Password123",
            },
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/register")
    assert fake_users.find_one({"email": "failed@example.com"}) is None

    with client.session_transaction() as session:
        assert "registration_data" not in session
        assert "registration_otp" not in session
