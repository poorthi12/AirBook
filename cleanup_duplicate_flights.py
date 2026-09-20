from database.db import flights_collection


flight_numbers = [
    "SK101",
    "SK102",
    "SK103",
    "SK104",
    "SK105"
]


for flight_number in flight_numbers:

    flights = list(
        flights_collection.find(
            {
                "flight_number": flight_number
            }
        ).sort("_id", 1)
    )

    print(
        flight_number,
        "found:",
        len(flights)
    )

    if len(flights) > 1:

        duplicate_ids = [
            flight["_id"]
            for flight in flights[1:]
        ]

        result = flights_collection.delete_many(
            {
                "_id": {
                    "$in": duplicate_ids
                }
            }
        )

        print(
            "Deleted duplicates:",
            result.deleted_count
        )


print("\nDuplicate cleanup completed.")

print(
    "Total flights:",
    flights_collection.count_documents({})
)