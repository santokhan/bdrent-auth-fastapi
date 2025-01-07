import asyncio
import os
from typing import Optional
import requests
from pydantic import BaseModel, Field, ValidationError


class SMSRequest(BaseModel):
    mobile_no: str = Field(
        ..., description="String or comma-separated string of numbers"
    )
    message: Optional[str] = Field(
        "Hello, Welcome to the SSI Mart Ecommerce.", description="Message to be sent"
    )


API_URL = "https://www.24bulksmsbd.com/api/smsSendApi"


def get_sms_credentials() -> tuple[str, str]:
    """Fetch SMS credentials from environment variables."""
    customer_id = os.getenv("SMS_CUSTOMR_ID")
    api_key = os.getenv("SMS_API_KEY")

    if not customer_id or not api_key:
        raise ValueError("SMS service configuration error. Missing SMS_CUSTOMR_ID or SMS_API_KEY.")

    return customer_id, api_key


def send_sms_request(payload: dict) -> dict:
    """Make a synchronous request to the SMS API."""
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to send SMS: {e}")


async def sms_sender(message: str, mobile_no: str) -> dict:
    """Send an SMS using the external API."""
    customer_id, api_key = get_sms_credentials()

    payload = {
        "api_key": api_key,
        "customer_id": int(customer_id),
        "mobile_no": mobile_no,
        "message": message,
    }

    return await asyncio.to_thread(send_sms_request, payload)


async def send_sms(sms_request: SMSRequest) -> dict:
    """Send an SMS and return the result."""
    return await sms_sender(sms_request.message, sms_request.mobile_no)


# Test
async def test():
    try:
        sms_request = SMSRequest(mobile_no="01307230077", message="Your verification code is: 123456.")
        response = await send_sms(sms_request)
        print(response)
    except ValidationError as e:
        print(f"Validation Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test())
