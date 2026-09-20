from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import SECRET_KEY
from database.db import test_connection, users_collection, flights_collection,bookings_collection
from werkzeug.security import generate_password_hash, check_password_hash   
from bson.objectid import ObjectId
from datetime import datetime
app = Flask(__name__)

app.secret_key = SECRET_KEY
@app.route("/")
def home():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "home/home.html",
        name=session.get("user_name"),
        email=session.get("user_email")
    )

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.", "error")
            return redirect(url_for("login"))

        # Find user in MongoDB
        user = users_collection.find_one({
            "email": email
        })

        if not user:
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        # Check password
        if not check_password_hash(user["password"], password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        # Login successful
        session["user_id"] = str(user["_id"])
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]

        flash("Login successful!", "success")

        return redirect(url_for("home"))

    return render_template("auth/login.html")

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Check empty fields
        if not name or not email or not phone or not password:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("register"))

        # Check password
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        # Check password length
        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
            return redirect(url_for("register"))

        # Check if email already exists
        existing_user = users_collection.find_one({
            "email": email
        })

        if existing_user:
            flash("An account with this email already exists.", "error")
            return redirect(url_for("register"))

        # Hash password
        password_hash = generate_password_hash(password)

        # Create user
        user = {
            "name": name,
            "email": email,
            "phone": phone,
            "password": password_hash,
            "verified": False
        }

        # Insert into MongoDB
        result = users_collection.insert_one(user)

        print("USER INSERTED SUCCESSFULLY")
        print("USER ID:", result.inserted_id)
        print("TOTAL USERS:", users_collection.count_documents({}))

        flash("Account created successfully! You can now login.", "success")

        return redirect(url_for("login"))

    return render_template("auth/register.html")


@app.route("/search-flights", methods=["GET", "POST"])
def search_flights():

    print("================================")
    print("SEARCH ROUTE HIT")
    print("METHOD:", request.method)
    print("FORM DATA:", request.form)
    print("================================")

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        from_city = request.form.get("from", "")
        to_city = request.form.get("to", "")
        departure = request.form.get("departure", "")
        passengers = request.form.get("passengers", "1")

        print("FROM:", from_city)
        print("TO:", to_city)
        print("DATE:", departure)
        print("PASSENGERS:", passengers)

        flights = list(
            flights_collection.find({
                "from": {
                    "$regex": f"^{from_city}$",
                    "$options": "i"
                },
                "to": {
                    "$regex": f"^{to_city}$",
                    "$options": "i"
                },
                "flight_date": departure
            })
        )
        print("SEARCH DATE:", departure)
        print("FLIGHTS FOUND:", len(flights))

        for flight in flights:
            print(
                flight["flight_number"],
                "|",
                flight.get("flight_date"),
                "|",
                flight["from"],
                "→",
                flight["to"]
            )

        print("FLIGHTS FOUND:", len(flights))

        return render_template(
            "flights/results.html",
            flights=flights,
            from_city=from_city,
            to_city=to_city,
            departure=departure,
            passengers=passengers
        )

    return redirect(url_for("home"))

