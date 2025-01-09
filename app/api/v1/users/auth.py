from shutil import ExecError
from bson import ObjectId
from fastapi import (
    Body,
    Depends,
    HTTPException,
    APIRouter,
    Header,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from requests import Session
from app.api.v1 import sms
from app.db import get_collection
from app.models.users import User
from app.services.mail.sender import send_email, send_email_verification
from .helper.bearer import get_bearer_token
from .helper.hash import verify_hash, make_hash
from .helper.schemas import AccessTokenResponse, TokenResponse
from .helper.models import (
    ForgotModel,
    ResetModel,
    UserLogin,
    UserModel,
    TokenInputModel,
    UserResponse,
    UsersResponse,
    VerificationModel,
)
from pymongo.errors import PyMongoError
from .helper.token import (
    create_access_token,
    create_refresh_token,
    decode,
    refresh_access_token,
)
from app.api.v1.users.helper.token import decode
from pymongo.collection import Collection
from app.db import get_db
from app.crud.users import (
    create_user,
    read_user,
    read_user_by_identifier,
    read_users,
    update_user,
    delete_user,
)

router = APIRouter()


async def user_collection() -> Collection:
    collection = await get_collection("users")
    return collection


@router.post("/signup")
async def register(
    user: UserModel,
    user_db: Session = Depends(get_db),
) -> dict:
    try:
        user.validate_phone_number()
        user.validate_password()

        user_data = {
            "role": user.role,
            "email": user.email,
            "phone": user.phone,
            "username": user.username,
            "name": user.name,
            "password": make_hash(user.password),
        }

        await create_user(user_db, user_data)

        return {"message": "User registered successfully"}

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        raise HTTPException(status_code=500, detail=e)


def trimmed_user(db_user: User):
    return {
        "id": db_user.id,
        "role": db_user.role,
        "username": db_user.username,
        "name": db_user.name,
        "verified": db_user.verified,
        "created_at": str(db_user.created_at),
        "updated_at": str(db_user.updated_at),
    }


@router.post("/signin")
async def login(
    user: UserLogin,  # non default
    response: Response,  # non default
    user_db=Depends(get_db),  # default
) -> TokenResponse:
    try:
        identifier = None

        if user.username is not None:
            identifier = user.username
        elif user.phone is not None:
            identifier = user.phone
        elif user.email is not None:
            identifier = user.email

        db_user = await read_user_by_identifier(user_db, identifier)

        verify_hash(hash=db_user.password, user_password=user.password)

        user_data = trimmed_user(db_user)
        refresh_token = create_refresh_token(data=user_data)

        await update_user(user_db, db_user.id, {"refresh_token": refresh_token})

        access_token = create_access_token(user_data)

        # Set cookie to response for 1.domain and 2.user
        response.set_cookie(
            key="auth_token",
            value=access_token,
            domain=".bengalrent.xyz",  # Root domain
            path="/",  # Accessible everywhere
            secure=True,  # Only over HTTPS
            httponly=True,  # Prevent JS access
            samesite="None",  # Required for cross-subdomain
        )
        response.set_cookie(
            key="user",
            value=user_data,  # Public info
            domain=".bengalrent.xyz",
            path="/",
            secure=True,
            httponly=False,  # Allow JS access if necessary
            samesite="None",
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_data,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/token")
async def token(
    token: TokenInputModel,
    response: Response,  # non default
    user_db=Depends(get_db), # default
) -> AccessTokenResponse:
    decoded = decode(token.refresh_token)
    try:
        db_user = await read_user(user_db, decoded.get("id"))

        user_data = trimmed_user(db_user)
        
        access_token = create_access_token(user_data)

        # Set cookie to response for 1.domain and 2.user
        response.set_cookie(
            key="auth_token",
            value=access_token,
            domain=".bengalrent.xyz",  # Root domain
            path="/",  # Accessible everywhere
            secure=True,  # Only over HTTPS
            httponly=True,  # Prevent JS access
            samesite="None",  # Required for cross-subdomain
        )
        response.set_cookie(
            key="user",
            value=user_data,  # Public info
            domain=".bengalrent.xyz",
            path="/",
            secure=True,
            httponly=False,  # Allow JS access if necessary
            samesite="None",
        )

        return {"access_token": access_token}

    except ExecError as e:
        raise HTTPException(status_code=400, detail=e.strerror)


@router.post("/signout")
async def logout(
    header: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    user_db=Depends(get_db),
):
    access_token = get_bearer_token(header.credentials)

    user_data = decode(access_token)

    filter = {}
    for key in ["email", "phone"]:
        if user_data.get(key):
            filter[key] = user_data.get(key)

    await update_user(user_db, user_data.get("id"), {"refresh_token": ""})

    return {"message": "User logged out successfully"}


@router.post("/forgot")
async def forgot(
    request: Request,
    referer: str = Header(default=None),
    user: ForgotModel = Body(...),
    user_db=Depends(get_db),
):
    try:
        identifier = None

        if user.username is not None:
            identifier = user.username
        elif user.phone is not None:
            identifier = user.phone
        elif user.email is not None:
            identifier = user.email

        db_user = await read_user_by_identifier(user_db, identifier)

        if db_user.id is None:
            raise HTTPException(
                status_code=400, detail="To create token user id is required"
            )

        reset_token = create_access_token({"id": id})

        full_url = f"{request.url.scheme}://{request.url.netloc}"
        params = {"token": reset_token, "redirect": referer}
        query_string = "&".join(f"{key}={value}" for key, value in params.items())

        url_with_token = ""
        if user.callback is not None:
            url_with_token = f"{user.callback}?{query_string}"
        else:
            url_with_token = f"{full_url}/api/v1/users/reset?{query_string}"

        # Send reset link via SMS or Email
        if user.phone is not None:
            await sms.sms_sender(
                message=f"Bengal Rental \nTo reset your password, click the link: {url_with_token}",
                mobile_no=user.phone,
            )
        elif user.email:
            await send_email(reset_link=url_with_token, to_email=user.email)

        return {"message": "Password reset link has been sent.", "to": user}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reset", response_class=HTMLResponse)
async def reset_form(token: str = Query(...)):
    with open("static/reset.html", "r", encoding="utf-8") as file:
        html_content = file.read()
        if html_content:
            return html_content


@router.post("/reset")
async def reset(reset_model: ResetModel, user_db=Depends(get_db)):
    try:
        if reset_model.token is None or reset_model.password is None:
            raise HTTPException(
                status_code=400, detail="Token and Password are required"
            )

        decoded_user = decode(reset_model.token)

        id = decoded_user.get("id", None)

        filter = {}
        if id is not None:
            filter["_id"] = ObjectId(id)

        password = make_hash(reset_model.password)

        updated = await user_db.update_one(filter, {"$set": {"password": password}})

        if updated is None:
            raise HTTPException(status_code=422, detail="Reset failed.")

        return {"message": "Password reset successful."}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify")
async def get_verification_email(
    request: Request,
    header: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    verification_model: VerificationModel = Body(),
    user_db=Depends(user_collection),
):
    callback_url = verification_model.callback_url
    user = decode(header.credentials)

    try:
        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token.")

        db_user = await user_db.find_one({"_id": ObjectId(user_id)})
        if not db_user:
            raise HTTPException(status_code=404, detail="No user found.")

        verification_token = create_access_token({"id": user_id})

        query_string = f"token={verification_token}&redirect={callback_url}"

        url_with_token = f"{request.url._url}?{query_string}"

        await send_email_verification(
            verification_link=url_with_token, to_email=db_user["email"]
        )

        return {"message": "Password reset link has been sent."}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.get("/verify")
async def verify(
    token: str = Query(...),
    redirect: str = Query(...),
    user_db=Depends(get_db),
):
    try:
        user = decode(token)

        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token.")

        filter = {"_id": ObjectId(user_id)}

        updated = await user_db.update_one(filter, {"$set": {"verified": True}})
        if updated.modified_count == 0:
            raise HTTPException(
                status_code=404, detail="User not found or already verified."
            )

        return RedirectResponse(url=redirect)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{id}", response_model=UserResponse)
async def user(
    id: str,
    user_db=Depends(get_db),
):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid 'id' provided")

    try:
        doc = await user_db.find_one({"_id": ObjectId(id)})

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
    sort_by: str = "created_at",
    sort_order: int = -1,
    skip: int = 0,
    limit: int = 10,
    user_db=Depends(get_db),
):
    try:
        users = await read_users(user_db)

        if not users:
            return {"users": [], "count": 0}

        filtered = []

        for user in users:
            if user.id is None:
                pass

            filtered.append(
                UserResponse(
                    id=user.id,
                    name=user.name,
                    username=user.username,
                    verified=user.verified,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                )
            )

        return {"list": filtered, "count": 0}

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
async def delete(
    id: str,
    user_db=Depends(get_db),
):
    try:
        await delete_user(user_db, id)
        return {"message": "User has been deleted.", "id": id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
