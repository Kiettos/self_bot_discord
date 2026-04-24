from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_db # Import file kết nối database bạn đã làm ở bước trước

app = FastAPI(title="Bot Manager API")

# Cấu hình CORS để cho phép Frontend (React) gọi API mà không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép mọi nguồn (khi dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lấy instance của Supabase
db = get_db()

# --- ĐỊNH NGHĨA KHUÔN DỮ LIỆU TỪ UI GỬI XUỐNG ---
class BotConfig(BaseModel):
    name: str
    discord_token: str
    groq_api_key: str
    target_channel: str
    keywords: list[str]