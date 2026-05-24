import json
import os
from langchain_core.tools import tool

MEMORY_FILE = "long_term_memory.json"

@tool
def load_memory() -> str:
    """
    Công cụ dùng để đọc lại toàn bộ trí nhớ dài hạn của người dùng.
    Hãy gọi công cụ này khi người dùng hỏi về các thông tin cá nhân, sở thích, 
    hoặc các lưu ý đã ghi nhớ từ trước.
    """
    if not os.path.exists(MEMORY_FILE):
        return "Hiện chưa có thông tin nào trong bộ nhớ dài hạn."
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return json.dumps(data, ensure_ascii=False, indent=4)
        except:
            return "Lỗi khi đọc file bộ nhớ."

@tool
def save_long_term_memory(key: str, information: str) -> str:
    """
    Công cụ BẮT BUỘC dùng để ghi nhớ các thông tin quan trọng, tĩnh, hoặc sở thích của người dùng vào bộ nhớ dài hạn.
    Tham số:
    - key: Từ khóa đại diện ngắn gọn (VD: 'ten_sep', 'ten_truong', 'mon_an_ua_thich').
    - information: Nội dung chi tiết cần ghi nhớ.
    """
    data = {}
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e: 
                print(f"[memory_tools] Lỗi đọc JSON: {e}") 
                data = {}
    
    # Ghi đè hoặc thêm mới thông tin
    data[key] = information
    
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    return f"Hệ thống đã ghi vào bộ nhớ dài hạn: {key} = {information}"