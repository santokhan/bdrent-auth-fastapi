import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.collection import Collection
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


load_dotenv()


class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        """Establishes a connection to the MongoDB database using environment variables."""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            db_name = os.getenv("DB_NAME")

            if not mongo_uri:
                raise EnvironmentError(
                    "MONGO_URI is not found in environment variables."
                )
            if not db_name:
                raise EnvironmentError("DB_NAME is not found in environment variables.")

            self.client = AsyncIOMotorClient(mongo_uri)
            self.db = self.client[db_name]
            print(f"Connected to MongoDB: {db_name}")

        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")

    async def disconnect(self):
        """Closes the MongoDB connection."""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB.")


mongo = MongoDB()


async def get_collection(name: str = "") -> Collection:
    collection = mongo.db[name]
    return collection


SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
