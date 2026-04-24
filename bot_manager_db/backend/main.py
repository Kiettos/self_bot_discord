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
    
    
    @app.get("/bots")
    def get_all_bots():
        """Lấy toàn bộ danh sách bot hiện có trong Database"""
        response = db.table("bots").select("*").execute()
        return {"status": "success", "data": response.data}
    
    
    
    
    import subprocess
import os
import signal
import sys
from fastapi import HTTPException

# --- API START BOT ---
@app.post("/start/{bot_id}")
def start_bot(bot_id: str):
    # 1. Lấy thông tin bot từ database
    response = db.table("bots").select("*").eq("id", bot_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy bot")
    
    bot_data = response.data[0]
    
    # 2. Kiểm tra xem file script có tồn tại không
    script_path = f"../generated_bots/runner_{bot_id}.py"
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="File code của bot chưa được sinh ra!")

    # 3. Kích hoạt bot bằng Subprocess
    try:
        # Đường dẫn tới python.exe trong môi trường ảo (venv) của bạn
        # Nếu bạn dùng Linux/Mac, hãy đổi thành: venv_python = sys.executable hoặc "venv/bin/python"
        venv_python = sys.executable 
        
        # Chạy file dưới dạng tiến trình ngầm (background process)
        process = subprocess.Popen([venv_python, script_path])
        
        # 4. Lưu Process ID (PID) vào Supabase để sau này biết đường mà tắt
        db.table("bots").update({
            "status": "running",
            "pid": process.pid
        }).eq("id", bot_id).execute()
        
        return {"status": "success", "message": f"Bot đã chạy với PID: {process.pid}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi chạy bot: {str(e)}")


# --- API STOP BOT ---
@app.post("/stop/{bot_id}")
def stop_bot(bot_id: str):
    # 1. Tìm thông tin bot và PID
    response = db.table("bots").select("*").eq("id", bot_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy bot")
        
    bot_data = response.data[0]
    pid = bot_data.get("pid")
    
    if not pid:
        raise HTTPException(status_code=400, detail="Bot này hiện không chạy (không có PID)")

    # 2. Bắn tín hiệu "Kill" (Tiêu diệt) tiến trình
    try:
        os.kill(pid, signal.SIGTERM) # Gửi lệnh tắt an toàn
    except ProcessLookupError:
        pass # Tiến trình đã tự tắt từ trước rồi
    except Exception as e:
        pass # Bỏ qua các lỗi khác liên quan đến hệ điều hành

    # 3. Cập nhật lại trạng thái trên Database
    db.table("bots").update({
        "status": "stopped",
        "pid": None
    }).eq("id", bot_id).execute()
    
    return {"status": "success", "message": "Đã tắt bot thành công!"}
    