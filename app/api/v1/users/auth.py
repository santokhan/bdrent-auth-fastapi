from datetime import datetime
from bson import ObjectId
from fastapi import Depends, HTTPException, APIRouter, Header, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.config import db
from .helper.bearer import get_bearer_token
from .helper.hash import verify_hash, make_hash
from .helper.schemas import AccessTokenResponse, TokenResponse
from .helper.models import (
    ForgotModel,
    ResetModel,
    UserModel,
    TokenInputModel,
    UserResponse,
    UsersResponse,
)
from pymongo.errors import PyMongoError
from .helper.token import (
    create_access_token,
    create_refresh_token,
    decode,
    refresh_access_token,
)

router = APIRouter()

collection = db["users"]


@router.post("/register")
async def register(user: UserModel) -> dict:
    try:
        print(user)
        user.validate_phone_number()
        user.validate_password()

        filter = {}
        if user.phone:
            filter["phone"] = user.phone
        if user.email:
            filter["email"] = user.email

        existing_user = await collection.find_one(filter)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="User already exists",
            )

        collection.insert_one(
            {
                "email": user.email,
                "phone": user.phone,
                "password": make_hash(user.password),
                "verified": False,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
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
        db_user = await collection.find_one(filter)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        verify_hash(hash=db_user["password"], user_password=user.password)

        # Set to token
        user_data = {}
        for key in ["email", "phone"]:
            if db_user.get(key):
                user_data[key] = db_user.get(key)

        # Store to databaes that help on logout
        refresh_token = create_refresh_token(user_data)
        await collection.update_one(filter, {"$set": {"refresh_token": refresh_token}})

        access_token = create_access_token(user_data)
        print(user_data)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_data,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/token")
async def token(token: TokenInputModel) -> AccessTokenResponse:
    doc = await collection.find_one({"refresh_token": token.refresh_token})
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    return {"access_token": refresh_access_token(token.refresh_token)}


@router.post("/logout")
async def logout(header: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    access_token = get_bearer_token(header.credentials)

    user_data = decode(access_token)

    print(user_data)

    filter = {}
    for key in ["email", "phone"]:
        if user_data.get(key):
            filter[key] = user_data.get(key)

    await collection.update_one(filter, {"$unset": {"refresh_token": ""}})

    return {"message": "User logged out successfully"}


@router.post("/forgot")
async def forgot(
    request: Request, referer: str = Header(default=None), user: ForgotModel = None
):
    try:
        user.validate_phone_number()

        filter = {}
        if user.email:
            filter["email"] = user.email
        if user.phone:
            filter["phone"] = user.phone

        db_user = await collection.find_one(filter)

        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Not user found with the given email",
            )
        # Set to token
        user_data = {}
        for key in ["email", "phone"]:
            if user_data.get(key):
                db_user[key] = user_data.get(key)

        reset_token = create_access_token(user_data)

        full_url = f"{request.url.scheme}://{request.url.netloc}"
        params = {"token": reset_token, "redirect": referer}
        query_string = "&".join(f"{key}={value}" for key, value in params.items())

        if user.callback:
            url = f"{user.callback}?{query_string}"
        else:
            url = f"{full_url}/api/v1/users/reset?{query_string}"
            # print(url)
            # return RedirectResponse(url=url, status_code=307)

        return {"token": reset_token}

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

        updated = await collection.update_one(
            filter, {"$set": {"password": make_hash(reset.password)}}
        )

        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Reset failed."
            )

        return {"message": "Password reset successful."}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{id}", response_model=UserResponse)
async def user(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid 'id' provided")

    try:
        doc = await collection.find_one({"_id": ObjectId(id)})

        if doc is None:
            raise HTTPException(status_code=404, detail=f"Item with id {id} not found")

        return UserResponse(
            id=str(doc.get("_id")),
            email=doc.get("email"),
            phone=doc.get("phone"),
            verified=doc.get("verified"),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


VALID_SORT_FIELDS = ["created_at", "updated_at", "email", "name", "phone"]


@router.get("", response_model=UsersResponse)
async def users(
    sort_by: str = "created_at", sort_order: int = -1, skip: int = 0, limit: int = 10
):
    try:
        # Validate the sort_by field
        if sort_by not in VALID_SORT_FIELDS:
            raise ValueError(f"Invalid sort field: {sort_by}")

        # Validate the sort_order field
        if sort_order not in [1, -1]:
            raise ValueError("sort_order must be 1 (ascending) or -1 (descending)")

        filters = {}

        # Query the database with sorting, skipping, and limiting
        users = (
            await collection.find(filters)
            .sort(sort_by, sort_order)
            .skip(skip)
            .limit(limit)
            .to_list(length=None)
        )
        count = await collection.count_documents(filters)

        # If no users are found, return an empty list
        if not users:
            return {"users": []}

        # Using list comprehension to build the filtered response
        filtered = []

        for user in users:
            _id = user.get("_id", None)
            if _id is not None:
                filtered.append(
                    UserResponse(
                        id=str(_id),
                        email=user.get("email", None),
                        phone=user.get("phone", None),
                        verified=user.get("verified", False),
                        created_at=user.get("created_at"),
                        updated_at=user.get("updated_at"),
                    )
                )

        return {"list": filtered, "count": count}

    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.delete("/{id}")
async def delete(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid 'id' provided")

    try:
        result = await collection.delete_one({"_id": ObjectId(id)})

        # If no document was deleted, the id might not exist in the database
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"Item with id {id} not found")

        return {"message": "User has been deleted.", "id": id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
