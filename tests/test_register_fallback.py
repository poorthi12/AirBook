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


def test_multi_passenger_payment_keeps_group_total(monkeypatch):
    flight_id = str(ObjectId())
    flight = {
        "_id": ObjectId(flight_id),
        "flight_number": "AI101",
        "from": "Delhi",
        "to": "Mumbai",
        "from_code": "DEL",
        "to_code": "BOM",
        "departure": "10:30",
        "arrival": "12:30",
        "flight_date": "2026-10-01",
        "airline": "Air India",
        "price": 5000,
        "available_seats": 20,
    }

    class FakeBookings:
        def __init__(self):
            self.saved = []

        def find_one(self, query):
            return None

        def insert_one(self, booking):
            self.saved.append(booking)
            return type("Inserted", (), {"inserted_id": ObjectId()})()

    fake_bookings = FakeBookings()

    class FakeFlights:
        def find_one(self, query):
            return flight

        def update_one(self, query, update):
            return None

    monkeypatch.setattr(app_module, "flights_collection", FakeFlights())
    monkeypatch.setattr(app_module, "bookings_collection", fake_bookings)

    with app_module.app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = "user-1"
            session["selected_flight_id"] = flight_id
            session["selected_seats"] = ["12A", "12B"]
            session["passengers"] = [
                {"name": "A", "email": "a@example.com", "phone": "1", "gender": "Male", "dob": "2000-01-01"},
                {"name": "B", "email": "b@example.com", "phone": "2", "gender": "Female", "dob": "2000-02-02"},
            ]
            session["booking_passengers"] = 2

        response = client.post(
            "/payment",
            data={"payment_method": "UPI"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/booking-confirmation")

    with client.session_transaction() as session:
        assert session["booking_total"] == 5250 * 2


def test_multi_passenger_confirmation_uses_all_bookings(monkeypatch):
    first_id = ObjectId()
    second_id = ObjectId()
    flight = {
        "_id": ObjectId(),
        "flight_number": "AI101",
        "from": "Delhi",
        "to": "Mumbai",
        "from_code": "DEL",
        "to_code": "BOM",
        "departure": "10:30",
        "arrival": "12:30",
        "flight_date": "2026-10-01",
        "airline": "Air India",
        "price": 5000,
    }

    class FakeBookings:
        def find(self, query):
            return [
                {
                    "_id": first_id,
                    "pnr": "ABC123",
                    "user_id": "user-1",
                    "flight_number": flight["flight_number"],
                    "from": flight["from"],
                    "from_code": flight["from_code"],
                    "to": flight["to"],
                    "to_code": flight["to_code"],
                    "departure": flight["departure"],
                    "arrival": flight["arrival"],
                    "flight_date": flight["flight_date"],
                    "airline": flight["airline"],
                    "passenger": {"name": "A"},
                    "seat": "12A",
                    "payment_status": "PAID",
                    "booking_status": "CONFIRMED",
                    "total": 5290,
                },
                {
                    "_id": second_id,
                    "pnr": "ABC123",
                    "user_id": "user-1",
                    "flight_number": flight["flight_number"],
                    "from": flight["from"],
                    "from_code": flight["from_code"],
                    "to": flight["to"],
                    "to_code": flight["to_code"],
                    "departure": flight["departure"],
                    "arrival": flight["arrival"],
                    "flight_date": flight["flight_date"],
                    "airline": flight["airline"],
                    "passenger": {"name": "B"},
                    "seat": "12B",
                    "payment_status": "PAID",
                    "booking_status": "CONFIRMED",
                    "total": 5290,
                },
            ]

    monkeypatch.setattr(app_module, "bookings_collection", FakeBookings())

    with app_module.app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = "user-1"
            session["booking_ids"] = [str(first_id), str(second_id)]
            session["booking_total"] = 10580

        response = client.get("/booking-confirmation")

    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert "A" in content and "B" in content
    assert "12A" in content and "12B" in content
    assert "₹10,580" in content


def test_single_passenger_accepts_numbered_form_fields(monkeypatch):
    flight_id = str(ObjectId())
    flight = {
        "_id": ObjectId(flight_id),
        "flight_number": "SK236",
        "from": "Bengaluru",
        "to": "Hyderabad",
        "from_code": "BLR",
        "to_code": "HYD",
        "departure": "05:45",
        "arrival": "06:30",
        "duration": "45m",
        "airline": "AirBook Airways",
        "price": 2999,
        "available_seats": 20,
    }

    class FakeFlights:
        def find_one(self, query):
            return flight

    class FakeBookings:
        def find(self, query):
            return []

    monkeypatch.setattr(app_module, "flights_collection", FakeFlights())
    monkeypatch.setattr(app_module, "bookings_collection", FakeBookings())

    with app_module.app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = "user-1"
            session["selected_flight_id"] = flight_id
            session["selected_seats"] = ["5F"]
            session["booking_passengers"] = 1

        response = client.post(
            "/passenger-details",
            data={
                "passenger_name_1": "Test Passenger",
                "passenger_email_1": "test@example.com",
                "passenger_phone_1": "9876543210",
                "passenger_gender_1": "Male",
                "passenger_dob_1": "1995-05-12",
            },
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/booking-review")

    with client.session_transaction() as session:
        assert session["passengers"][0]["name"] == "Test Passenger"
        assert session["passengers"][0]["email"] == "test@example.com"


def test_payment_requires_method_selection(monkeypatch):
    flight_id = str(ObjectId())
    flight = {
        "_id": ObjectId(flight_id),
        "flight_number": "AI101",
        "from": "Delhi",
        "to": "Mumbai",
        "from_code": "DEL",
        "to_code": "BOM",
        "departure": "10:30",
        "arrival": "12:30",
        "flight_date": "2026-10-01",
        "airline": "Air India",
        "price": 5000,
        "available_seats": 20,
    }

    monkeypatch.setattr(app_module, "flights_collection", type("FakeFlights", (), {"find_one": lambda self, query: flight})())
    monkeypatch.setattr(app_module, "bookings_collection", type("FakeBookings", (), {"find_one": lambda self, query: None})())

    with app_module.app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = "user-1"
            session["selected_flight_id"] = flight_id
            session["selected_seats"] = ["12A", "12B"]
            session["passengers"] = [
                {"name": "A", "email": "a@example.com", "phone": "1", "gender": "Male", "dob": "2000-01-01"},
                {"name": "B", "email": "b@example.com", "phone": "2", "gender": "Female", "dob": "2000-02-02"},
            ]

        response = client.post(
            "/payment",
            data={},
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert "Please select payment method to continue paying." in response.get_data(as_text=True)


def test_payment_page_redirects_after_completion(monkeypatch):
    flight_id = str(ObjectId())
    flight = {
        "_id": ObjectId(flight_id),
        "flight_number": "AI101",
        "from": "Delhi",
        "to": "Mumbai",
        "from_code": "DEL",
        "to_code": "BOM",
        "departure": "10:30",
        "arrival": "12:30",
        "flight_date": "2026-10-01",
        "airline": "Air India",
        "price": 5000,
        "available_seats": 20,
    }

    monkeypatch.setattr(app_module, "flights_collection", type("FakeFlights", (), {"find_one": lambda self, query: flight})())
    monkeypatch.setattr(app_module, "bookings_collection", type("FakeBookings", (), {"find_one": lambda self, query: None})())

    with app_module.app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = "user-1"
            session["selected_flight_id"] = flight_id
            session["selected_seats"] = ["12A", "12B"]
            session["passengers"] = [
                {"name": "A", "email": "a@example.com", "phone": "1", "gender": "Male", "dob": "2000-01-01"},
                {"name": "B", "email": "b@example.com", "phone": "2", "gender": "Female", "dob": "2000-02-02"},
            ]
            session["payment_completed"] = True

        response = client.get("/payment", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/booking-confirmation")


def test_new_booking_resets_payment_completed_flag(monkeypatch):
    with app_module.app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = "user-1"
            session["payment_completed"] = True
            session["selected_flight_id"] = "old-flight"
            session["selected_seats"] = ["12A"]
            session["passengers"] = [{"name": "Old"}]

        response = client.post(
            "/search-flights",
            data={
                "from": "Delhi",
                "to": "Mumbai",
                "departure": "2026-10-01",
                "passengers": "2",
            },
            follow_redirects=False,
        )

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert session.get("payment_completed") is None
        assert session.get("selected_flight_id") is None
        assert session.get("selected_seats") is None
        assert session.get("passengers") is None


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


def test_view_ticket_handles_partial_booking_data(monkeypatch):
    booking_id = ObjectId()

    class FakeBookings:
        def find_one(self, query):
            return {
                "_id": booking_id,
                "pnr": "ABC123",
                "user_id": "user-1",
                "flight_number": "AI101",
                "flight_date": "2026-10-01",
                "airline": "Air India",
                "from": "Delhi",
                "to": "Mumbai",
                "departure": "10:30",
                "arrival": "12:30",
                "passenger": "Test Passenger",
                "seat": "12A",
                "booking_status": "CONFIRMED",
                "payment_status": "PAID",
            }

    monkeypatch.setattr(app_module, "bookings_collection", FakeBookings())

    with app_module.app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = "user-1"

        response = client.get(f"/ticket/{booking_id}")

    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert "Test Passenger" in content
    assert "ABC123" in content


def test_forgot_password_sends_reset_otp(monkeypatch):
    class FakeUsersCollection:
        def find_one(self, query):
            return {"email": "user@example.com", "password": "hashed"}

    monkeypatch.setattr(app_module, "users_collection", FakeUsersCollection())
    monkeypatch.setattr(email_utils, "is_mail_configured", lambda: True)
    monkeypatch.setattr(email_utils, "send_reset_otp_email", lambda recipient, otp: True)

    with app_module.app.test_client() as client:
        response = client.post(
            "/forgot-password",
            data={"email": "user@example.com"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/reset-password")
