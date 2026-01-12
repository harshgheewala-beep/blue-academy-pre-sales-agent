from pydantic import Field, BaseModel
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
    Fetch page data by slug.
    Read Only
    Args: slug.
    :return dict:
    """
    page_data, _ = await resolve_page_data_by_slug(slug)
    return page_data or {}



class LeadDetails(BaseModel):
    name: str = Field(..., description="The full name of the user. Do not guess.")
    email: str = Field(..., description="A valid email address provided by the user.")
    contact: str = Field(..., description="The phone number starting with +.")
    slug: str = Field(..., description="The slug of the course the user is interested in.")


@function_tool(name_override="mark_user_lead")
async def mark_user_lead(
        details: LeadDetails,
) -> str:
    """
    Use this function to mark user's interest in course to provide them follow up
    [Critical]
    Always provide user details given name, email, contact and slug
    Do not call this call if you don't have user's contact details
    This field can't be empty string `""` or None
    Args:
        details:
    Returns:
        String indicating user marked for follow up
    """


    invalid_placeholders = {
        "user",
        "user@example.com",
        "+123456789",
    }

    if details.name.lower() in invalid_placeholders:
        return "Please provide your real name."

    if details.email in invalid_placeholders:
        return "Please provide a valid email address."

    if details.contact in invalid_placeholders:
        return "Please provide a valid contact number."

    if not details.name or details.name == "":
        return "Please provide your name"

    if not details.email or details.email == "":
        return "Please provide your email"

    if not details.contact or details.contact == "":
        return "Please provide your contact"

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




