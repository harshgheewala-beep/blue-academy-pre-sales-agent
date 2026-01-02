import asyncio
import uuid
from services.supabase_service import supabase_client, get_supabase_client
from services import similarity
from services.page_data_handler import resolve_page_data_by_slug
from agents import function_tool
from services.weaviate import fetch_weaviate_object, fetch_similar_courses



@function_tool(name_override="get_similar_courses")
def get_similar_courses(query: str)->list:
    """
    Use this function to get similar courses based on a query text input.

    Args:
        query: Simple query string including important keywords to get similar courses
    Returns:
        List of similar courses along with their details
    """
    response_data = similarity.get_similar_courses(query,
                                                    db)

    if not response_data:
        return []

    return response_data


@function_tool(name_override="get_similar_lesson_chunk")
def get_similar_lesson_chunk(query: str)->list:
    """
    Use this function to get similar lesson based on a query text input.

    Args:
        query: Simple query string including important keywords to get similar lesson chunk.
    Returns:
        List of similar courses along with their details
    """
    response_data = similarity.get_similar_lesson_chunks(query,db)

    return response_data or []



@function_tool(name_override="get_course_metadata")
def get_course_metadata(course_id:str | uuid.UUID)->dict:
    """
    Use this function to get course metadata
    Args: string representing the course ID in string format
    Returns:
         dictionary with course metadata
    """
    course_metadata = (db.table("courses")
                       .select("title,"
                                "level,"
                                "price,"
                               "duration_weeks,"
                                "skills,"
                                "prerequisites,"
                                "category")
                       .eq("id",course_id)
                       .execute().data)

    return course_metadata or {}


@function_tool(name_override="get_current_page_details")
async def get_current_page_details_using_slug(slug : str)->dict:
    """
    Use this function to get current page details using slug
    :param slug:
        slug of the current page
    :return dict:
        dictionary with current page details
    """

    print("hitting page details using slug")
    page_details = await fetch_weaviate_object(slug)

    if not page_details:
        return {}

    return {
        "Page Details":page_details
    }


@function_tool(name_override="get_similar_course_chunks")
async def get_similar_course_chunks(query: str)->list[dict]:
    """
    This function is used to get similar courses based on a query text input.
    :param query: The query string including important keywords to get similar courses chunks.
    :return:
    List of similar courses along with their details
    """


    result = await similarity.get_similar_course_chunks(query)
    return result



@function_tool(name_override="get_current_page_data_using_slug")
async def get_current_page_data_using_slug(slug: str) -> dict:
    """
    Fetch page data by slug.
    Read Only
    Args: slug.
    :return dict:
    """
    page_data, _ = await resolve_page_data_by_slug(slug)
    return page_data or {}
