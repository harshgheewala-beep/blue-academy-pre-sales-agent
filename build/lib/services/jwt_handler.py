from jwt import encode, decode, InvalidTokenError, InvalidSignatureError
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from fastapi import HTTPException
import secrets
import hashlib


load_dotenv()


JWT_SECRET = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"


async def generate_jwt_token(payload: dict)-> str:
    token = encode(payload,
                          algorithm=JWT_ALGORITHM,
                          key=JWT_SECRET)

    return token



async def create_access_token(payload: dict) -> str:
    payload.update({
        "iat": datetime.now(),
        "exp": datetime.now() + timedelta(minutes=30)})

    return encode(payload,
                algorithm=JWT_ALGORITHM,
                key=JWT_SECRET)


async def create_refresh_token() -> str:
    """
    For Generate a refresh token
    :return:
    """
    return secrets.token_urlsafe(64)


async def hash_refresh_token(refresh_token: str) -> str:
    """
    For generating the hashed refresh token
    :param refresh_token:
    :return:
    """
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()

async def verify_jwt_token(token: str)-> dict:
    try:
        payload = decode(token,
                         key=JWT_SECRET,
                         algorithms=[JWT_ALGORITHM],
                         verify=True)
        return payload

    except InvalidSignatureError:
        raise HTTPException(status_code=401,
                            detail="Unauthorized access")

    except InvalidTokenError:
        raise HTTPException(status_code=401,
                            detail="Unauthorized access")
