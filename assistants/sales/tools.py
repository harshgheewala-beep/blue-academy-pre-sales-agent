from pydantic import Field, BaseModel, field_validator

from model.input_schema import LeadDetails
from services import similarity
from services.page_data_handler import resolve_page_data_by_slug
from agents import function_tool
from services.mongo_db import mark_course_lead
from services.weaviate_service import fetch_weaviate_object


@function_tool(name_override="get_current_page_details")
async def get_current_page_details(slug : str)->dict:
    """
    Use this function to get current page details using slug
    :param slug:
        slug of the current page
    :return dict:
        dictionary with current page details
    """

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
    Fetch current page data by slug.
    Read Only
    Args: slug.
    Returns dict:
    """
    page_data, _ = await resolve_page_data_by_slug(slug)
    return page_data or {}






@function_tool(name_override="mark_user_lead")
async def mark_user_lead(
        details: LeadDetails,
) -> str:
    """
    Use this function to mark user's interest in course to provide them follow up
    [Critical]
    Always provide user details given name, email, contact and slug
    Do not call this call if you don't have all user's contact details
    This field can't be empty string `""` or None
    So gather all details from user.
    Args:
        details:
    Returns:
        String indicating user marked for follow up
    """

    invalid_placeholders = {
        "user",
        "user@example.com",
        "+1234567890",
        "none",
        "null"
    }

    if (not details.name or details.name == "") or (not details.email or details.email == '') or (not details.contact or details.contact == ''):
        return 'Please Provide all the contact details properly'

    if details.name.lower() in invalid_placeholders:
        return "Please provide your real name."

    if details.email in invalid_placeholders:
        return "Please provide a valid email address."

    if details.contact in invalid_placeholders:
        return "Please provide a valid contact number."



    result = await mark_course_lead(
        course_slug=details.slug,
        user_payload={
        "name": details.name,
        "email": details.email,
        "contact": details.contact,
    })

    if type(result) == str:
        return result

    return "Marked user for follow up" if result else "Failed to mark user"




