from database.db import flights_collection


flights = [

    {
        "flight_number": "SK101",
        "airline": "SkyBook Airways",
        "from": "Bengaluru",
        "from_code": "BLR",
        "to": "Delhi",
        "to_code": "DEL",
        "flight_date": "2026-09-25",
        "departure": "06:30",
        "arrival": "09:20",
        "duration": "2h 50m",
        "price": 5499,
        "total_seats": 180,
        "available_seats": 180
    },

    {
        "flight_number": "SK102",
        "airline": "SkyBook Airways",
        "from": "Bengaluru",
        "from_code": "BLR",
        "to": "Mumbai",
        "to_code": "BOM",
        "flight_date": "2026-09-26",
        "departure": "10:15",
        "arrival": "12:05",
        "duration": "1h 50m",
        "price": 4299,
        "total_seats": 180,
        "available_seats": 180
    },

    {
        "flight_number": "SK103",
        "airline": "SkyBook Airways",
        "from": "Bengaluru",
        "from_code": "BLR",
        "to": "Hyderabad",
        "to_code": "HYD",
        "flight_date": "2026-09-27",
        "departure": "14:00",
        "arrival": "15:20",
        "duration": "1h 20m",
        "price": 2999,
        "total_seats": 180,
        "available_seats": 180
    },

    {
        "flight_number": "SK104",
        "airline": "SkyBook Airways",
        "from": "Delhi",
        "from_code": "DEL",
        "to": "Bengaluru",
        "to_code": "BLR",
        "flight_date": "2026-09-28",
        "departure": "17:30",
        "arrival": "20:20",
        "duration": "2h 50m",
        "price": 5799,
        "total_seats": 180,
        "available_seats": 180
    },

    {
        "flight_number": "SK105",
        "airline": "SkyBook Airways",
        "from": "Mumbai",
        "from_code": "BOM",
        "to": "Bengaluru",
        "to_code": "BLR",
        "flight_date": "2026-09-29",
        "departure": "19:15",
        "arrival": "21:05",
        "duration": "1h 50m",
        "price": 3999,
        "total_seats": 180,
        "available_seats": 180
    }

]


result = flights_collection.insert_many(flights)

print("Flights inserted successfully!")
print("Inserted:", len(result.inserted_ids))