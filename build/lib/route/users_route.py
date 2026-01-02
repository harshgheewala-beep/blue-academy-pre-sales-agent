import jwt
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from supabase.client import Client
from model.input_schema import UserDetails, UserRegistration, LoginSchema
from services.authentication import authenticate_user
from services.supabase_service import get_supabase_client
from bcrypt import checkpw, hashpw, gensalt
from services.jwt_handler import generate_jwt_token, create_access_token

router = APIRouter(
    tags=["Users"],
    prefix="/users",
)






@router.get("",
            description="List users")
async def list_user(db: Client = Depends(get_supabase_client)):
    response = db.table("users").select("*").order("name").execute()
    return response.data or []


@router.get("/{user_id}",
            description="Get user details by id")
async def get_user(user_id: str, db: Client = Depends(get_supabase_client)):
    response = db.table("users").select("*").eq("id",user_id).execute()
    return response.data or []


@router.post("/register",
             description="Create new user")
async def create_user(user_details: UserRegistration, db: Client = Depends(get_supabase_client)):

    hashed_password_bytes = hashpw(
        user_details.password.encode("utf-8"),
        gensalt())
    user_data = user_details.model_dump()
    user_data["password"] = hashed_password_bytes.decode("utf-8")
    user_data['role'] = db.table("role").select("id").eq("name","student").execute().data[0]

    response = db.table("users").insert(
        user_data
    ).execute()
    return response.data


@router.put("/{user_id}",
            description="Update user details")
async def update_user_details(user_id: str,db: Client = Depends(get_supabase_client)):
    pass


@router.delete("/{user_id}",
               description="Delete user details")
async def delete_user(user_id: str, db: Client = Depends(get_supabase_client)):
    pass


@router.get("/{user_id}/courses",
            description="List courses of current user")
async def list_user_courses(user_id: str, db: Client = Depends(get_supabase_client)):
    response = db.table("enrolment").select(
        "*"
    ).eq("user_id",user_id).execute()

    return response.data or []


