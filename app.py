import base64
from datetime import datetime, timedelta
import io
import os
import random
from bson.objectid import ObjectId
from config import (
    MAIL_DEFAULT_SENDER,
    MAIL_PASSWORD,
    MAIL_PORT,
    MAIL_SERVER,
    MAIL_USE_TLS,
    MAIL_USERNAME,
    MONGO_URI,
    SECRET_KEY,
)
from database.db import (
    bookings_collection,
    flights_collection,
    test_connection,
    users_collection,
)
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from PIL import Image
import qrcode
from reportlab.pdfgen import canvas
from routes.admin import admin_bp
from utils.email import is_mail_configured, mail, send_otp_email
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(admin_bp)

# --- PRODUCTION REVERSE PROXY SUPPORT (RENDER) ---
# Tells Flask it is running behind Render's HTTPS load balancer
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1
)

# --- SECRET KEY & SESSION STABILITY ---
# A fallback ensures all Gunicorn worker processes decode the session identically
app.secret_key = SECRET_KEY or os.getenv(
    "SECRET_KEY", "airbook-skybook-fixed-production-secret-key"
)
app.config["SECRET_KEY"] = app.secret_key
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.getenv("FLASK_ENV") != "development"
    and not app.config.get("DEBUG", False)
)

# --- FLASK-MAIL CONFIGURATION ---
# Dynamically configures Port 465 (SSL) or Port 587 (TLS) cleanly
mail_port = int(os.getenv("MAIL_PORT", MAIL_PORT or 465))
is_port_465 = mail_port == 465

app.config["MAIL_SERVER"] = (
    os.getenv("MAIL_SERVER") or MAIL_SERVER or "smtp.gmail.com"
)
app.config["MAIL_PORT"] = mail_port
app.config["MAIL_USE_SSL"] = (
    str(os.getenv("MAIL_USE_SSL", "True" if is_port_465 else "False"))
    .strip()
    .lower()
    in {"1", "true", "yes", "on"}
)
app.config["MAIL_USE_TLS"] = (
    str(os.getenv("MAIL_USE_TLS", "False" if is_port_465 else "True"))
    .strip()
    .lower()
    in {"1", "true", "yes", "on"}
)
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME") or MAIL_USERNAME
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD") or MAIL_PASSWORD
app.config["MAIL_DEFAULT_SENDER"] = (
    os.getenv("MAIL_DEFAULT_SENDER")
    or MAIL_DEFAULT_SENDER
    or app.config["MAIL_USERNAME"]
)
app.config["MAIL_TIMEOUT"] = int(os.getenv("MAIL_TIMEOUT", "25"))

mail.init_app(app)


@app.route("/api/upcoming-flights")
def upcoming_flights():

  if "user_id" not in session:
    return jsonify({"error": "Unauthorized"}), 401

  today = datetime.now().strftime("%Y-%m-%d")
  tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
  two_months_end = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")

  flights = list(
      flights_collection.find({
          "flight_date": {"$gte": today, "$lte": two_months_end}
      })
      .sort("flight_date", 1)
      .sort("departure", 1)
  )

  today_flights = []
  tomorrow_flights = []
  next_two_months = []

  for flight in flights:
    flight_copy = {
        "flight_number": flight.get("flight_number"),
        "airline": flight.get("airline"),
        "from": flight.get("from"),
        "to": flight.get("to"),
        "from_code": flight.get("from_code"),
        "to_code": flight.get("to_code"),
        "flight_date": flight.get("flight_date"),
        "departure": flight.get("departure"),
        "arrival": flight.get("arrival"),
        "duration": flight.get("duration"),
        "price": flight.get("price"),
        "available_seats": flight.get("available_seats"),
    }

    if flight.get("flight_date") == today:
      today_flights.append(flight_copy)
    elif flight.get("flight_date") == tomorrow:
      tomorrow_flights.append(flight_copy)

    if flight.get("flight_date") >= today:
      next_two_months.append(flight_copy)

  return jsonify({
      "today": today_flights[:4],
      "tomorrow": tomorrow_flights[:4],
      "next_two_months": next_two_months[:200],
      "generated_at": datetime.now().isoformat(),
  })


