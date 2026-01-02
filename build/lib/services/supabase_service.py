import os
from dotenv import load_dotenv
from supabase.client import Client
import supabase
load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase_client: Client = supabase.create_client(
    supabase_url=SUPABASE_URL,
    supabase_key=SUPABASE_KEY,
)


def get_supabase_client():
    return supabase_client


