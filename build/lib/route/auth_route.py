from fastapi import APIRouter, Depends, HTTPException
from model.input_schema import LoginSchema
from supabase.client import Client
from services.supabase_service import get_supabase_client
from services.authentication import authenticate_user
from services.jwt_handler import create_access_token, create_refresh_token, hash_refresh_token
from datetime import datetime, timedelta


router = APIRouter(
    tags=["Auth"],
)


def store_refresh_token(user_id: str, refresh_hash: str, db: Client):
    expires_at = (datetime.now() + timedelta(days=7)).isoformat()
    db.table("refresh_tokens").insert({
        "user_id": user_id,
        "token_hash": refresh_hash,
        "expires_at": expires_at,
        "revoked": False
    }).execute()


@router.post("/login",
            description="Login user")
async def login_user(credentials : LoginSchema, db: Client = Depends(get_supabase_client)):

    user = authenticate_user(credentials)

    enrolled_courses_resp = db.table("enrolment").select("course_id").eq("user_id",user["id"]).execute()

    enrolled_courses = [
        c["course_id"] for c in enrolled_courses_resp.data or []
    ]

    permissions = [
        perm["permissions"]["name"] for perm in user["role"].get("role_permissions",[])
    ]


    payload = {
        "sub": user["id"],
        "permissions": permissions,
        "email": user["email"],
        "role": user["role"]["name"],
        "enrolled_courses": enrolled_courses,
    }

    access_token = await create_access_token(payload)
    print(access_token)

    refresh_token = await create_refresh_token()
    refresh_hash = await hash_refresh_token(refresh_token)
    print(refresh_hash)

    store_refresh_token(user["id"], refresh_hash, db)


    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post("/auth/refresh",
             description="Refresh access token")
async def refresh_access_token(refresh_token: str, db: Client = Depends(get_supabase_client)):
    token_hash = await hash_refresh_token(refresh_token)

    token_row = (
        db.table("refresh_tokens")
        .select("*")
        .eq("token_hash", token_hash)
        .eq("revoked", False)
        .gte("expires_at", datetime.now().isoformat())
        .single()
        .execute()
    )

    if not token_row.data:
        raise HTTPException(status_code=400, detail="Invalid refresh token")


    user_id = token_row.data["user_id"]

    user = (
        db.table("users")
        .select("id,email,role(name,role_permissions(permissions(name)))")
        .eq("id", user_id)
        .single()
        .execute()
    ).data

    permissions = [
        p["permissions"]["name"]
        for p in user["role"]["role_permissions"]
    ]

    payload = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"]["name"],
        "permissions": permissions,
    }

    new_access_token = await create_access_token(payload)

    return {"access_token": new_access_token}


@router.post("/auth/rotate")
async def rotate_refresh_token(user_id: str,old_token_id: str,db: Client = Depends(get_supabase_client)) -> dict:
    # revoke old
    db.table("refresh_tokens").update({
        "revoked": True
    }).eq("id", old_token_id).execute()

    # create new
    new_refresh_token = await create_refresh_token()
    store_refresh_token(user_id, new_refresh_token, db)

    return {"refresh_token": new_refresh_token}


@router.post("/logout",
            description="Logout user")
async def logout_user(user_id: str, db: Client = Depends(get_supabase_client)):
    db.table("refresh_tokens").update({
        "revoked": True
    }).eq("user_id", user_id).execute()