@app.route("/")
def home():

  if "user_id" not in session:
    return redirect(url_for("login"))

  city_names = sorted(
      set(
          flights_collection.distinct("from")
          + flights_collection.distinct("to")
      )
  )

  return render_template(
      "home/home.html",
      name=session.get("user_name"),
      email=session.get("user_email"),
      city_names=city_names,
  )


@app.route("/all-upcoming-flights")
def all_upcoming_flights():

  if "user_id" not in session:
    return redirect(url_for("login"))

  start_date = datetime.now().strftime("%Y-%m-%d")
  end_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")

  flights = list(
      flights_collection.find({
          "flight_date": {"$gte": start_date, "$lte": end_date}
      })
      .sort("flight_date", 1)
      .sort("departure", 1)
  )

  grouped_flights = {}

  for flight in flights:
    flight_date = flight.get("flight_date")
    grouped_flights.setdefault(flight_date, []).append({
        "flight_number": flight.get("flight_number"),
        "airline": flight.get("airline"),
        "from": flight.get("from"),
        "to": flight.get("to"),
        "from_code": flight.get("from_code"),
        "to_code": flight.get("to_code"),
        "flight_date": flight_date,
        "departure": flight.get("departure"),
        "arrival": flight.get("arrival"),
        "duration": flight.get("duration"),
        "price": flight.get("price"),
        "available_seats": flight.get("available_seats"),
    })

  return render_template(
      "home/upcoming_flights.html",
      name=session.get("user_name"),
      grouped_flights=sorted(grouped_flights.items()),
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
    user = users_collection.find_one({"email": email})

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
    session["user_role"] = user.get("role", "user")

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

    # Basic validations
    if not name or not email or not phone or not password:
      flash("Please fill in all fields.", "error")
      return redirect(url_for("register"))

    if password != confirm_password:
      flash("Passwords do not match.", "error")
      return redirect(url_for("register"))

    if len(password) < 6:
      flash("Password must contain at least 6 characters.", "error")
      return redirect(url_for("register"))

    # Check if user already exists
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
      flash("An account with this email already exists.", "error")
      return redirect(url_for("register"))

    if not is_mail_configured():
      flash(
          "Email verification is not configured on this server. Please contact"
          " support.",
          "error",
      )
      return redirect(url_for("register"))

    # Generate OTP and store in session
    otp = str(random.randint(100000, 999999))
    session["registration_otp"] = otp
    session["registration_data"] = {
        "name": name,
        "email": email,
        "phone": phone,
        "password": password,
    }
    session["otp_expiry"] = (datetime.now() + timedelta(minutes=5)).timestamp()

    # Dispatch email in background thread (non-blocking)
    try:
      send_otp_email(email, otp)
    except Exception as e:
      print("OTP EMAIL ERROR:", repr(e))
      session.pop("registration_otp", None)
      session.pop("registration_data", None)
      session.pop("otp_expiry", None)
      flash("Unable to send verification email. Please try again.", "error")
      return redirect(url_for("register"))

    flash("A 6-digit verification code has been sent to your email.", "success")
    # Redirects immediately (<150ms) to /verify
    return redirect(url_for("verify"))

  return render_template("auth/register.html")


@app.route("/verify", methods=["GET", "POST"])
def verify():

  if "registration_otp" not in session:
    flash("No verification request found. Please register again.", "error")
    return redirect(url_for("register"))

  if request.method == "POST":

    entered_otp = request.form.get("otp", "").strip()

    stored_otp = session.get("registration_otp")
    expiry = session.get("otp_expiry")
    registration_data = session.get("registration_data")

    if not stored_otp or not registration_data:
      flash("Verification session expired. Please register again.", "error")
      return redirect(url_for("register"))

    # Check OTP expiry
    if not expiry or datetime.now().timestamp() > expiry:

      session.pop("registration_otp", None)
      session.pop("registration_data", None)
      session.pop("otp_expiry", None)

      flash("OTP has expired. Please register again.", "error")
      return redirect(url_for("register"))

    # Check OTP
    if entered_otp != stored_otp:

      flash("Invalid OTP. Please try again.", "error")
      return redirect(url_for("verify"))

    # Create user after successful verification
    password_hash = generate_password_hash(registration_data["password"])

    user = {
        "name": registration_data["name"],
        "email": registration_data["email"],
        "phone": registration_data["phone"],
        "password": password_hash,
        "verified": True,
    }

    result = users_collection.insert_one(user)

    print("USER VERIFIED AND CREATED")
    print("USER ID:", result.inserted_id)
    print("EMAIL:", registration_data["email"])

    # Clear temporary registration data
    session.pop("registration_otp", None)
    session.pop("registration_data", None)
    session.pop("otp_expiry", None)

    flash("Email verified successfully! You can now login.", "success")

    return redirect(url_for("login"))

  return render_template("auth/verify.html")


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

    from_city = request.form.get("from", "").strip()
    to_city = request.form.get("to", "").strip()
    departure = request.form.get("departure", "").strip()
    passengers = request.form.get("passengers", "1")

    print("FROM:", from_city)
    print("TO:", to_city)
    print("DATE:", departure)
    print("PASSENGERS:", passengers)

    # --------------------------------
    # 1. SEARCH EXACT DATE
    # --------------------------------

    route_flights = list(
        flights_collection.find({
            "from": {"$regex": f"^{from_city}$", "$options": "i"},
            "to": {"$regex": f"^{to_city}$", "$options": "i"},
        })
        .sort("flight_date", 1)
        .sort("departure", 1)
    )

    selected_date = None

    try:
      selected_date = datetime.strptime(departure, "%Y-%m-%d").date()
    except ValueError:
      selected_date = None

    flights = []

    for flight in route_flights:
      flight_date = flight.get("flight_date")

      if flight_date == departure:
        flights.append(flight)

    print("SEARCH DATE:", departure)
    print("FLIGHTS FOUND:", len(flights))

    # --------------------------------
    # 2. IF NO FLIGHT, SEARCH OTHER DATES
    # --------------------------------

    alternative_dates = False

    if len(flights) == 0:

      print("NO FLIGHTS ON SELECTED DATE")
      print("SEARCHING ALTERNATIVE DATES...")

      alternative_flights = []

      for flight in route_flights:
        flight_date = flight.get("flight_date")

        try:
          if (
              selected_date is not None
              and flight_date
              and datetime.strptime(flight_date, "%Y-%m-%d").date()
              > selected_date
          ):
            alternative_flights.append(flight)
        except ValueError:
          continue

      alternative_flights = alternative_flights[:10]

      if alternative_flights:
        flights = alternative_flights
        alternative_dates = True

      print("ALTERNATIVE FLIGHTS FOUND:", len(alternative_flights))

    # --------------------------------
    # 3. PRINT RESULTS
    # --------------------------------

    for flight in flights:
      print(
          flight["flight_number"],
          "|",
          flight.get("flight_date"),
          "|",
          flight["from"],
          "→",
          flight["to"],
      )

    return render_template(
        "flights/results.html",
        flights=flights,
        from_city=from_city,
        to_city=to_city,
        departure=departure,
        passengers=passengers,
        alternative_dates=alternative_dates,
    )

  return redirect(url_for("home"))


@app.route("/flight/<flight_id>")
def flight_details(flight_id):

  if "user_id" not in session:
    return redirect(url_for("login"))

  try:
    flight = flights_collection.find_one({"_id": ObjectId(flight_id)})
  except Exception:
    flight = None

  if not flight:
    flash("Flight not found.", "error")
    return redirect(url_for("home"))

  return render_template("flights/flight_details.html", flight=flight)


@app.route("/seat-selection/<flight_id>", methods=["GET", "POST"])
def seat_selection(flight_id):

  if "user_id" not in session:
    return redirect(url_for("login"))

  try:
    flight = flights_collection.find_one({"_id": ObjectId(flight_id)})
  except Exception:
    flight = None

  if not flight:
    flash("Flight not found.", "error")
    return redirect(url_for("home"))

  # Get seats already booked for this flight
  booked_seats = bookings_collection.find(
      {"flight_id": flight["_id"], "booking_status": {"$ne": "CANCELLED"}}
  )

  booked_seats = [
      booking["seat"] for booking in booked_seats if booking.get("seat")
  ]

  if request.method == "POST":

    selected_seat = request.form.get("seat")

    if not selected_seat:
      flash("Please select a seat.", "error")
      return redirect(url_for("seat_selection", flight_id=flight_id))

    # Check if selected seat is already booked
    if selected_seat in booked_seats:
      flash(
          f"Seat {selected_seat} is already booked. Please select another seat.",
          "error",
      )

      return redirect(url_for("seat_selection", flight_id=flight_id))

    session["selected_flight_id"] = flight_id
    session["selected_seat"] = selected_seat

    return redirect(url_for("passenger_details"))

  return render_template(
      "flights/seat_selection.html", flight=flight, booked_seats=booked_seats
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
    flight = flights_collection.find_one({"_id": ObjectId(flight_id)})
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
        "dob": passenger_dob,
    }

    return redirect(url_for("booking_review"))

  return render_template(
      "booking/passenger_details.html",
      flight=flight,
      selected_seat=selected_seat,
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
    flight = flights_collection.find_one({"_id": ObjectId(flight_id)})
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
      "booking/review.html",
      flight=flight,
      passenger=passenger,
      selected_seat=selected_seat,
      base_fare=base_fare,
      taxes=taxes,
      total=total,
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
    flight = flights_collection.find_one({"_id": ObjectId(flight_id)})
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
    # Prevent duplicate payment submission
    if session.get("payment_completed"):
      return redirect(url_for("booking_confirmation"))

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
        "booking_status": "CONFIRMED",
    })

    if existing_booking:

      flash(
          f"Seat {selected_seat} has already been booked. Please select another"
          " seat.",
          "error",
      )

      return redirect(
          url_for("seat_selection", flight_id=str(flight["_id"]))
      )

    # -----------------------------------
    # GENERATE PNR
    # -----------------------------------

    import string

    pnr = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

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
        "booking_status": "CONFIRMED",
    }

    # -----------------------------------
    # INSERT BOOKING
    # -----------------------------------

    result = bookings_collection.insert_one(booking)

    # -----------------------------------
    # REDUCE AVAILABLE SEATS
    # -----------------------------------

    flights_collection.update_one(
        {"_id": flight["_id"], "available_seats": {"$gt": 0}},
        {"$inc": {"available_seats": -1}},
    )

    # -----------------------------------
    # SAVE BOOKING IN SESSION
    # -----------------------------------

    session["booking_id"] = str(result.inserted_id)
    session["pnr"] = pnr
    session["payment_completed"] = True

    # -----------------------------------
    # GO TO CONFIRMATION
    # -----------------------------------

    return redirect(url_for("booking_confirmation"))

  return render_template(
      "booking/payment.html",
      flight=flight,
      selected_seat=selected_seat,
      passenger=passenger,
      base_fare=base_fare,
      taxes=taxes,
      total=total,
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
    booking = bookings_collection.find_one({"_id": ObjectId(booking_id)})
  except Exception:
    booking = None

  if not booking:
    flash("Booking not found.", "error")
    return redirect(url_for("home"))

  # Create QR code data
  qr_data = f"""
SkyBook Flight Ticket

PNR: {booking['pnr']}
Flight: {booking['flight_number']}
Date: {booking.get('flight_date', '')}
From: {booking['from']} ({booking['from_code']})
To: {booking['to']} ({booking['to_code']})
Departure: {booking['departure']}
Arrival: {booking['arrival']}
Passenger: {booking['passenger']['name']}
Seat: {booking['seat']}
Status: {booking['booking_status']}
"""

  # Generate QR code
  qr = qrcode.QRCode(version=1, box_size=4, border=2)

  qr.add_data(qr_data)
  qr.make(fit=True)

  qr_image = qr.make_image()

  # Resize QR code to exactly 50 × 50 pixels
  qr_image = qr_image.resize((50, 50), Image.Resampling.LANCZOS)

  buffer = io.BytesIO()
  qr_image.save(buffer, format="PNG")

  qr_code = base64.b64encode(buffer.getvalue()).decode("utf-8")

  return render_template(
      "booking/confirmation.html", booking=booking, qr_code=qr_code
  )


@app.route("/ticket/<booking_id>")
def ticket(booking_id):

  if "user_id" not in session:
    return redirect(url_for("login"))

  try:
    booking = bookings_collection.find_one({
        "_id": ObjectId(booking_id),
        "user_id": session["user_id"],
    })
  except Exception:
    booking = None

  if not booking:
    flash("Ticket not found.", "error")
    return redirect(url_for("booking_history"))

  # Create QR code data
  qr_data = f"""
SkyBook Flight Ticket

PNR: {booking['pnr']}
Flight: {booking['flight_number']}
Date: {booking.get('flight_date', '')}
From: {booking['from']} ({booking['from_code']})
To: {booking['to']} ({booking['to_code']})
Departure: {booking['departure']}
Arrival: {booking['arrival']}
Passenger: {booking['passenger']['name']}
Seat: {booking['seat']}
Status: {booking['booking_status']}
"""

  # Generate QR code
  qr = qrcode.QRCode(version=1, box_size=4, border=2)

  qr.add_data(qr_data)
  qr.make(fit=True)

  qr_image = qr.make_image()

  # Convert QR image to Base64
  buffer = io.BytesIO()
  qr_image.save(buffer, format="PNG")

  qr_code = base64.b64encode(buffer.getvalue()).decode("utf-8")

  # Add formatted date if needed
  if booking.get("flight_date"):
    try:
      date_obj = datetime.strptime(booking["flight_date"], "%Y-%m-%d")
      booking["formatted_date"] = date_obj.strftime("%d %B %Y")
    except ValueError:
      booking["formatted_date"] = booking["flight_date"]
  else:
    booking["formatted_date"] = "Date unavailable"

  return render_template(
      "booking/confirmation.html", booking=booking, qr_code=qr_code
  )


@app.route("/download-ticket/<booking_id>")
def download_ticket(booking_id):

  if "user_id" not in session:
    return redirect(url_for("login"))

  try:
    booking = bookings_collection.find_one({
        "_id": ObjectId(booking_id),
        "user_id": session["user_id"],
    })
  except Exception:
    booking = None

  if not booking:
    flash("Ticket not found.", "error")
    return redirect(url_for("booking_history"))

  buffer = io.BytesIO()

  pdf = canvas.Canvas(buffer, pagesize=(595, 842))

  width = 595
  height = 842

  # ==========================================
  # HEADER
  # ==========================================

  pdf.setFillColorRGB(0.04, 0.05, 0.08)
  pdf.rect(0, 0, width, height, fill=1, stroke=0)

  pdf.setFillColorRGB(1, 1, 1)
  pdf.setFont("Helvetica-Bold", 25)
  pdf.drawString(45, 790, "SKYBOOK")

  pdf.setFont("Helvetica", 9)
  pdf.setFillColorRGB(0.65, 0.68, 0.72)
  pdf.drawString(47, 773, "YOUR JOURNEY. OUR PRIORITY.")

  # Status
  pdf.setFillColorRGB(0.15, 0.75, 0.45)
  pdf.roundRect(430, 775, 115, 25, 12, fill=1, stroke=0)

  pdf.setFillColorRGB(1, 1, 1)
  pdf.setFont("Helvetica-Bold", 9)
  pdf.drawCentredString(487, 784, booking["booking_status"])

  # ==========================================
  # MAIN TICKET
  # ==========================================

  pdf.setFillColorRGB(0.98, 0.98, 0.98)
  pdf.roundRect(35, 175, 525, 565, 18, fill=1, stroke=0)

  # ==========================================
  # FLIGHT HEADER
  # ==========================================

  pdf.setFillColorRGB(0.08, 0.09, 0.13)
  pdf.setFont("Helvetica-Bold", 16)

  pdf.drawString(60, 700, booking["flight_number"])

  pdf.setFont("Helvetica", 10)
  pdf.setFillColorRGB(0.40, 0.42, 0.46)

  pdf.drawString(60, 682, booking["airline"])

  pdf.drawRightString(535, 700, booking.get("flight_date", ""))

  # Divider
  pdf.setStrokeColorRGB(0.85, 0.85, 0.87)
  pdf.line(60, 660, 535, 660)

  # ==========================================
  # ROUTE
  # ==========================================

  pdf.setFillColorRGB(0.08, 0.09, 0.13)

  # FROM
  pdf.setFont("Helvetica-Bold", 30)
  pdf.drawString(65, 610, booking["from_code"])

  pdf.setFont("Helvetica-Bold", 17)
  pdf.drawString(65, 580, booking["departure"])

  pdf.setFont("Helvetica", 9)
  pdf.setFillColorRGB(0.40, 0.42, 0.46)

  pdf.drawString(65, 562, booking["from"])

  # Arrow
  pdf.setFillColorRGB(0.20, 0.21, 0.25)
  pdf.setFont("Helvetica-Bold", 20)

  pdf.drawCentredString(297, 595, "--------->")

  # TO
  pdf.setFillColorRGB(0.08, 0.09, 0.13)

  pdf.setFont("Helvetica-Bold", 30)
  pdf.drawRightString(530, 610, booking["to_code"])

  pdf.setFont("Helvetica-Bold", 17)
  pdf.drawRightString(530, 580, booking["arrival"])

  pdf.setFont("Helvetica", 9)
  pdf.setFillColorRGB(0.40, 0.42, 0.46)

  pdf.drawRightString(530, 562, booking["to"])

  # ==========================================
  # PASSENGER SECTION
  # ==========================================

  pdf.setStrokeColorRGB(0.85, 0.85, 0.87)
  pdf.line(60, 530, 535, 530)

  pdf.setFillColorRGB(0.40, 0.42, 0.46)
  pdf.setFont("Helvetica-Bold", 8)

  pdf.drawString(65, 505, "PASSENGER")
  pdf.drawString(300, 505, "SEAT")

  pdf.setFillColorRGB(0.08, 0.09, 0.13)
  pdf.setFont("Helvetica-Bold", 13)

  pdf.drawString(65, 483, booking["passenger"]["name"])

  pdf.drawString(300, 483, booking["seat"])

  # ==========================================
  # BOOKING REFERENCE
  # ==========================================

  pdf.setFillColorRGB(0.40, 0.42, 0.46)
  pdf.setFont("Helvetica-Bold", 8)

  pdf.drawString(65, 445, "BOOKING REFERENCE")

  pdf.setFillColorRGB(0.08, 0.09, 0.13)
  pdf.setFont("Helvetica-Bold", 18)

  pdf.drawString(65, 420, booking["pnr"])

  # ==========================================
  # PAYMENT
  # ==========================================

  pdf.setFillColorRGB(0.40, 0.42, 0.46)
  pdf.setFont("Helvetica-Bold", 8)

  pdf.drawString(300, 445, "PAYMENT")

  pdf.setFillColorRGB(0.08, 0.09, 0.13)
  pdf.setFont("Helvetica-Bold", 11)

  pdf.drawString(300, 420, booking["payment_status"])

  # ==========================================
  # FARE
  # ==========================================

  pdf.setStrokeColorRGB(0.85, 0.85, 0.87)
  pdf.line(60, 390, 535, 390)

  pdf.setFillColorRGB(0.40, 0.42, 0.46)
  pdf.setFont("Helvetica", 9)

  pdf.drawString(65, 365, "Base Fare")

  pdf.drawRightString(530, 365, f"Rs. {booking['base_fare']:,}")

  pdf.drawString(65, 342, "Taxes & Fees")

  pdf.drawRightString(530, 342, f"Rs. {booking['taxes']:,}")

  pdf.setStrokeColorRGB(0.85, 0.85, 0.87)
  pdf.line(65, 325, 530, 325)

  pdf.setFillColorRGB(0.08, 0.09, 0.13)
  pdf.setFont("Helvetica-Bold", 14)

  pdf.drawString(65, 298, "TOTAL PAID")

  pdf.drawRightString(530, 298, f"Rs. {booking['total']:,}")

  # ==========================================
  # FOOTER
  # ==========================================

  pdf.setFillColorRGB(0.40, 0.42, 0.46)
  pdf.setFont("Helvetica", 8)

  pdf.drawCentredString(
      297, 210, "Please carry a valid government ID while travelling."
  )

  pdf.drawCentredString(297, 195, "Thank you for flying with SkyBook.")

  pdf.setFillColorRGB(1, 1, 1)
  pdf.setFont("Helvetica-Bold", 9)

  pdf.drawCentredString(297, 135, "SKYBOOK • DIGITAL FLIGHT TICKET")

  pdf.save()

  buffer.seek(0)

  return send_file(
      buffer,
      as_attachment=True,
      download_name=f"SkyBook_Ticket_{booking['pnr']}.pdf",
      mimetype="application/pdf",
  )


@app.route("/booking-history")
def booking_history():

  if "user_id" not in session:
    return redirect(url_for("login"))

  bookings = list(
      bookings_collection.find({"user_id": session["user_id"]}).sort("_id", -1)
  )

  upcoming = []
  completed = []
  cancelled = []

  today = datetime.now().strftime("%Y-%m-%d")

  for booking in bookings:

    status = booking.get("booking_status", "CONFIRMED")

    # -----------------------------------
    # CANCELLED BOOKINGS
    # -----------------------------------

    if status == "CANCELLED":
      cancelled.append(booking)
      continue

    # -----------------------------------
    # GET FLIGHT DATE
    # -----------------------------------

    flight_date = booking.get("flight_date")

    if not flight_date:
      flight = flights_collection.find_one({"_id": booking["flight_id"]})
      if flight:
        flight_date = flight.get("flight_date")

    # -----------------------------------
    # UPCOMING / COMPLETED
    # -----------------------------------

    if flight_date:
      if flight_date < today:
        completed.append(booking)
      else:
        upcoming.append(booking)
    else:
      upcoming.append(booking)

  # -----------------------------------
  # FORMAT DATES
  # -----------------------------------

  for booking in upcoming + completed + cancelled:
    if booking.get("flight_date"):
      try:
        date_obj = datetime.strptime(booking["flight_date"], "%Y-%m-%d")
        booking["formatted_date"] = date_obj.strftime("%d %B %Y")
      except ValueError:
        booking["formatted_date"] = booking["flight_date"]
    else:
      booking["formatted_date"] = "Date unavailable"

  return render_template(
      "profile/booking_history.html",
      upcoming=upcoming,
      completed=completed,
      cancelled=cancelled,
  )


@app.route("/my-bookings")
def my_bookings():

  if "user_id" not in session:
    return redirect(url_for("login"))

  bookings = list(
      bookings_collection.find({"user_id": session["user_id"]}).sort("_id", -1)
  )

  upcoming = []
  today = datetime.now().strftime("%Y-%m-%d")

  for booking in bookings:

    status = booking.get("booking_status", "CONFIRMED")

    # Skip cancelled bookings
    if status == "CANCELLED":
      continue

    flight_date = booking.get("flight_date")

    if not flight_date:
      flight = flights_collection.find_one({"_id": booking["flight_id"]})
      if flight:
        flight_date = flight.get("flight_date")

    if flight_date and flight_date >= today:
      upcoming.append(booking)

  # Format dates
  for booking in upcoming:
    if booking.get("flight_date"):
      try:
        date_obj = datetime.strptime(booking["flight_date"], "%Y-%m-%d")
        booking["formatted_date"] = date_obj.strftime("%d %B %Y")
      except ValueError:
        booking["formatted_date"] = booking["flight_date"]
    else:
      booking["formatted_date"] = "Date unavailable"

  return render_template("profile/my_bookings.html", bookings=upcoming)


@app.route("/profile")
def profile():

  if "user_id" not in session:
    return redirect(url_for("login"))

  try:
    user = users_collection.find_one({"_id": ObjectId(session["user_id"])})
  except Exception:
    user = None

  if not user:
    session.clear()
    flash("Your account could not be found.", "error")
    return redirect(url_for("login"))

  booking_count = bookings_collection.count_documents(
      {"user_id": session["user_id"]}
  )

  return render_template(
      "profile/profile.html", user=user, booking_count=booking_count
  )


@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

  if "user_id" not in session:
    return redirect(url_for("login"))

  try:
    user = users_collection.find_one({"_id": ObjectId(session["user_id"])})
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
        {"_id": ObjectId(session["user_id"])},
        {"$set": {"name": name, "phone": phone}},
    )

    # Update current session
    session["user_name"] = name

    flash("Profile updated successfully!", "success")

    return redirect(url_for("profile"))

  return render_template("profile/edit_profile.html", user=user)


