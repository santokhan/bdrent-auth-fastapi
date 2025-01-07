setup(){
    python -m venv venv
    exit
    pip install fastapi uvicorn python-dotenv pymongo pydantic[email] phonenumbers argon2-cffi PyJWT motor
    pip freeze > requirements.txt
}

run_server(){
    python -m venv venv
    pip install -r requirements.txt
    source venv/Scripts/activate # windows bash
    # venv\Scripts\activate # windows powershell
    # source venv/bin/activate # linux bash
    uvicorn main:app --port 3005 --reload
}

docker(){
    docker compose up --build # build used to make new build after change
    docker exec -it mongodb_container
    mongosh -u root -p 1234
}

mongodb(){
    mongosh --version
    mongosh
    use admin # Use admin db to authenticate
    db.auth("root", "1234") # authenticate
    use test # create and switch to db like git bash
    db.createCollection("auth") # require at least one collection
}

docker exec -it python_container python app/api/v1/otp_store.py