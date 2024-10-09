from fastapi import HTTPException, APIRouter, Header, Path, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from app.config import db
from .helper.bearer import get_bearer_token
from .helper.hash import verify_hash, make_hash
from .helper.schemas import AccessTokenResponse, TokenResponse
from .helper.models import ForgotModel, ResetModel, UserModel, TokenInputModel
from .helper.token import (
    create_access_token,
    create_refresh_token,
    decode,
    refresh_access_token,
)

router = APIRouter()

users_collection = db["users"]


@router.post("/register")
async def register(user: UserModel) -> dict:
    try:
        user.validate_phone_number()
        user.validate_password()

        filter = {}
        if user.email:
            filter["email"] = user.email
        if user.phone:
            filter["phone"] = user.phone

        existing_user = await users_collection.find_one(filter)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        users_collection.insert_one(
            {
                "email": user.email,
                "phone": user.phone,
                "password": make_hash(user.password),
                "verified": False,
            }
        )

        return {"message": "User registered successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(user: UserModel) -> TokenResponse:
    if not user.email and not user.phone:
        raise HTTPException(status_code=400, detail="Email or phone must be provided")
    try:
        filter = {}
        if user.email:
            filter["email"] = user.email
        if user.phone:
            filter["phone"] = user.phone
        db_user = await users_collection.find_one(filter)

        verify_hash(hash=db_user["password"], user_password=user.password)

        # Set to token
        user_data = {}
        for key in ["email", "phone"]:
            if user_data.get(key):
                db_user[key] = user_data.get(key)

        # Store to databaes that help on logout
        refresh_token = create_refresh_token(user_data)
        await users_collection.update_one(
            filter, {"$set": {"refresh_token": refresh_token}}
        )

        access_token = create_access_token(user_data)

        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/token")
async def token(token: TokenInputModel) -> AccessTokenResponse:
    doc = await users_collection.find_one({"refresh_token": token.refresh_token})
    if doc is None:
        raise HTTPException(status_code=400, detail="Invalid token")

    return {"access_token": refresh_access_token(token.refresh_token)}


@router.post("/logout")
async def logout(authorization: str = Header(None)) -> dict:
    print(authorization)
    bearer_token = get_bearer_token(authorization)
    user_data = decode(bearer_token)

    filter = {}
    for key in ["email", "phone"]:
        if user_data.get(key):
            filter[key] = user_data.get(key)

    await users_collection.update_one(filter, {"$unset": {"refresh_token": ""}})

    return {"message": "User logged out successfully"}


@router.post("/forgot")
async def forgot(referer: str = Header(default=None), user: ForgotModel = None):
    try:
        user.validate_phone_number()

        filter = {}
        if user.email:
            filter["email"] = user.email
        if user.phone:
            filter["phone"] = user.phone

        db_user = await users_collection.find_one(filter)

        # Set to token
        user_data = {}
        for key in ["email", "phone"]:
            if user_data.get(key):
                db_user[key] = user_data.get(key)

        reset_token = create_access_token(user_data)

        params = {"token": reset_token, "redirect": referer}
        query_string = "&".join(f"{key}={value}" for key, value in params.items())

        if user.callback:
            url = f"{user.callback}?{query_string}"
            return RedirectResponse(url=url, status_code=307)
        else:
            url = f"/api/v1/users/reset?{query_string}"
            # print(url)
            return RedirectResponse(url=url, status_code=307)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reset", response_class=HTMLResponse)
async def reset_form(token: str = Query(...)):
    with open("static/reset.html", "r", encoding="utf-8") as file:
        html_content = file.read()
        if html_content:
            return html_content


@router.post("/reset")
async def reset(reset: ResetModel):
    try:
        filter = {"$or": [{"email": reset.email}, {"phone": reset.phone}]}

        updated = await users_collection.update_one(
            filter, {"$set": {"password": make_hash(reset.password)}}
        )

        if updated is None:
            raise HTTPException(status_code=400, detail="Reset failed.")

        return {"message": "Password reset successful."}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
