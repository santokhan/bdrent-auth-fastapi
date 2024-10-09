from fastapi import APIRouter

router = APIRouter()


@router.get("/")  # Keep the forslash for root only not for others
async def root() -> dict:
    return {"message": "Welcome back Santo! to your Authenticaton API server."}
