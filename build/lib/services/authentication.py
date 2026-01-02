from http.client import HTTPResponse
from starlette.responses import JSONResponse
from fastapi import HTTPException, Request
from services.jwt_handler import  verify_jwt_token
from services.supabase_service import get_supabase_client
from supabase.client import Client
from model.input_schema import LoginSchema
from bcrypt import checkpw


db: Client = get_supabase_client()


def authenticate_user(credentials: LoginSchema):

    request_body = credentials.model_dump()

    email = request_body.get("email")
    password = request_body.get("password")

    response = (db.table("users").select("id, email, password",
                                         "role(name, role_permissions(permissions(name)))")
                .match({
        "email":email,
        "is_deleted":False
    }).execute())

    if not response.data:
        raise HTTPException(status_code=404,
                            detail="No email found")

    if not checkpw(
            password=password.encode('utf-8'),
            hashed_password=response.data[0]["password"].encode("utf-8")):
        raise HTTPException(status_code=401,
                            detail="Incorrect email or password")


    return response.data[0]


def get_current_user(request: Request):

    auth_header = request.headers.get('Authorization')
    if not auth_header:
    #     return JSONResponse(status_code=401,
    #                         content={"detail": "Missing Authorization Details"})
        raise HTTPException(status_code=401,
                            detail="Missing Authorization Details")


    if not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401,
                            detail="Invalid Authorization Format")


    token =  auth_header.split(" ")[1]
    payload = verify_jwt_token(token)

    return payload
