import regex as re
from typing import Any
import json
from bs4 import BeautifulSoup


def strip_html(text: str) -> str:
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(
        separator=" ",
        strip=True)


def clean_text(text: str)-> str:
    if not text:
        return ""

    text = strip_html(text)
    text = re.sub(r"\s+"," ",text)
    return text.strip()


def clean_data_v2(payload: list[dict])-> list[dict]:
    cleaned = []

    for item in payload:
        data = {
            "course_id": extract_text(item.get("id")),
            "slug": extract_text(item.get("slug")),
            "course_title": clean_text(extract_text(item.get("title"))),
            "course_description": clean_text(extract_text(item.get("subtitle"))),
            "category": clean_text(extract_text(item.get("category"))),
            "duration": clean_text(extract_text(item.get("duration"))),
            "fee": clean_text(extract_text(item.get("fee"))),
            "hero_features": clean_text(extract_text(item.get("heroFeatures"))),
            "skills": clean_text(extract_text(item.get("skills"))),
            "prerequisites": clean_text(extract_text(item.get("prerequisites"))),
            "target_audience": clean_text(extract_text(item.get("targetAudience"))),
            "curriculum": clean_text(extract_text(item.get("curriculum"))),
            "faqs": clean_text(extract_text(item.get("faqs"))),
        }

        cleaned.append(data)

    return cleaned


def clean_data(payload: list[dict]):
    cleaned_textual_data = []
    for item in payload:
        data = {
        "course_id": serialize_data(item.get("id")),
        "slug": serialize_data(item.get("slug")),
        "course_title" : serialize_data(item.get("title")),
        "course_description" : serialize_data(item.get("subtitle")),
        "category": serialize_data(item.get("category")),
        "duration": serialize_data(item.get("duration")),
        "fee": serialize_data(item.get("fee")),
        "hero_features": serialize_data(item.get("heroFeatures")),
        "skills": serialize_data(item.get("skills")),
        "prerequisites": serialize_data(item.get("prerequisites")),
        "target_audience": serialize_data(item.get("targetAudience")),
        "curriculum": serialize_data(item.get("curriculum")),
        "faqs": serialize_data(item.get("faqs")),
        }

        cleaned_textual_data.append(data)

    return cleaned_textual_data


def extract_text(value: Any) -> str:
    text: list[str] = []
    if isinstance(value, str):
        text.append(value)
    elif isinstance(value, list):
        for item in value:
            text.append(extract_text(item))

    elif isinstance(value, dict):
        for v in value.values():
            text.append(extract_text(v))

    return " ".join(text)


def serialize_data(data: Any):
    serialized_data = None
    if isinstance(data, list):
        temp = []
        for item in data:

            if isinstance(item, dict):
                temp.extend([val for val in item.values() if isinstance(val,str)])

            elif isinstance(item, str):
                temp.append(item)
            else:
                pass

        serialized_data =  " ".join(temp).strip()

    elif isinstance(data, dict):
        serialized_data = " ".join(data.values())

    elif isinstance(data, str):
        return data
    else:
        return serialized_data

    return serialized_data


def normalize_query(query: str):
    query = query.lower()
    query = re.sub(r"[^a-z0-9\s]","",query)
    tokens = query.strip().split()
    return "_".join(sorted(tokens))

def clean_chat(list_chat: list[Any])-> list[dict]:
    cleaned_chat = []

    for item in list_chat:
        role = item.get("role",None)
        content = item.get("content",None)
        if role == "user":
            cleaned_chat.append({
                "role":"user",
                "content":content
            })

        elif role == "assistant":
            if isinstance(content,list) and len(content)>0:
                text_content = content[0].get("text","")
            else:
                text_content = str(content)

            try:
                parsed_content = json.loads(text_content)
                cleaned_chat.append({"role":"assistant","content":parsed_content})
            except Exception as e:
                print(str(e))
                cleaned_chat.append({"role":"assistant","content":text_content})
        else:
            pass

    return cleaned_chat