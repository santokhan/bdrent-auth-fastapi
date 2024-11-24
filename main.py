from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1 import root
from app.api.v1.users import auth
from app.utils.cors import allow_origins


def create_app():
    app = FastAPI(
        title="Authentication",
    )

    app.mount("/static", StaticFiles(directory="static"), name="static")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(root.router)
    app.include_router(
        tags=["auth"],
        prefix="/api/v1/auth",
        router=auth.router,
    )

    return app


app = create_app()
