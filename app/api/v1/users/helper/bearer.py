from fastapi import HTTPException, Header


def get_bearer_token(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )
    return authorization.split(" ")[1]
