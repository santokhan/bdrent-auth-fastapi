import re
from datetime import datetime
from phonenumbers import is_valid_number, parse
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import List, Optional


class UserModel(BaseModel):
    role: str
    username: str = None
    name: str = None
    email: Optional[EmailStr] = None
    phone: str = Field(
        default=None, min_length=11, max_length=11
    )  # Store as a string for initial input
    password: str

    def validate_phone_number(self):
        if self.phone:  # validate only if user inputed
            try:
                parsed_number = parse(self.phone, "BD")
                if is_valid_number(parsed_number):
                    return parsed_number
                else:
                    raise ValueError("Invalid phone number")
            except Exception:
                raise ValueError("Invalid phone number format")
        return None

    def trim(self):
        return self.phone.strip()[-11:]

    def validate_password(self):
        if self.password:  # validate only if user inputed
            errors = []

            if len(self.password) < 6:
                errors.append("must be at least 6 characters long.")
            if not re.search(r"[a-zA-Z]", self.password):
                errors.append("must contain at least one letter.")
            if not re.search(r"[0-9]", self.password):
                errors.append("must contain at least one number.")

            if errors:
                raise ValueError("Invalid password: " + " ".join(errors))

        return "Valid password"


class UserLogin(BaseModel):
    username: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    password: str


class UserResponse(BaseModel):
    id: int
    role: str
    username: Optional[str] = None
    name: Optional[str] = None
    verified: Optional[bool] = False
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_response(cls, values):
        if not values['username']:
            raise ValueError('The key "username" must be provided')

        if not values['role']:
            raise ValueError('The key "role" must be provided')

        values["created_at"] = str(values["created_at"])
        values["updated_at"] = str(values["updated_at"])

        return values


class UsersResponse(BaseModel):
    list: List[UserResponse] = Field(default_factory=list)
    count: int = Field(default_factory=int)


class ForgotModel(BaseModel):
    email: Optional[EmailStr] = Field(default=None)
    username: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(
        default=None, min_length=11, max_length=11
    )  # Store as a string for initial input
    callback: Optional[str] = Field(
        default=None, detail="Reset form URL that client will send in body."
    )

    def validate_phone_number(self):
        if self.phone:  # validate only if user inputed
            try:
                parsed_number = parse(self.phone, "BD")
                if is_valid_number(parsed_number):
                    return parsed_number
                else:
                    raise ValueError("Invalid phone number")
            except Exception:
                raise ValueError("Invalid phone number format")
        return None


class ResetModel(BaseModel):
    password: str = Field(default=None)
    token: str = Field(default=None, description="Token including user object.")

    def validate_phone_number(self):
        if self.phone:  # validate only if user inputed
            try:
                parsed_number = parse(self.phone, "BD")
                if is_valid_number(parsed_number):
                    return parsed_number
                else:
                    raise ValueError("Invalid phone number")
            except Exception:
                raise ValueError("Invalid phone number format")
        return None


class TokenInputModel(BaseModel):
    refresh_token: str


class VerificationModel(BaseModel):
    callback_url: str = Field(description="Callback URL sent from client or app.")
