from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from services.supabase_service import get_supabase_client
from services.permission_checks import required_roles


router = APIRouter(
    prefix="/role",
    tags=["Roles and permissions"],
)


@router.get("",description="Get all roles")
async def get_roles_and_permissions(db: Client = Depends(get_supabase_client)):
    response = db.table("role"
                           ).select("*").execute()
    return response.data


@router.post("/{role_id}/permissions",
             description="Add permissions to role")
async def add_permissions(role_id: str, permission:str, db: Client = Depends(get_supabase_client)):
    permission_id = db.table("permissions").select("id").eq("name",permission).execute().data[0]["id"]
    response = db.table("role_permissions").insert({
        "role_id": role_id,
        "permission_id": permission_id,
    }).execute()

    return response.data


@router.get("/{role_id}/permissions",description="Get a permissions for specific role")
async def get_permissions(role_id:str,db: Client = Depends(get_supabase_client)):
    response = db.table("role_permissions").select("role_id,permissions(id,name, description)").eq("role_id",role_id).execute()

    if not response.data:
        raise HTTPException(status_code=404,
                            detail="No permissions for this role")

    return response.data


@router.post("/permissions",
             description="Create new permission")
async def create_permission(name: str,description: str,db: Client = Depends(get_supabase_client)):
    response = db.table("permissions").insert({
        "name": name,
        "description": description,
    }).execute()

    return response.data

@router.get("/permissions/group",
            description="Get permissions for a group")
async def get_permissions_groups(group: str, db: Client = Depends(get_supabase_client)):
    response = db.table("permissions").select("*").text_search("name",group).execute()

    return response.data