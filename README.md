# 🤖 Trợ lý ảo Hỗ trợ Công tác Văn phòng (Multi-Agent System)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![Google API](https://img.shields.io/badge/Integration-Google_Workspace-green)

> **Đồ án Tốt nghiệp** | Khoa Công nghệ Thông tin - Đại học Nha Trang
> 
> **Sinh viên thực hiện:** Nguyễn Đình Nguyên (MSSV: 64131537)
> 
> **Giảng viên hướng dẫn:** TS. Nguyễn Đình Hưng

## 📖 Tổng quan đề tài
Dự án ứng dụng Trí tuệ Nhân tạo phát triển hệ thống trợ lý ảo phục vụ tự động hóa quy trình văn phòng. Hệ thống được xây dựng dựa trên kiến trúc **Đa tác nhân (Multi-Agent System)** sử dụng LangGraph và mô hình ngôn ngữ lớn (Gemini), kết hợp cùng khung lý thuyết thao tác-suy luận **ReAct**.

Thay vì một mô hình đơn lẻ, hệ thống bao gồm một **Tác nhân Quản lý (Supervisor)** điều phối luồng công việc cho 4 **Tác nhân Chuyên trách (Workers)**, cho phép xử lý các tác vụ phức tạp, đa bước một cách chính xác và bảo mật.

## ✨ Tính năng cốt lõi (Core Agents)
- 🗂️ **Document Agent (Chuyên gia Tri thức):** Tìm kiếm, trích xuất thông tin từ tài liệu nội bộ (PDF/DOCX) dựa trên công nghệ RAG kết hợp cơ sở dữ liệu vector FAISS.
- 📧 **Mail Agent (Chuyên gia Email):** Phân tích, tóm tắt và tự động gửi email thông qua tích hợp Gmail API.
- 📅 **Calendar Agent (Chuyên gia Lịch trình):** Tra cứu sự kiện và thiết lập lịch họp tự động qua Google Calendar API.
- 🧮 **Math Agent (Chuyên gia Tính toán):** Xử lý các phép toán số học chính xác thông qua Tool Calling, giảm thiểu đáng kể hiện tượng "ảo giác" (hallucination) của LLM trong tính toán.
- 🧠 **Bộ nhớ dài hạn (Long-term Memory):** Lưu trữ và truy xuất thông tin cá nhân hóa (tên, sở thích người dùng) qua tệp JSON cục bộ, cho phép hệ thống cá nhân hóa phản hồi giữa các phiên làm việc.

## ⚙️ Kiến trúc Hệ thống
- **Mô hình ngôn ngữ:** Google Gemini (qua Gemini API)
- **Cơ chế điều phối:** Đồ thị Trạng thái có hướng (Directed State Graph) — LangGraph
- **Cấu trúc tác nhân:** 1 Supervisor → 4 Worker Agents → 1 Thư ký tổng hợp
- **Khung suy luận:** ReAct (Reasoning + Acting) với chu trình Thought → Action → Observation
- **Truy xuất tài liệu:** RAG pipeline — Chunking → Embedding → FAISS Vector Search
- **Giao diện:** Streamlit

## 🚀 Hướng dẫn cài đặt

**1. Clone kho lưu trữ:**
```bash
git clone https://github.com/NguyenDinhNguyen111/My_Multi_Agent_System.git
cd My_Multi_Agent_System
```

**2. Cài đặt môi trường:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**3. Thiết lập biến môi trường:**

Tạo file `.env` tại thư mục gốc và cung cấp API Key:
```
GOOGLE_API_KEY="your_gemini_api_key_here"
```

**4. Thiết lập Google Workspace API:**

Kích hoạt Gmail API và Google Calendar API trên Google Cloud Console.
Thiết lập OAuth, Scopes, Test Users rồi tạo credentials. (chi tiết xin đọc file SETUP_GOOGLE_API.md)
Tải file `credentials.json` và đặt vào thư mục gốc của dự án.
Chạy lần đầu để xác thực OAuth 2.0:
```bash
python setup_auth.py
```

**5. Khởi chạy ứng dụng:**
```bash
streamlit run app.py
```