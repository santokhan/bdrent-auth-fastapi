from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from app.api.v1.users import auth
import os
from app.api.v1 import root
from app.api.v1.users import auth


def create_app():
    app = FastAPI(
        title="Authentication",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "*",
            "http://localhost:5174",
            "http://localhost:5173",
            "http://localhost:3000",
            "https://ssi-admin.netlify.app",
            "https://ssi-admin-v2.netlify.app",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(root.router)
    app.include_router(
        tags=["users"],
        prefix="/api/v1/users",
        router=auth.router,
    )

    return app


app = create_app()
