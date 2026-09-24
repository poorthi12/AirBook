from database.db import flights_collection
from datetime import date, timedelta


# ==========================================
# CITIES
# ==========================================

cities = [
    {
        "name": "Bengaluru",
        "code": "BLR"
    },
    {
        "name": "Mangalore",
        "code": "IXE"
    },
    {
        "name": "Delhi",
        "code": "DEL"
    },
    {
        "name": "Mumbai",
        "code": "BOM"
    },
    {
        "name": "Hyderabad",
        "code": "HYD"
    },
    {
        "name": "Chennai",
        "code": "MAA"
    },
    {
        "name": "Kolkata",
        "code": "CCU"
    },
    {
        "name": "Goa",
        "code": "GOI"
    },
    {
        "name": "Kochi",
        "code": "COK"
    },
    {
        "name": "Pune",
        "code": "PNQ"
    },
    {
        "name": "Ahmedabad",
        "code": "AMD"
    },
    {
        "name": "Jaipur",
        "code": "JAI"
    }
]


# ==========================================
# APPROXIMATE FLIGHT DATA
# ==========================================

route_data = {

    ("BLR", "IXE"): ("1h 00m", 2499),
    ("BLR", "DEL"): ("2h 50m", 5499),
    ("BLR", "BOM"): ("1h 50m", 4299),
    ("BLR", "HYD"): ("1h 20m", 2999),
    ("BLR", "MAA"): ("1h 05m", 2799),
    ("BLR", "CCU"): ("2h 30m", 4999),
    ("BLR", "GOI"): ("1h 05m", 3199),
    ("BLR", "COK"): ("1h 10m", 2899),
    ("BLR", "PNQ"): ("1h 30m", 3499),
    ("BLR", "AMD"): ("2h 10m", 4599),
    ("BLR", "JAI"): ("2h 35m", 4999),

    ("IXE", "DEL"): ("2h 50m", 5999),
    ("IXE", "BOM"): ("1h 35m", 3799),
    ("IXE", "HYD"): ("1h 30m", 3299),
    ("IXE", "MAA"): ("1h 20m", 3199),
    ("IXE", "CCU"): ("2h 50m", 5499),
    ("IXE", "GOI"): ("1h 00m", 2799),
    ("IXE", "COK"): ("1h 05m", 2699),
    ("IXE", "PNQ"): ("1h 35m", 3699),
    ("IXE", "AMD"): ("2h 10m", 4599),
    ("IXE", "JAI"): ("2h 45m", 5199),

    ("DEL", "BOM"): ("2h 10m", 4999),
    ("DEL", "HYD"): ("2h 10m", 4599),
    ("DEL", "MAA"): ("2h 45m", 5299),
    ("DEL", "CCU"): ("2h 15m", 4799),
    ("DEL", "GOI"): ("2h 40m", 5199),
    ("DEL", "COK"): ("3h 10m", 5999),
    ("DEL", "PNQ"): ("2h 00m", 4699),
    ("DEL", "AMD"): ("1h 45m", 4299),
    ("DEL", "JAI"): ("1h 00m", 2999),

    ("BOM", "HYD"): ("1h 30m", 3299),
    ("BOM", "MAA"): ("1h 45m", 3799),
    ("BOM", "CCU"): ("2h 40m", 4999),
    ("BOM", "GOI"): ("1h 05m", 2799),
    ("BOM", "COK"): ("1h 45m", 3499),
    ("BOM", "PNQ"): ("1h 10m", 2499),
    ("BOM", "AMD"): ("1h 15m", 2999),
    ("BOM", "JAI"): ("1h 50m", 3799),

    ("HYD", "MAA"): ("1h 15m", 2899),
    ("HYD", "CCU"): ("2h 00m", 3999),
    ("HYD", "GOI"): ("1h 20m", 2999),
    ("HYD", "COK"): ("1h 40m", 3499),
    ("HYD", "PNQ"): ("1h 25m", 3199),
    ("HYD", "AMD"): ("1h 50m", 3999),
    ("HYD", "JAI"): ("2h 10m", 4499),

    ("MAA", "CCU"): ("2h 25m", 4499),
    ("MAA", "GOI"): ("1h 25m", 2999),
    ("MAA", "COK"): ("1h 00m", 2599),
    ("MAA", "PNQ"): ("1h 40m", 3499),
    ("MAA", "AMD"): ("2h 20m", 4499),
    ("MAA", "JAI"): ("2h 40m", 4999),

    ("CCU", "GOI"): ("2h 50m", 5499),
    ("CCU", "COK"): ("3h 00m", 5999),
    ("CCU", "PNQ"): ("2h 35m", 4999),
    ("CCU", "AMD"): ("2h 30m", 4999),
    ("CCU", "JAI"): ("2h 20m", 4799),

    ("GOI", "COK"): ("1h 15m", 2899),
    ("GOI", "PNQ"): ("1h 05m", 2799),
    ("GOI", "AMD"): ("1h 45m", 3699),
    ("GOI", "JAI"): ("2h 20m", 4499),

    ("COK", "PNQ"): ("1h 50m", 3699),
    ("COK", "AMD"): ("2h 25m", 4599),
    ("COK", "JAI"): ("2h 55m", 5299),

    ("PNQ", "AMD"): ("1h 20m", 2999),
    ("PNQ", "JAI"): ("1h 55m", 3799),

    ("AMD", "JAI"): ("1h 30m", 3299)
}


