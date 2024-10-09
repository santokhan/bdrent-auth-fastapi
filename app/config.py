import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()


# mongodb
def get_mongo_connection():
    """Establishes a connection to the MongoDB database using environment variables."""
    try:
        load_dotenv()  # Load environment variables from .env file

        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise EnvironmentError("MONGO_URI not found in environment variables.")

        db_name = os.getenv("DB_NAME")
        if not db_name:
            raise EnvironmentError("DB_NAME not found in environment variables.")

        client = AsyncIOMotorClient(mongo_uri)
        db = client[db_name]  # Use the database name from the environment variable

        return client, db

    except EnvironmentError as e:
        print(e)
        return None, None  # Return None if there is an error


client, db = get_mongo_connection()
if (
    client is not None and db is not None
):  # Compare with None instead of truthy evaluation
    print("MongoDB connection established.")
else:
    print("Failed to establish MongoDB connection.")
