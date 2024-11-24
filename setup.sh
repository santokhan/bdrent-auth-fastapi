python -m venv venv
exit

pip install fastapi uvicorn python-dotenv pymongo pydantic[email] phonenumbers argon2-cffi PyJWT motor

pip freeze > requirements.txt