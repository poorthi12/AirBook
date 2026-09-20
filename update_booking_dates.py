from database.db import bookings_collection, flights_collection

bookings = bookings_collection.find({})

updated = 0

for booking in bookings:

    flight = flights_collection.find_one({
        "_id": booking["flight_id"]
    })

    if flight and flight.get("flight_date"):

        bookings_collection.update_one(
            {
                "_id": booking["_id"]
            },
            {
                "$set": {
                    "flight_date": flight["flight_date"]
                }
            }
        )

        print(
            booking["pnr"],
            "→",
            flight["flight_date"]
        )

        updated += 1

print()
print("Bookings updated:", updated)