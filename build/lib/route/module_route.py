from fastapi import APIRouter, Depends, HTTPException
from postgrest import CountMethod
from starlette.responses import JSONResponse
from supabase.client import Client

from route.lesson_route import get_all_textual_data
from services.ingestion import ingest_lesson_chunks
from services.supabase_service import get_supabase_client
from model.input_schema import LessonDetails

router = APIRouter(
    tags=["Modules"],
    prefix="/module",
)




@router.get("/{module_id}",
            description="Get a module's details")
async def get_module(module_id: str, db: Client = Depends(get_supabase_client)):
    response = db.table("modules").select("*").eq("id", module_id).execute()
    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Module not found")

    return response.data



@router.get("/{module_id}/lessons",
            description="Get a module's lessons")
async def get_lessons(module_id: str, db: Client = Depends(get_supabase_client)):

    response = (db.table("lessons")
                .select("*")
                .eq("module_id", module_id)
                .order("order_index",desc=False)
                .execute())

    if len(response.data) == 0:
        return JSONResponse(status_code=404,
                            content={"detail": "Lesson not found"})

    return response.data


@router.post("/{module_id}/lessons",
             description="Add a lesson to module")
async def add_lesson_to_module(module_id: str, lesson: LessonDetails, db:Client = Depends(get_supabase_client)):
    # order_index = 1
    # lessons = db.table("lessons").select("*").eq("module_id",module_id).execute()
    #
    # if len(lessons.data) == 0:
    #     order_index = 1
    # else:
    #     order_index += len(lessons.data)
    # print(lessons.data)
    # data = lesson.model_dump()
    # data.update({
    #     "module_id": module_id,
    #     "order_index": order_index
    # }
    # )
    # print(type(data))
    #
    # response = db.table("lessons").insert(
    #     data
    # ).execute()
    #
    # if not response.data:
    #     return JSONResponse(status_code=500,
    #                         content={"detail": "Error adding lesson"})
    #
    # lesson_id = response.data[0]["id"]
    # textual_data = await get_all_textual_data(lesson_id, db)
    # ingest_lesson_chunks(textual_data,db)
    #
    # return response.data

    count_resp = db.table("lessons").select("id", count=CountMethod("exact")).eq("module_id", module_id).execute()
    order_index = (count_resp.count or 0) + 1

    data = lesson.model_dump()
    data.update({
            "module_id": module_id,
            "order_index": order_index
    })

    response = db.table("lessons").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Error adding lesson")

    lesson_id = response.data[0]["id"]
    textual_data = await get_all_textual_data(lesson_id, db)

    import threading
    threading.Thread(
            target=ingest_lesson_chunks,
            args=(textual_data, db),
            daemon=True
        ).start()

    return response.data


@router.patch("/{module_id}",
              description="Update a module's details")
async def update_module(module_id: str, db: Client = Depends(get_supabase_client)):
    pass


@router.delete("/{module_id}",
               description="Delete a module's details")
async def delete_module(module_id: str, db: Client = Depends(get_supabase_client)):
    pass
