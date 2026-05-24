import streamlit as st
import datetime
import os
import json

from tools.document_tools import process_and_vectorize
from langchain_core.messages import SystemMessage
# ==========================================
# CẤU HÌNH GIAO DIỆN TRANG
# ==========================================
st.set_page_config(page_title="Trợ lý ảo AI - Đồ án tốt nghiệp", page_icon="🤖", layout="wide")
# ==========================================
# HÀM PHỤ TRỢ: QUẢN LÝ ĐA PHIÊN CHAT
# ==========================================
HISTORY_DIR = "chat_histories"
os.makedirs(HISTORY_DIR, exist_ok=True) # Tự động tạo thư mục nếu chưa có

def get_all_sessions():
    """Lấy danh sách tất cả các file lịch sử, sắp xếp mới nhất lên đầu."""
    files = [f for f in os.listdir(HISTORY_DIR) if f.endswith('.json')]
    files.sort(reverse=True) # Sắp xếp giảm dần theo tên (thời gian)
    return files

def load_session(session_filename):
    """Đọc nội dung của một phiên chat cụ thể."""
    path = os.path.join(HISTORY_DIR, session_filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return [{"role": "assistant", "content": "Chào bạn! Mình là trợ lý ảo. Mình có thể tính toán, giúp bạn kiểm tra/gửi email, quản lý lịch trình, đọc tài liệu và ghi nhớ thông tin quan trọng!"}]

def save_session(session_filename, messages):
    """Lưu phiên chat hiện tại xuống đúng file của nó."""
    path = os.path.join(HISTORY_DIR, session_filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)

# ==========================================
# KHỞI TẠO HỆ THỐNG
# ==========================================
from core.multi_agent import multi_agent_app
from langchain_core.messages import HumanMessage, AIMessage

# Caching giúp AI không bị khởi tạo lại liên tục
@st.cache_resource
def get_agent():
    # Trả về Đồ thị Đa tác nhân
    return multi_agent_app

agent = get_agent()

# Quản lý Phiên bản (Session ID)
if "session_id" not in st.session_state:
    # Nếu chưa có, tự động tạo một phiên mới với tên là thời gian hiện tại
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.session_id = f"Chat_{now_str}.json"

# Quản lý Trạng thái Hội thoại theo Session ID
if "messages" not in st.session_state:
    st.session_state.messages = load_session(st.session_state.session_id)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# CẤU HÌNH GIAO DIỆN SIDEBAR
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/8649/8649603.png", width=100)
    st.title("Về Hệ thống")
    st.write("Trợ lý ảo văn phòng AI Agent. Tích hợp mô hình ngôn ngữ lớn và Google Workspace API.")
    
    # NÚT TẠO CUỘC TRÒ CHUYỆN MỚI
    if st.button("➕ Tạo cuộc trò chuyện mới", type="primary", use_container_width=True):
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.session_id = f"Chat_{now_str}.json"
        st.session_state.messages = load_session(st.session_state.session_id) # Sẽ nạp câu chào mặc định
        st.rerun()

    st.markdown("---")
    st.subheader("🕒 Lịch sử trò chuyện")
    
    # HIỂN THỊ DANH SÁCH CÁC CUỘC TRÒ CHUYỆN CŨ
    sessions = get_all_sessions()
    if not sessions:
        st.caption("Chưa có lịch sử nào.")
    else:
        for sess in sessions:
            display_name = sess.replace(".json", "").replace("_", " ")
            is_active = (sess == st.session_state.session_id)
            button_type = "primary" if is_active else "secondary"
            
            # Chia làm 2 cột: Cột trái to để chứa tên chat, cột phải nhỏ để chứa nút xóa
            col1, col2 = st.columns([4, 2])
            
            with col1:
                # Nút chọn cuộc trò chuyện
                if st.button(f"💬 {display_name}", key=f"btn_{sess}", type=button_type, use_container_width=True):
                    st.session_state.session_id = sess
                    st.session_state.messages = load_session(sess)
                    st.rerun()
            
            with col2:
                # Nút xóa cuộc trò chuyện
                if st.button("🗑️\nXóa", key=f"del_{sess}"):
                    # 1. Xóa file vật lý khỏi ổ cứng
                    file_path = os.path.join(HISTORY_DIR, sess)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    # 2. Nếu file vừa xóa chính là luồng đang mở, phải reset lại màn hình
                    if is_active:
                        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.session_state.session_id = f"Chat_{now_str}.json"
                        st.session_state.messages = load_session(st.session_state.session_id)
                    
                    # 3. Tải lại giao diện
                    st.toast("Đã xóa cuộc trò chuyện!", icon="✅")
                    st.rerun()
                
    st.markdown("---")
    st.subheader("📂 Xử lý Tài liệu (RAG)")
    uploaded_file = st.file_uploader("Tải lên báo cáo (PDF, DOCX)", type=["pdf", "docx"])

    if uploaded_file is not None:
        if st.button("Tiến hành đọc tài liệu", use_container_width=True):
            with st.spinner("Đang phân tích và mã hóa Vector..."):
                # Tạo thư mục temp nếu chưa có
                os.makedirs("temp", exist_ok=True)
                file_path = os.path.join("temp", uploaded_file.name)
                
                # Lưu file tạm xuống ổ cứng
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Gọi hàm xử lý RAG
                success = process_and_vectorize(file_path)
                if success:
                    st.success("Đã học xong tài liệu! Bạn có thể đặt câu hỏi.")
                else:
                    st.error("Có lỗi xảy ra khi đọc file.")
  
    st.markdown("---")
    st.subheader("🕵️ Developer Tools")
    
    if st.button("🔍 Xem Checkpoint (Git Log)", use_container_width=True):
        # 1. Khai báo đúng cái ID của phòng chat hiện tại
        config = {"configurable": {"thread_id": st.session_state.session_id}}
        
        # 2. Rút trích toàn bộ lịch sử snapshot từ Checkpointer
        try:
            history = list(agent.get_state_history(config))
            
            if len(history) > 0:
                st.success(f"Đã bắt được {len(history)} 'commits' (bản chụp trạng thái)!")
                
                # 3. In từng bản snapshot ra màn hình
                for idx, snapshot in enumerate(history):
                    # Lấy ID của bản chụp (giống mã hash của commit)
                    commit_hash = snapshot.config['configurable']['checkpoint_id'][:8]
                    
                    with st.expander(f"Commit #{len(history) - idx} | ID: {commit_hash}"):
                        # Trạng thái tiếp theo (next) của Quản lý
                        next_step = snapshot.values.get('next', 'Không có')
                        st.markdown(f"👉 **Lệnh điều phối (next):** `{next_step}`")
                        
                        # Số lượng tin nhắn đang có trong bộ nhớ thời điểm đó
                        msgs = snapshot.values.get('messages', [])
                        st.markdown(f"💬 **Số tin nhắn trong Graph:** `{len(msgs)}`")
                        
                        # Tùy chọn nâng cao: Bấm để xem toàn bộ Dữ liệu thô (JSON)
                        st.json(snapshot.values)
            else:
                st.info("Chưa có trạng thái nào được lưu. Hãy chat một câu để hệ thống tạo commit!")
        except Exception as e:
            st.error(f"Lỗi truy xuất: {e}")
    
    st.markdown("---")
    st.subheader("💡 Gợi ý câu lệnh:")
    st.info("- Đọc 3 email mới nhất." \
    "\n- Hãy lên lịch họp 'báo cáo đồ án 32' vào 9h đến 10h sáng ngày mai. " \
    "\n- Tính xem kinh phí để mua 10 bộ PC cho phòng làm việc, mỗi bộ 15 triệu. " \
    "\n- Hãy đọc tài liệu 'test.docx/.pdf' (tên tài liệu bạn vừa tải lên hoặc đã có trong cơ sở dữ liệu) cho tôi.")

# ==========================================
# XỬ LÝ TƯƠNG TÁC
# ==========================================
if prompt := st.chat_input("Nhập yêu cầu của bạn..."):
    # 1. Lưu câu của User vào đúng file session hiện tại
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_session(st.session_state.session_id, st.session_state.messages)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
            try:
                # 1. GIỮ LẠI KHỐI NHẬN THỨC THỜI GIAN & TRÍ NHỚ
                now = datetime.datetime.now()
                current_time_str = now.strftime("%d/%m/%Y %H:%M:%S")

                # Gọi trực tiếp hàm load_memory từ file tools
                from tools.memory_tools import load_memory
                
                # Ép kiểu gọi hàm để lấy text trí nhớ
                try:
                    memory_content = load_memory.invoke("")
                    print(f"DEBUG - Trí nhớ nạp được: {memory_content}") # Kiểm tra ở Terminal
                except:
                    memory_content = "Không có thông tin."

                global_context = (
                    f"THÔNG TIN HỆ THỐNG:\n"
                    f"- Hôm nay là: {current_time_str}.\n"
                    f"- Trí nhớ dài hạn của người dùng:\n{memory_content}\n"
                    f"Hãy sử dụng trí nhớ này để xưng hô và cá nhân hóa câu trả lời nếu cần."
                )

                # 2. CHUYỂN ĐỔI CHUẨN DỮ LIỆU SANG LANGCHAIN MESSAGES
                from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
                
                # Bơm bối cảnh chung vào đầu lịch sử dưới dạng SystemMessage
                langchain_history = [SystemMessage(content=global_context)]

                # --- ÁP DỤNG SLIDING WINDOW: CHỈ LẤY 10 TIN NHẮN GẦN NHẤT ---
                MAX_HISTORY = 10
                recent_msgs = st.session_state.messages[-MAX_HISTORY:]
                
                for msg in recent_msgs:
                    if msg["role"] == "user":
                        langchain_history.append(HumanMessage(content=msg["content"]))
                    else:
                        langchain_history.append(AIMessage(content=msg["content"]))
                
                # 3. GỌI HỆ ĐA TÁC NHÂN (SỬ DỤNG STREAMING & STATUS CHI TIẾT)
                final_answer = ""
                
                # Tạo hộp "Thinking..."
                with st.status("🧠 Hệ thống đang tư duy...", expanded=False) as status:
                    
                    for event in agent.stream(
                        {"messages": langchain_history},
                        config={
                            "configurable": {"thread_id": st.session_state.session_id}, # Gắn nhãn ID luồng chạy
                            "recursion_limit": 20
                        }
                    ):
                        for node_name, node_state in event.items():
                            
                            # 3.1. NẾU LÀ QUẢN LÝ (Supervisor)
                            # Quản lý không sinh ra message, chỉ sinh ra biến 'next'
                            if node_name == "supervisor":
                                next_action = node_state.get("next", "Không rõ")
                                st.write(f"👉 *Quản lý quyết định giao tiếp cho:* `{next_action}`")
                                
                            # 3.2. NẾU LÀ THƯ KÝ TỔNG HỢP (Final Node)
                            elif node_name == "final_node":
                                st.write("✨ *Thư ký đang tổng hợp báo cáo cuối cùng...*")
                                # Rút trích kết quả cuối
                                if "messages" in node_state and len(node_state["messages"]) > 0:
                                    last_msg = node_state["messages"][-1]
                                    if isinstance(last_msg.content, list):
                                        final_answer = "".join([item.get("text", "") for item in last_msg.content if isinstance(item, dict) and "text" in item])
                                    else:
                                        final_answer = str(last_msg.content)
                                        
                            # 3.3. NẾU LÀ CÁC NHÂN VIÊN (Worker Agents)
                            else:
                                st.write(f"⚙️ *Nhân viên `{node_name}` đã nộp báo cáo:*")
                                # Lấy tin nhắn cuối cùng (chính là bản báo cáo đã được Đóng dấu Thẻ tên)
                                if "messages" in node_state and len(node_state["messages"]) > 0:
                                    last_msg = node_state["messages"][-1]
                                    
                                    report_content = ""
                                    if isinstance(last_msg.content, list):
                                        report_content = "".join([item.get("text", "") for item in last_msg.content if isinstance(item, dict) and "text" in item])
                                    else:
                                        report_content = str(last_msg.content)
                                    
                                    # HIỂN THỊ CHI TIẾT BÁO CÁO: Dùng st.info để tạo hộp viền màu xanh nhạt
                                    st.info(report_content)
                                    
                                    # Dự phòng cập nhật kết quả
                                    final_answer = report_content
                    
                    # Đóng hộp Thinking lại
                    status.update(label="Đã hoàn tất xử lý!", state="complete", expanded=False)
                
                # 4. HIỂN THỊ KẾT QUẢ TỔNG HỢP RA MÀN HÌNH CHÍNH
                st.markdown(final_answer)
                
                #Lưu câu của Assistant vào đúng file session hiện tại
                st.session_state.messages.append({"role": "assistant", "content": final_answer})
                save_session(st.session_state.session_id, st.session_state.messages)
                
            except Exception as e:
                error_msg = f"Xin lỗi, hệ thống gặp sự cố: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                save_session(st.session_state.session_id, st.session_state.messages)