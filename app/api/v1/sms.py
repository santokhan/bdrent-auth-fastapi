import os
import requests
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

url = "https://www.24bulksmsbd.com/api/smsSendApi"


async def sms_sender(message: str = None, mobile_no: str = None):
    if message is None or mobile_no is None:
        raise HTTPException(
            status_code=400, detail="SMS Sender require message & mobile_no"
        )

    SMS_CUSTOMER_ID = os.getenv("SMS_CUSTOMER_ID")
    SMS_API_KEY = os.getenv("SMS_API_KEY")

    if not SMS_CUSTOMER_ID or not SMS_API_KEY:
        raise HTTPException(status_code=500, detail="SMS service configuration error.")

    payload = {
        "customer_id": int(SMS_CUSTOMER_ID),
        "api_key": SMS_API_KEY,
        "message": message,
        "mobile_no": mobile_no,
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an error for bad responses
        if response.status_code == 200:
            data = response.json()
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))