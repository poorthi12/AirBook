from database.db import flights_collection


updates = {
    "SK101": "2026-09-25",
    "SK102": "2026-09-26",
    "SK103": "2026-09-27",
    "SK104": "2026-09-28",
    "SK105": "2026-09-29"
}


for flight_number, flight_date in updates.items():

    result = flights_collection.update_many(
        {
            "flight_number": flight_number
        },
        {
            "$set": {
                "flight_date": flight_date
            }
        }
    )

    print(
        flight_number,
        "→",
        flight_date,
        "| Updated:",
        result.modified_count
    )


print("\nFlight dates updated successfully!")