from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1 import root
from app.api.v1.users import auth
from app.api.v1 import otp
from app.db import mongo
from app.utils.cors import allow_origins
from app.db import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    print("Starting up...")
    await mongo.connect()
    if mongo.db is None:
        raise RuntimeError("Failed to connect to the database.")
    print("MongoDB connection established")

    # Yield control to the app lifecycle
    yield

    # Shutdown: Disconnect MongoDB
    print("Shutting down...")
    await mongo.disconnect()
    print("MongoDB connection closed")


# Initialize the FastAPI app with a custom lifespan
app = FastAPI(title="Authentication", lifespan=lifespan)

# Create all tables
Base.metadata.create_all(bind=engine)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(root.router)
app.include_router(
    auth.router,
    tags=["auth"],
    prefix="/api/v1/auth",
)
app.include_router(
    otp.router,
    tags=["otp"],
    prefix="/api/v1/otp",
)
