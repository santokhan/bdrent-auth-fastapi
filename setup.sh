python -m venv venv
exit

pip install fastapi uvicorn python-dotenv pymongo pydantic[email] phonenumbers argon2-cffi PyJWT motor

pip freeze > requirements.txt
pip install -r requirements.txt

source venv/Scripts/activate
uvicorn main:app --port 3005 --reload

venv\Scripts\activate
uvicorn main:app --port 3005 --reload

