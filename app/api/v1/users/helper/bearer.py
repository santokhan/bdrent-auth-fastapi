from fastapi import HTTPException, status


def get_bearer_token(authorization: str) -> str:
    """
    Extracts and returns the bearer token from the Authorization header.

    Note:
    - This function handles errors internally and raises appropriate exceptions 
      if the Authorization header is invalid or missing.
    - Do not wrap this function in a try/except block, as it is designed to 
      handle its own error responses.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization.split(" ")[1]