@app.route("/flight/<flight_id>")
def flight_details(flight_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        flight = flights_collection.find_one({
            "_id": ObjectId(flight_id)
        })
    except Exception:
        flight = None

    if not flight:
        flash("Flight not found.", "error")
        return redirect(url_for("home"))

    return render_template(
        "flights/flight_details.html",
        flight=flight
    )
@app.route("/seat-selection/<flight_id>", methods=["GET", "POST"])
def seat_selection(flight_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        flight = flights_collection.find_one({
            "_id": ObjectId(flight_id)
        })
    except Exception:
        flight = None

    if not flight:
        flash("Flight not found.", "error")
        return redirect(url_for("home"))

    # Get seats already booked for this flight
    booked_seats = bookings_collection.find({
        "flight_id": flight["_id"],
        "booking_status": {
            "$ne": "CANCELLED"
        }
    })

    booked_seats = [
        booking["seat"]
        for booking in booked_seats
        if booking.get("seat")
    ]

    if request.method == "POST":

        selected_seat = request.form.get("seat")

        if not selected_seat:
            flash("Please select a seat.", "error")
            return redirect(
                url_for("seat_selection", flight_id=flight_id)
            )

        # Check if selected seat is already booked
        if selected_seat in booked_seats:
            flash(
                f"Seat {selected_seat} is already booked. Please select another seat.",
                "error"
            )

            return redirect(
                url_for("seat_selection", flight_id=flight_id)
            )

        session["selected_flight_id"] = flight_id
        session["selected_seat"] = selected_seat

        return redirect(
            url_for("passenger_details")
        )

    return render_template(
        "flights/seat_selection.html",
        flight=flight,
        booked_seats=booked_seats
    )

@app.route("/passenger-details", methods=["GET", "POST"])
def passenger_details():

    if "user_id" not in session:
        return redirect(url_for("login"))

    flight_id = session.get("selected_flight_id")
    selected_seat = session.get("selected_seat")

    if not flight_id or not selected_seat:
        flash("Please select a flight and seat first.", "error")
        return redirect(url_for("home"))

    try:
        flight = flights_collection.find_one({
            "_id": ObjectId(flight_id)
        })
    except Exception:
        flight = None

    if not flight:
        flash("Flight not found.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":

        passenger_name = request.form.get("passenger_name", "").strip()
        passenger_email = request.form.get("passenger_email", "").strip().lower()
        passenger_phone = request.form.get("passenger_phone", "").strip()
        passenger_gender = request.form.get("passenger_gender", "")
        passenger_dob = request.form.get("passenger_dob", "")

        if not passenger_name or not passenger_email or not passenger_phone:
            flash("Please fill in all required passenger details.", "error")
            return redirect(url_for("passenger_details"))

        session["passenger"] = {
            "name": passenger_name,
            "email": passenger_email,
            "phone": passenger_phone,
            "gender": passenger_gender,
            "dob": passenger_dob
        }

        return redirect(url_for("booking_review"))

    return render_template(
        "booking/passenger_details.html",
        flight=flight,
        selected_seat=selected_seat
    )

@app.route("/booking-review", methods=["GET", "POST"])
def booking_review():

    if "user_id" not in session:
        return redirect(url_for("login"))

    flight_id = session.get("selected_flight_id")
    selected_seat = session.get("selected_seat")
    passenger = session.get("passenger")

    if not flight_id or not selected_seat or not passenger:
        flash("Booking information is incomplete.", "error")
        return redirect(url_for("home"))

    try:
        flight = flights_collection.find_one({
            "_id": ObjectId(flight_id)
        })
    except Exception:
        flight = None

    if not flight:
        flash("Flight not found.", "error")
        return redirect(url_for("home"))

    base_fare = flight["price"]
    taxes = round(base_fare * 0.05)
    total = base_fare + taxes

    if request.method == "POST":
        return redirect(url_for("payment"))

    return render_template(
        "booking/payment.html",
        flight=flight,
        passenger=passenger,
        selected_seat=selected_seat,
        base_fare=base_fare,
        taxes=taxes,
        total=total     
    )

@app.route("/payment", methods=["GET", "POST"])
def payment():

    if "user_id" not in session:
        return redirect(url_for("login"))

    flight_id = session.get("selected_flight_id")
    selected_seat = session.get("selected_seat")
    passenger = session.get("passenger")

    if not flight_id or not selected_seat or not passenger:
        flash("Booking information is incomplete.", "error")
        return redirect(url_for("home"))

    try:
        flight = flights_collection.find_one({
            "_id": ObjectId(flight_id)
        })
    except Exception:
        flight = None

    if not flight:
        flash("Flight not found.", "error")
        return redirect(url_for("home"))

    base_fare = flight["price"]
    taxes = round(base_fare * 0.05)
    total = base_fare + taxes

    if request.method == "POST":

        payment_method = request.form.get("payment_method")

        if not payment_method:
            flash("Please select a payment method.", "error")
            return redirect(url_for("payment"))

        # -----------------------------------
        # CHECK FLIGHT AVAILABILITY
        # -----------------------------------

        if flight.get("available_seats", 0) <= 0:
            flash("Sorry, this flight is fully booked.", "error")
            return redirect(url_for("home"))

        # -----------------------------------
        # CHECK SELECTED SEAT AVAILABILITY
        # -----------------------------------

        existing_booking = bookings_collection.find_one({
            "flight_id": flight["_id"],
            "seat": selected_seat,
            "booking_status": "CONFIRMED"
        })

        if existing_booking:

            flash(
                f"Seat {selected_seat} has already been booked. Please select another seat.",
                "error"
            )

            return redirect(
                url_for(
                    "seat_selection",
                    flight_id=str(flight["_id"])
                )
            )

        # -----------------------------------
        # GENERATE PNR
        # -----------------------------------

        import random
        import string

        pnr = "".join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=6
            )
        )

        # -----------------------------------
        # CREATE BOOKING
        # -----------------------------------

        booking = {

            "pnr": pnr,

            "user_id": session["user_id"],

            "flight_id": flight["_id"],

            "flight_number": flight["flight_number"],

            "flight_date": flight["flight_date"],

            "airline": flight["airline"],

            "from": flight["from"],
            "from_code": flight["from_code"],

            "to": flight["to"],
            "to_code": flight["to_code"],

            "departure": flight["departure"],
            "arrival": flight["arrival"],

            "passenger": passenger,

            "seat": selected_seat,

            "base_fare": base_fare,
            "taxes": taxes,
            "total": total,

            "payment_method": payment_method,

            "payment_status": "PAID",

            "booking_status": "CONFIRMED"
        }

        # -----------------------------------
        # INSERT BOOKING
        # -----------------------------------

        result = bookings_collection.insert_one(booking)

        # -----------------------------------
        # REDUCE AVAILABLE SEATS
        # -----------------------------------

        flights_collection.update_one(
            {
                "_id": flight["_id"],
                "available_seats": {
                    "$gt": 0
                }
            },
            {
                "$inc": {
                    "available_seats": -1
                }
            }
        )

        # -----------------------------------
        # SAVE BOOKING IN SESSION
        # -----------------------------------

        session["booking_id"] = str(result.inserted_id)
        session["pnr"] = pnr

        # -----------------------------------
        # GO TO CONFIRMATION
        # -----------------------------------

        return redirect(
            url_for("booking_confirmation")
        )

    return render_template(
        "booking/payment.html",
        flight=flight,
        selected_seat=selected_seat,
        passenger=passenger,
        base_fare=base_fare,
        taxes=taxes,
        total=total
    )


@app.route("/booking-confirmation")
def booking_confirmation():

    if "user_id" not in session:
        return redirect(url_for("login"))

    booking_id = session.get("booking_id")

    if not booking_id:
        flash("Booking not found.", "error")
        return redirect(url_for("home"))

    try:
        booking = bookings_collection.find_one({
            "_id": ObjectId(booking_id)
        })
    except Exception:
        booking = None

    if not booking:
        flash("Booking not found.", "error")
        return redirect(url_for("home"))

    return render_template(
        "booking/confirmation.html",
        booking=booking
    )

@app.route("/ticket/<booking_id>")
def ticket(booking_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        booking = bookings_collection.find_one({
            "_id": ObjectId(booking_id),
            "user_id": session["user_id"]
        })
    except Exception:
        booking = None

    if not booking:
        flash("Ticket not found.", "error")
        return redirect(url_for("booking_history"))

    return render_template(
        "booking/confirmation.html",
        booking=booking
    )

@app.route("/booking-history")
def booking_history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    from datetime import datetime

    bookings = list(
        bookings_collection.find({
            "user_id": session["user_id"]
        }).sort("_id", -1)
    )

    upcoming = []
    completed = []
    cancelled = []

    today = datetime.now().strftime("%Y-%m-%d")

    for booking in bookings:

        status = booking.get("booking_status", "CONFIRMED")

        # Cancelled bookings
        if status == "CANCELLED":
            cancelled.append(booking)
            continue

        # Get flight date
        flight = flights_collection.find_one({
            "_id": booking["flight_id"]
        })

        if flight and flight.get("flight_date"):

            flight_date = flight["flight_date"]

            if flight_date < today:
                completed.append(booking)
            else:
                upcoming.append(booking)

        else:
            # If flight date is unavailable,
            # keep it in upcoming
            upcoming.append(booking)

        for booking in upcoming + completed + cancelled:

            if booking.get("flight_date"):
                date_obj = datetime.strptime(
                    booking["flight_date"],
                    "%Y-%m-%d"
                )

                booking["formatted_date"] = date_obj.strftime(
                    "%d %B %Y"
                )

    return render_template(
        "profile/booking_history.html",
        upcoming=upcoming,
        completed=completed,
        cancelled=cancelled
    )
@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        user = users_collection.find_one({
            "_id": ObjectId(session["user_id"])
        })
    except Exception:
        user = None

    if not user:
        session.clear()
        flash("Your account could not be found.", "error")
        return redirect(url_for("login"))

    booking_count = bookings_collection.count_documents({
        "user_id": session["user_id"]
    })

    return render_template(
        "profile/profile.html",
        user=user,
        booking_count=booking_count
    )

@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        user = users_collection.find_one({
            "_id": ObjectId(session["user_id"])
        })
    except Exception:
        user = None

    if not user:
        session.clear()
        flash("Your account could not be found.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not phone:
            flash("Name and phone number are required.", "error")
            return redirect(url_for("edit_profile"))

        users_collection.update_one(
            {
                "_id": ObjectId(session["user_id"])
            },
            {
                "$set": {
                    "name": name,
                    "phone": phone
                }
            }
        )

        # Update current session
        session["user_name"] = name

        flash("Profile updated successfully!", "success")

        return redirect(url_for("profile"))

    return render_template(
        "profile/edit_profile.html",
        user=user
    )

@app.route("/cancel-booking/<booking_id>", methods=["POST"])
def cancel_booking(booking_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        booking = bookings_collection.find_one({
            "_id": ObjectId(booking_id),
            "user_id": session["user_id"]
        })
    except Exception:
        booking = None

    if not booking:
        flash("Booking not found.", "error")
        return redirect(url_for("booking_history"))

    if booking.get("booking_status") == "CANCELLED":
        flash("This booking has already been cancelled.", "error")
        return redirect(url_for("booking_history"))

    bookings_collection.update_one(
        {
            "_id": booking["_id"]
        },
        {
            "$set": {
                "booking_status": "CANCELLED"
            }
        }
    )

    flights_collection.update_one(
        {
            "_id": booking["flight_id"]
        },
        {
            "$inc": {
                "available_seats": 1
            }
        }
    )

    flash(
        f"Booking {booking['pnr']} has been cancelled successfully.",
        "success"
    )

    return redirect(url_for("booking_history"))

print("\nREGISTERED ROUTES:")
for rule in app.url_map.iter_rules():
    print(rule, "->", rule.endpoint)

if __name__ == "__main__":

    app.run(debug=True)