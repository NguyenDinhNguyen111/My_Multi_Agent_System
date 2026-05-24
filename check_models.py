import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Tải API Key từ file .env
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("🔍 DANH SÁCH CÁC MODEL KHẢ DỤNG CHO TÀI KHOẢN CỦA BẠN:")
print("=" * 60)

# 2. Gọi hàm list_models() và duyệt qua kết quả
for m in genai.list_models():
    # Chỉ lọc những model có thể Tạo văn bản (generateContent) hoặc Đọc tài liệu (embedContent)
    if 'generateContent' in m.supported_generation_methods or 'embedContent' in m.supported_generation_methods:
        print(f"Tên Model: {m.name}")
        print(f"Chức năng hỗ trợ: {m.supported_generation_methods}")
        print("-" * 60)