@app.route("/cancel-booking/<booking_id>", methods=["POST"])
def cancel_booking(booking_id):

  if "user_id" not in session:
    return redirect(url_for("login"))

  try:
    booking = bookings_collection.find_one({
        "_id": ObjectId(booking_id),
        "user_id": session["user_id"],
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
      {"_id": booking["_id"]}, {"$set": {"booking_status": "CANCELLED"}}
  )

  flights_collection.update_one(
      {"_id": booking["flight_id"]}, {"$inc": {"available_seats": 1}}
  )

  flash(
      f"Booking {booking['pnr']} has been cancelled successfully.", "success"
  )

  return redirect(url_for("booking_history"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

  print("FORGOT PASSWORD ROUTE HIT")
  print("METHOD:", request.method)
  print("SESSION:", dict(session))

  if request.method == "POST":

    email = request.form.get("email", "").strip().lower()

    if not email:
      flash("Please enter your email address.", "error")
      return redirect(url_for("forgot_password"))

    user = users_collection.find_one({"email": email})

    if not user:
      flash("No account found with this email address.", "error")
      return redirect(url_for("forgot_password"))

    # Generate 6-digit reset OTP
    otp = str(random.randint(100000, 999999))

    session["reset_otp"] = otp
    session["reset_email"] = email
    session["reset_otp_expiry"] = (
        datetime.now() + timedelta(minutes=5)
    ).timestamp()

    from utils.email import send_reset_otp_email

    try:
      send_reset_otp_email(email, otp)
    except Exception as e:
      print("RESET OTP EMAIL ERROR:", e)

      session.pop("reset_otp", None)
      session.pop("reset_email", None)
      session.pop("reset_otp_expiry", None)

      flash("Unable to send verification email. Please try again.", "error")
      return redirect(url_for("forgot_password"))

    flash("Password reset OTP sent to your email.", "success")
    return redirect(url_for("reset_password"))

  return render_template("auth/forgot_password.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():

  if "reset_otp" not in session or "reset_email" not in session:
    flash("No password reset request found. Please try again.", "error")
    return redirect(url_for("forgot_password"))

  if request.method == "POST":

    entered_otp = request.form.get("otp", "").strip()
    new_password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    stored_otp = session.get("reset_otp")
    expiry = session.get("reset_otp_expiry")
    email = session.get("reset_email")

    # Check OTP expiry
    if not expiry or datetime.now().timestamp() > expiry:
      session.pop("reset_otp", None)
      session.pop("reset_email", None)
      session.pop("reset_otp_expiry", None)

      flash("Reset OTP has expired. Please request a new one.", "error")
      return redirect(url_for("forgot_password"))

    # Check OTP
    if entered_otp != stored_otp:
      flash("Invalid OTP. Please try again.", "error")
      return redirect(url_for("reset_password"))

    # Check password length
    if len(new_password) < 6:
      flash("Password must contain at least 6 characters.", "error")
      return redirect(url_for("reset_password"))

    # Check password confirmation
    if new_password != confirm_password:
      flash("Passwords do not match.", "error")
      return redirect(url_for("reset_password"))

    # Hash the new password
    password_hash = generate_password_hash(new_password)

    # Update password in MongoDB
    users_collection.update_one(
        {"email": email}, {"$set": {"password": password_hash}}
    )

    # Clear reset session
    session.pop("reset_otp", None)
    session.pop("reset_email", None)
    session.pop("reset_otp_expiry", None)

    flash("Password reset successfully! You can now login.", "success")
    return redirect(url_for("login"))

  return render_template("auth/reset_password.html")


@app.route("/change-password", methods=["GET", "POST"])
def change_password():

  if "user_id" not in session:
    return redirect(url_for("login"))

  try:
    user = users_collection.find_one({"_id": ObjectId(session["user_id"])})
  except Exception:
    user = None

  if not user:
    session.clear()
    flash("Your account could not be found.", "error")
    return redirect(url_for("login"))

  if request.method == "POST":

    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Check current password
    if not check_password_hash(user["password"], current_password):
      flash("Current password is incorrect.", "error")
      return redirect(url_for("change_password"))

    # Check password length
    if len(new_password) < 6:
      flash("New password must contain at least 6 characters.", "error")
      return redirect(url_for("change_password"))

    # Check confirmation
    if new_password != confirm_password:
      flash("New passwords do not match.", "error")
      return redirect(url_for("change_password"))

    # Prevent same password
    if check_password_hash(user["password"], new_password):
      flash(
          "New password must be different from your current password.", "error"
      )
      return redirect(url_for("change_password"))

    # Hash new password
    new_password_hash = generate_password_hash(new_password)

    # Update MongoDB
    users_collection.update_one(
        {"_id": ObjectId(session["user_id"])},
        {"$set": {"password": new_password_hash}},
    )

    flash("Password changed successfully!", "success")
    return redirect(url_for("profile"))

  return render_template("profile/change_password.html")


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)