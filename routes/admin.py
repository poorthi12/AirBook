from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from database.db import users_collection, flights_collection, bookings_collection
from bson.objectid import ObjectId
from functools import wraps

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "admin_id" not in session:
            return redirect(url_for("admin.admin_login"))

        return function(*args, **kwargs)

    return decorated_function

@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = users_collection.find_one({
            "email": email,
            "role": "admin"
        })

        if not user:
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("admin.admin_login"))

        from werkzeug.security import check_password_hash

        if not check_password_hash(user["password"], password):
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("admin.admin_login"))

        # ADMIN SESSION
        session["admin_id"] = str(user["_id"])
        session["admin_name"] = user["name"]

        return redirect(url_for("admin.dashboard"))

    return render_template("admin/login.html")


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@admin_bp.route("/dashboard")
@admin_required
def dashboard():

    users_count = users_collection.count_documents({})

    flights_count = flights_collection.count_documents({})

    bookings_count = bookings_collection.count_documents({
        "booking_status": "CONFIRMED"
    })

    revenue_result = list(
        bookings_collection.aggregate([
            {
                "$match": {
                    "payment_status": "PAID",
                    "booking_status": "CONFIRMED"
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {
                        "$sum": "$total"
                    }
                }
            }
        ])
    )

    revenue = 0

    if revenue_result:
        revenue = revenue_result[0]["total"]

    return render_template(
        "admin/dashboard.html",
        users_count=users_count,
        flights_count=flights_count,
        bookings_count=bookings_count,
        revenue=revenue
    )
# ==========================================
# MANAGE FLIGHTS
# ==========================================

@admin_bp.route("/flights")
@admin_required
def manage_flights():



    flights = list(
        flights_collection.find().sort("flight_date", 1)
    )

    return render_template(
        "admin/flights.html",
        flights=flights
    )


# ==========================================
# ADD FLIGHT
# ==========================================

@admin_bp.route("/flights/add", methods=["GET", "POST"])
@admin_required
def add_flight():


    if request.method == "POST":

        flight = {
            "flight_number": request.form.get("flight_number", "").strip().upper(),
            "airline": request.form.get("airline", "").strip(),
            "from": request.form.get("from", "").strip(),
            "from_code": request.form.get("from_code", "").strip().upper(),
            "to": request.form.get("to", "").strip(),
            "to_code": request.form.get("to_code", "").strip().upper(),
            "flight_date": request.form.get("flight_date", ""),
            "departure": request.form.get("departure", ""),
            "arrival": request.form.get("arrival", ""),
            "price": int(request.form.get("price", 0)),
            "total_seats": 180,
            "available_seats": 180
        }

        flights_collection.insert_one(flight)

        flash("Flight added successfully!", "success")

        return redirect(url_for("admin.manage_flights"))

    return render_template("admin/add_flight.html")

# ==========================================
# EDIT FLIGHT
# ==========================================

@admin_bp.route("/flights/edit/<flight_id>", methods=["GET", "POST"])
@admin_required
def edit_flight(flight_id):

    try:
        flight = flights_collection.find_one({
            "_id": ObjectId(flight_id)
        })
    except Exception:
        flight = None

    if not flight:
        flash("Flight not found.", "error")
        return redirect(url_for("admin.manage_flights"))

    if request.method == "POST":

        updated_data = {
            "flight_number": request.form.get("flight_number", "").strip().upper(),
            "airline": request.form.get("airline", "").strip(),
            "from": request.form.get("from", "").strip(),
            "from_code": request.form.get("from_code", "").strip().upper(),
            "to": request.form.get("to", "").strip(),
            "to_code": request.form.get("to_code", "").strip().upper(),
            "flight_date": request.form.get("flight_date", ""),
            "departure": request.form.get("departure", ""),
            "arrival": request.form.get("arrival", ""),
            "price": int(request.form.get("price", 0))
        }

        flights_collection.update_one(
            {"_id": ObjectId(flight_id)},
            {"$set": updated_data}
        )

        flash("Flight updated successfully!", "success")

        return redirect(url_for("admin.manage_flights"))

    return render_template(
        "admin/edit_flight.html",
        flight=flight
    )

# ==========================================
# DELETE FLIGHT
# ==========================================

@admin_bp.route("/flights/delete/<flight_id>", methods=["POST"])
@admin_required
def delete_flight(flight_id):


    try:
        flights_collection.delete_one({
            "_id": ObjectId(flight_id)
        })

        flash("Flight deleted successfully.", "success")

    except Exception:
        flash("Unable to delete flight.", "error")

    return redirect(url_for("admin.manage_flights"))

# ==========================================
# MANAGE BOOKINGS
# ==========================================

@admin_bp.route("/bookings")
@admin_required
def manage_bookings():


    bookings = list(
        bookings_collection.find().sort("_id", -1)
    )

    return render_template(
        "admin/bookings.html",
        bookings=bookings
    )

@admin_bp.route("/users")
@admin_required
def manage_users():

    users = list(
        users_collection.find().sort("_id", -1)
    )

    return render_template(
        "admin/users.html",
        users=users
    )
@admin_bp.route("/bookings/cancel/<booking_id>", methods=["POST"])
@admin_required
def cancel_booking_admin(booking_id):

    try:
        booking = bookings_collection.find_one({
            "_id": ObjectId(booking_id)
        })
    except Exception:
        booking = None

    if not booking:
        flash("Booking not found.", "error")
        return redirect(url_for("admin.manage_bookings"))

    # Already cancelled
    if booking.get("booking_status") == "CANCELLED":
        flash("Booking is already cancelled.", "error")
        return redirect(url_for("admin.manage_bookings"))

    # Cancel booking
    bookings_collection.update_one(
        {"_id": ObjectId(booking_id)},
        {
            "$set": {
                "booking_status": "CANCELLED"
            }
        }
    )

    # Return the seat to the flight
    try:
        flights_collection.update_one(
            {"_id": ObjectId(booking["flight_id"])},
            {
                "$inc": {
                    "available_seats": 1
                }
            }
        )
    except Exception:
        pass

    flash(
        f"Booking {booking['pnr']} cancelled successfully.",
        "success"
    )

    return redirect(url_for("admin.manage_bookings"))
@admin_bp.route("/bookings/view/<booking_id>")
@admin_required
def view_booking(booking_id):

    try:
        booking = bookings_collection.find_one({
            "_id": ObjectId(booking_id)
        })
    except Exception:
        booking = None

    if not booking:
        flash("Booking not found.", "error")
        return redirect(url_for("admin.manage_bookings"))

    return render_template(
        "admin/booking_details.html",
        booking=booking
    )
@admin_bp.route("/logout")
def admin_logout():

    session.pop("admin_id", None)
    session.pop("admin_name", None)

    flash("Admin logged out successfully.", "success")

    return redirect(url_for("admin.admin_login"))