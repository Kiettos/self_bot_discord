# File: backend/database.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Tải các biến môi trường từ file .env
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("⚠️ Thiếu SUPABASE_URL hoặc SUPABASE_KEY trong file .env!")

# Khởi tạo Client kết nối với Supabase
supabase_client: Client = create_client(url, key)

def get_db():
    return supabase_client