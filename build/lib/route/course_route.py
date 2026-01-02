import json
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from postgrest import CountMethod
from starlette.responses import JSONResponse
from supabase.client import Client
from model.input_schema import Course, CourseDetails, UpdateCourseMetaData, UpdateCourseDetails, UserDetails
from services.ingestion import ingest_course_embedding
from services.mongo_db import get_sync_details, fetch_changes, update_sync_details, increment_interest_count
from services.similarity import get_similar_course_chunks
from services.supabase_service import get_supabase_client
from services.data_handler import clean_data, clean_data_v2
from services.weaviate import delete_weaviate_object


router = APIRouter(
    prefix="/course",
    tags=["Course"],
)


logger = logging.getLogger("FastAPI Sync Route")



@router.get("/list",
            description="List all courses")
def list_courses(db: Client = Depends(get_supabase_client)):
    response = db.table("courses").select("*").execute()
    return response.data


@router.get("/by_id/{course_id}",
            description="Get course metadata using id")
def get_course_metadata(course_id: str | UUID, db: Client = Depends(get_supabase_client)):
    try:
        response = db.table("courses").select("*").eq(column="id", value=course_id).single().execute()
    except:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Course not found")

    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    return response.data



@router.get("/by_slug/{course_slug}",
            description="Get course metadata using slug")
def get_course_metadata(course_slug: str | UUID, db: Client = Depends(get_supabase_client)):
    try:
        response = db.table("courses").select("*").eq(column="slug", value=course_slug).single().execute()
    except:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Course not found")

    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    return response.data


@router.get("/by_id/{course_id}/multiple",
            description="Get multiple courses")
async def get_multiple_courses(payload: dict,
                               db: Client = Depends(get_supabase_client)):
    response = db.table("courses").select("*").in_("id", payload["course_ids"]).execute()

    return response.data or []


@router.get("/by_id/{course_id}/details",
            description="Get course details using id")
