from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)

db = client["AirBook"]

users_collection = db["users"]
flights_collection = db["flights"]
bookings_collection = db["bookings"]


def test_connection():
    try:
        client.admin.command("ping")

        print("MongoDB connected successfully!")
        print("Database:", db.name)
        print("Users:", users_collection.count_documents({}))
        print("Flights:", flights_collection.count_documents({}))
        print("Bookings:", bookings_collection.count_documents({}))

        return True

    except Exception as e:
        print("MongoDB connection failed!")
        print(e)

        return False