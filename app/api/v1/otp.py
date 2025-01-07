from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field, model_validator
from sms_service.main import SMSRequest, send_sms
from .otp_store import OTPStore
import asyncio  # Use asyncio for async operations

router = APIRouter()
otp_store = OTPStore()


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


class OTPVerify(OTPRequest):
    otp: str = Field(min_length=6, max_length=6)


class OTPResponse(BaseModel):
    message: str


@router.post("/generate-otp/")
async def generate_otp(request: OTPRequest = Body(...)) -> OTPResponse:
    # Simulate asynchronous OTP creation
    otp = await asyncio.to_thread(otp_store.create, request.phone_number)

    if otp is None:
        raise HTTPException(detail="Failed to generate OTP.")

    sms_status = await send_sms(
        SMSRequest(
            mobile_no=request.phone_number,
            message=f"Your verification code is: {otp}.",
        )
    )

    if sms_status is None:
        raise HTTPException(detail="Failed to send OTP.")

    return OTPResponse(message="OTP sent successfully")


# # Test
# {"phone_number": "01307230077"}


@router.post("/verify-otp/")
async def verify_otp(request: OTPVerify = Body(...)) -> OTPResponse:
    phone_number = request.phone_number

    # Check if OTP exists for the given phone number asynchronously
    stored_otp = await asyncio.to_thread(lambda: otp_store.read(phone_number))

    if not stored_otp:
        raise HTTPException(status_code=400, detail="OTP not found")

    if otp_store.verify(phone_number=phone_number, otp_input=request.otp) == False:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Check if the OTP is expired asynchronously
    if otp_store.is_expired(phone_number):
        await asyncio.to_thread(lambda: otp_store.delete(phone_number))
        raise HTTPException(status_code=400, detail="OTP expired")

    # OTP is valid, clear OTP after verification
    await asyncio.to_thread(lambda: otp_store.delete(phone_number))

    return OTPResponse(message="OTP verified successfully")


# # Test
# {"phone_number": "01307230077", "otp": ""}
