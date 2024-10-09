from argon2 import PasswordHasher
from fastapi import HTTPException

ph = PasswordHasher()


def make_hash(password):
    try:
        return ph.hash(password)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def verify_hash(hash, user_password):
    try:
        if not hash or not ph.verify(hash, user_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