def get_course_details(course_id: str | UUID, db: Client = Depends(get_supabase_client)):
    try:
        print("Fetching course details for ID:", course_id)
        response = db.table("course_details").select("*").eq(column="course_id", value=course_id).single().execute()
    except:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Course not found")

    if not response.data:
        print("No data found for course ID:", course_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    return response.data


@router.post("/add_course_metadata",
             description="Add course with metadata to database")
def add_course(data: Course ,db: Client = Depends(get_supabase_client)):

    response = db.table("courses").insert(data.model_dump()).execute()

    return response.data


@router.post("/add_course_details",
             description="Add course details to database")
def add_course_details(data: CourseDetails,
                       db: Client = Depends(get_supabase_client)):
    response = db.table("course_details").insert(data.model_dump()).execute()

    return response.data


@router.patch("/by_id/{course_id}/update_metadata",
              description="Update course metadata",
              deprecated=True)
def update_course_metadata(course_id: str,
                           updates: UpdateCourseMetaData,
                           db = Depends(get_supabase_client)):
    response = db.table("courses").update(updates.model_dump()).eq({"id": course_id}).execute()
    return response.data


@router.patch("/by_id/{course_id}/update_details",
              description="Update course Brief details")
def update_course_details(course_id: str,
                          updates: UpdateCourseDetails,
                          db = Depends(get_supabase_client)):
    response = db.table("course_details").update(updates.model_dump()).eq({"course_id": course_id}).execute()
    return response.data


@router.get("/filter_course_by_price")
def filter_course_by_price(price: int, db: Client = Depends(get_supabase_client)):
    response = db.table("courses").select("*").lte(column="price",value=price).execute()
    return response.data


@router.get("/get_similar_courses")
def get_similar_courses_api(query: str, db: Client = Depends(get_supabase_client)):
    # print(query)
    # print(db)

    data = get_similar_course_chunks(query)
    return data


@router.post("/by_id/{course_id}/enrol",
             description="Enrol a user to course")
def enrol_in_course(course_id: str | UUID, user: UserDetails, db: Client = Depends(get_supabase_client)):
    """
    Enrol a user for a course. If the user does not exist, create a new user entry.
    Might get changed to use authentication in the future.
    """
    course_resp = db.table("courses").select("id").eq("id", str(course_id)).execute()
    if not course_resp.data:
        raise HTTPException(status_code=404, detail="Course not found")
    

    user_resp = (db.table("users")
    .select("*")
    .eq(column="email", value=user.email)
    .execute())

    print(course_resp.data)
    print(user_resp)

    if user_resp.data:
        user_id = user_resp.data[0]["id"]
    else:
        new_user = (db.table("users").insert(user.model_dump()).execute())
        user_id = new_user.data[0]["id"]


    reg_check = (db.table("enrolment")
    .select("*")
    .match({
        "course_id":course_id,
        "user_id":user_id
    }).execute())

    
    if reg_check.data:
        return {
                "status": "already_registered",
                "message": "User already registered for this course",
                "course_id": course_id,
                "user_id": user_id
            }

    
    (db.table("enrolment").insert(
        {
            "course_id": course_id,
            "user_id": user_id
        }
    ).execute())

    return {
        "status": "registered",
        "message": "User successfully registered for the course",
        "course_id": course_id,
        "user_id": user_id,
    }



@router.post("/by_id/{course_id}/interest",
             description="Increment course interest count",deprecated=True)
def mark_interest(course_id: str | UUID, db: Client = Depends(get_supabase_client)):
    response = db.table("course_interest_metrics").select("*").eq("course_id",course_id).execute()


    if response.data:
        interest_count = response.data[0].get("interest_count")
        db.table("course_interest_metrics").update({"interest_count": interest_count + 1}).eq("course_id",course_id).execute()
    else:
        db.table("course_interest_metrics").insert(
            {
                "course_id": course_id,
                "interest_count": 1
            }
        ).execute()

    return JSONResponse(
        status_code=201,
        content={"detail": "Marked Interested"}
    )

@router.post("/{course_slug}/mark_interest",
            description="Mark course interest count")
async def mark_interest(course_slug:str):
    increment_interest_count(course_slug)



    return JSONResponse(
        status_code=200,
        content={
            "detail": "Marked Interested"
        }
    )



@router.post("/by_id/{course_id}/lead",
             description="Mark user for lead")
def marked_interested_users(course_id: str,user: UserDetails, db: Client = Depends(get_supabase_client)):
    course_resp = db.table("courses").select("id").eq("id", str(course_id)).execute()
    if not course_resp.data:
        raise HTTPException(status_code=404, detail="Course not found")


    response = db.table('interested_users').insert({
        "course_id": course_id,
        "name": user.name,
        "email": user.email,
        "contact_number": user.contact_number,
    }).execute()

    if response.data:
        return JSONResponse(
            status_code=201,
            content={
                "detail":"Marked User for course lead"
            }
        )

    else:
        raise HTTPException(status_code=500, detail="Something went wrong")


@router.get("/by_id/{course_id}/interest_count",
            description="Get course interest count")
def get_interest_count(course_id: str | UUID, db: Client = Depends(get_supabase_client)):
    response = db.table("course_interest_metric").select("course_id").eq("course_id", course_id).single().execute()

    return response.data[0].get("interest_count") if response.data else 0

@router.get("/leads",
            description="List all interested candidates")
def list_interested_users(db: Client = Depends(get_supabase_client)):
    response = (
        db.table("interested_users")
        .select("""
                name,
                email,
                contact_number,
                course_id,
                courses(
                id,
                title),
                created_at
        """)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data


@router.get("/by_id/{course_id}/modules",
            description="List all modules")
async def list_module(course_id: str, db: Client = Depends(get_supabase_client)):
    response = (db.table("modules")
                .select("*")
                .eq("course_id", course_id)
                .order("order_index",desc=False)
                .execute())

    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=404, detail="No modules available")
    return response.data


@router.post("/by_id/{course_id}/modules",
             description="Add Module to course")
async def add_module(course_id: str, module_name: str, db: Client = Depends(get_supabase_client)):
    count_resp = db.table("lessons").select("id", count=CountMethod("exact")).eq("course_id", course_id).execute()
    order_index = (count_resp.count or 0) + 1

    response = db.table("modules").insert(
        {
            "course_id": course_id,
            "name": module_name,
            "order_index": order_index,
        }
    ).execute()

    if response.data:
        return JSONResponse(
            content={"detail": "Module added"},
            status_code=201
        )

    return response.data

@router.post("/get_course_query")
async def get_course_by_query(query: str):
    result = await get_similar_course_chunks(query)
    print(result)
    return result


@router.post("/sync_mongo_data",
             description="Synchronize Weaviate Collection with Mongo DB Collection")
async def sync_mongo_data():
    try:
        last_sync_time = await get_sync_details()
        print(f"Last Update timestamp: {last_sync_time}")

        changes = await fetch_changes(last_sync_time)


        if not changes:
            logger.info("No changes found")
            return JSONResponse(
                status_code=200,
                content={
                    "details": "Data is already synced"
                }
            )

        slugs_to_purge = [doc["slug"] for doc in changes]
        updated_data = [docs for docs in changes if not docs["isDeleted"]]

        await delete_weaviate_object(slugs_to_purge)

        if not updated_data:
            return JSONResponse(
                status_code=200,
                content = {
                    "details": "Data Synced Successfully"
                }
            )

        # Uncomment this if v2 does not work
        # cleaned_data = clean_data(updated_data)

        cleaned_data = clean_data_v2(updated_data)

        ingestion_complete = await ingest_course_embedding(cleaned_data)

        if ingestion_complete:
            await update_sync_details()

            return {
                "status": "success",
                "message": "Data synced successful",
            }

        else:
            return {
                "status": "fail",
                "message": "Data synced failed",
            }


    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to sync data :{str(e)}")