# ==========================================
# TIMES
# ==========================================

departure_times = [
    "05:45",
    "07:30",
    "09:15",
    "11:00",
    "13:00",
    "15:15",
    "17:30",
    "19:15",
    "21:00"
]


# ==========================================
# HELPER FUNCTION
# ==========================================

def get_route_data(from_code, to_code):

    # Direct route
    if (from_code, to_code) in route_data:
        return route_data[(from_code, to_code)]

    # Reverse route
    if (to_code, from_code) in route_data:
        return route_data[(to_code, from_code)]

    return ("2h 00m", 3999)


# ==========================================
# GENERATE ALL DIRECTED ROUTES
# ==========================================

all_routes = []

for from_city in cities:

    for to_city in cities:

        if from_city["code"] == to_city["code"]:
            continue

        all_routes.append(
            {
                "from": from_city["name"],
                "from_code": from_city["code"],
                "to": to_city["name"],
                "to_code": to_city["code"]
            }
        )


# ==========================================
# GENERATE FLIGHTS
# ==========================================

flights = []

start_date = date(2026, 9, 23)
end_date = date(2026, 11, 22)

current_date = start_date

flight_number = 101
route_index = 0
time_index = 0


while current_date <= end_date:

    # --------------------------------------
    # Select routes for this day
    # --------------------------------------

    daily_routes = []

    # 12 flights per day
    # This allows the network to be covered
    # much more evenly.
    for i in range(12):

        route = all_routes[
            route_index % len(all_routes)
        ]

        daily_routes.append(route)

        route_index += 1


    # --------------------------------------
    # Create flights
    # --------------------------------------

    for route in daily_routes:

        from_code = route["from_code"]
        to_code = route["to_code"]

        duration, price = get_route_data(
            from_code,
            to_code
        )

        departure = departure_times[
            time_index % len(departure_times)
        ]

        # Simple arrival-time calculation
        # based on predefined duration.
        hour = int(departure.split(":")[0])
        minute = int(departure.split(":")[1])

        duration_parts = duration.replace("h", "").replace("m", "").split()

        # Extract numbers safely
        import re

        hours_match = re.search(r"(\d+)h", duration)
        minutes_match = re.search(r"(\d+)m", duration)

        flight_hours = (
            int(hours_match.group(1))
            if hours_match
            else 0
        )

        flight_minutes = (
            int(minutes_match.group(1))
            if minutes_match
            else 0
        )

        total_minutes = (
            hour * 60
            + minute
            + flight_hours * 60
            + flight_minutes
        )

        arrival_hour = (total_minutes // 60) % 24
        arrival_minute = total_minutes % 60

        arrival = (
            f"{arrival_hour:02d}:"
            f"{arrival_minute:02d}"
        )

        flight = {
            "flight_number": f"SK{flight_number}",
            "airline": "AirBook Airways",

            "from": route["from"],
            "from_code": from_code,

            "to": route["to"],
            "to_code": to_code,

            "flight_date": current_date.strftime(
                "%Y-%m-%d"
            ),

            "departure": departure,
            "arrival": arrival,

            "duration": duration,

            "price": price,

            "total_seats": 180,
            "available_seats": 180
        }

        flights.append(flight)

        flight_number += 1
        time_index += 1


    current_date += timedelta(days=1)


# ==========================================
# INSERT INTO MONGODB
# ==========================================
# ==========================================
# CLEAR OLD FLIGHTS
# ==========================================

flights_collection.delete_many({})

print("Old flight data deleted.")


# ==========================================
# INSERT NEW FLIGHTS
# ==========================================

result = flights_collection.insert_many(flights)


print("----------------------------------------")
print("AirBook flights inserted successfully!")
print("----------------------------------------")
print("Total flights:", len(result.inserted_ids))
print("Cities:", len(cities))
print("Direct routes:", len(all_routes))
print("Date range:", start_date, "to", end_date)
print("----------------------------------------")