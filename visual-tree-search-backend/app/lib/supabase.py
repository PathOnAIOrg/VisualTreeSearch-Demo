import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Get Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    raise ValueError("Missing SUPABASE_URL environment variable")

if not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_KEY environment variable")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)