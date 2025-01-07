from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field, model_validator
import time
from .otp_store import OTPStore
import asyncio  # Use asyncio for async operations

router = APIRouter()


class OTPRequest(BaseModel):
    phone_number: str = Field(min_length=11, max_length=11)

    @model_validator(mode="after")
    def check_phone_number_prefix(cls, values):
        phone_number = values.phone_number

        prefix = ("013", "014", "015", "016", "017", "018", "019")

        if phone_number and not phone_number.startswith(prefix):
            raise ValueError(
                f"Phone number must start with 013, 014, 015, 016, 017, 018, or 019"
            )
        return values


class OTPVerify(BaseModel):
    phone_number: str
    otp: str


otp_store = OTPStore()


# Generate OTP
@router.post("/generate-otp/")
async def generate_otp(request: OTPRequest = Body(...)):
    # Simulate asynchronous OTP creation
    await asyncio.to_thread(otp_store.create, request.phone_number)
    return {"message": "OTP sent successfully"}


# Verify OTP
@router.post("/verify-otp/")
async def verify_otp(request: OTPVerify):
    phone_number = request.phone_number
    otp = request.otp

    # Check if OTP exists for the given phone number asynchronously
    stored_otp = await asyncio.to_thread(lambda: otp_store.get(phone_number))

    if not stored_otp:
        raise HTTPException(status_code=400, detail="OTP not found")

    if stored_otp["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Check if the OTP is expired asynchronously
    if time.time() - stored_otp["timestamp"] > 300:
        await asyncio.to_thread(lambda: otp_store.delete(phone_number))
        raise HTTPException(status_code=400, detail="OTP expired")

    # OTP is valid, clear OTP after verification
    await asyncio.to_thread(lambda: otp_store.delete(phone_number))

    return {"message": "OTP verified successfully"}


# Replace this function with your SMS sender script
async def send_sms(phone_number, otp):
    # Simulate async SMS sending
    print(f"Sending OTP {otp} to {phone_number}")
    # Your script logic here, ideally using an async SMS sending service
