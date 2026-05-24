import operator
import os
from dotenv import load_dotenv
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# -------------------------------------------------------------------
# 1. ĐỊNH NGHĨA TRẠNG THÁI (STATE) CHO ĐỒ THỊ
# -------------------------------------------------------------------
class AgentState(TypedDict):
    # messages: Lưu trữ toàn bộ lịch sử hội thoại (nối tiếp nhau bằng operator.add)
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# -------------------------------------------------------------------
# 2. KHỞI TẠO BỘ NÃO LLM CHUNG
# -------------------------------------------------------------------
# Dùng model siêu nhẹ để đảm bảo tốc độ phản hồi nhanh
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", temperature=0)

print("Đã khởi tạo thành công cấu trúc State cho Multi-Agent.")

# --- HÀM PHỤ TRỢ DÙNG CHUNG: LÀM SẠCH KẾT QUẢ TỪ GEMINI ---
def clean_gemini_output(raw_content) -> str:
    if isinstance(raw_content, list):
        return "".join([item.get("text", "") for item in raw_content if isinstance(item, dict) and "text" in item])
    elif isinstance(raw_content, str):
        return raw_content
    return str(raw_content)

# Bổ sung các thư viện cần thiết
from langgraph.prebuilt import create_react_agent # type: ignore
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage

# Import các tools
from tools.calendar_tools import get_upcoming_events, create_calendar_event
from tools.gmail_tools import get_gmail_tools
from tools.document_tools import query_document
from tools.memory_tools import save_long_term_memory
from tools.math_tools import add, minus, multiply, divide

# -------------------------------------------------------------------
# 3. HÀM BỌC TÁC NHÂN (NODE WRAPPER)
# -------------------------------------------------------------------
def agent_node(state, agent, name, system_instruction):
    # Nhét SystemMessage vào đầu danh sách lịch sử chat
    messages = [SystemMessage(content=system_instruction)] + state["messages"]
    
    # Giao cho AI xử lý
    result = agent.invoke(
        {"messages": messages}, 
        config={"recursion_limit": 15}
    )
    last_message = result["messages"][-1]

    parsed_content = clean_gemini_output(last_message.content)
    
    stamped_content = f"=== BÁO CÁO TỪ {name.upper()} ===\n{parsed_content}"
    
    from langchain_core.messages import AIMessage
    stamped_message = AIMessage(content=stamped_content, name=name)
    
    return {
        "messages": [stamped_message]
    }

# -------------------------------------------------------------------
# 4. KHỞI TẠO ĐỘI NGŨ NHÂN VIÊN CHUYÊN TRÁCH (WORKER AGENTS)
# -------------------------------------------------------------------

# 1. Nhân viên Lịch trình (Chỉ cầm tool Calendar)
calendar_agent = create_react_agent(# type: ignore
    llm, 
    tools=[get_upcoming_events, create_calendar_event]
)
# 2. Nhân viên Thư ký (Chỉ cầm tool Gmail)
mail_agent = create_react_agent(# type: ignore
    llm, 
    tools=get_gmail_tools()
)
# 3. Nhân viên Tri thức (Cầm tool RAG và Memory)
document_agent = create_react_agent(# type: ignore
    llm, 
    tools=[query_document, save_long_term_memory]
)
# 4. Nhân viên Kế toán (Chỉ cầm tool Toán học)
math_agent = create_react_agent(# type: ignore
    llm, 
    tools=[add, minus, multiply, divide]
)

print("Đã tuyển dụng xong đội ngũ 4 Nhân viên!")

from typing import Literal
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel

# -------------------------------------------------------------------
# 5. TẠO BỘ NÃO QUẢN LÝ (SUPERVISOR)
# -------------------------------------------------------------------

# Danh sách các nhân viên dưới quyền
members = ["calendar_agent", "mail_agent", "document_agent", "math_agent"]

# Khai báo các lựa chọn định tuyến (Routing)
options = ["FINISH"] + members

# SỬ DỤNG PYDANTIC ĐỂ ÉP KIỂU DỮ LIỆU ĐẦU RA
# Điều này cực kỳ quan trọng: Ép AI Quản lý phải trả về đúng 1 trong 5 từ khóa, 
# không được nói dông dài ("Tôi nghĩ nên giao cho...") để tránh làm sập hệ thống.
class routeResponse(BaseModel):
    next: Literal["FINISH", "calendar_agent", "mail_agent", "document_agent", "math_agent"]

system_prompt = (
    "Bạn là Quản lý (Supervisor) của một đội trợ lý ảo. Đội ngũ gồm: {members}. "
    "LUẬT ĐIỀU PHỐI (BẮT BUỘC TUÂN THỦ):\n"
    "1. CHIA NHỎ: Phân tích yêu cầu và liệt kê rõ các nhiệm vụ, rồi giao cho đúng nhân viên làm đúng chuyên môn: mail_agent (Email), calendar_agent (Lịch), document_agent (Tài liệu VÀ Ghi nhớ thông tin), math_agent (Tính toán số học).\n"
    "2. KIỂM TRA THẺ TÊN (QUAN TRỌNG): Hãy nhìn vào các dòng chữ '=== BÁO CÁO TỪ... ===' trong lịch sử chat để biết ai đã làm gì. Nếu người dùng yêu cầu đọc tài liệu,"
    "BẮT BUỘC phải có báo cáo từ DOCUMENT_AGENT. Nếu chỉ có báo cáo từ MAIL_AGENT, nghĩa là phần tài liệu CHƯA LÀM.\n"
    "3. TỔNG KẾT: TRẢ VỀ 'FINISH' KHI MỌI NHIỆM VỤ ĐỀU ĐÃ ĐƯỢC BÁO CÁO BỞI ĐÚNG NHÂN VIÊN CHUYÊN TRÁCH."
)
# Lắp ráp Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="messages"),
    (
        "system",
        "Dựa trên cuộc hội thoại trên, ai là người tiếp theo nên hành động? "
        "Chỉ trả lời bằng một trong các lựa chọn sau: {options}."
    ),
]).partial(options=str(options), members=", ".join(members))

# Gắn cấu trúc bắt buộc (Structured Output) vào lõi LLM
supervisor_chain = prompt | llm.with_structured_output(routeResponse)

def supervisor_node(state):
    # Quản lý suy nghĩ và ra quyết định
    decision = supervisor_chain.invoke(state)

    # Lấy chính xác chuỗi kết quả (ví dụ: "FINISH") và lưu vào biến next
    return {"next": decision.next}

print("Đã bổ nhiệm xong vị trí Quản lý (Supervisor)!")

def final_node(state):
    print("   ✨ Thư ký đang xử lý cuối cùng...")
    messages = state["messages"]
    
    # 1. Tách System Message (Trí nhớ) ra khỏi lịch sử
    system_msg = messages[0] # Luôn là SystemMessage(content=global_context)
    chat_history = messages[1:] # Các tin nhắn còn lại
    # 2. Trích xuất các báo cáo thô (nếu có)
    reports_text = ""
    from langchain_core.messages import AIMessage
    for msg in messages:
        if isinstance(msg, AIMessage) and "=== BÁO CÁO TỪ" in str(msg.content):
            reports_text += str(msg.content) + "\n\n"
            
    # 3. Lấy câu hỏi cuối cùng của người dùng để biết họ vừa hỏi gì
    user_query = "Không rõ câu hỏi."
    for msg in reversed(chat_history):
        if msg.type == "human": # Tìm tin nhắn gần nhất của user
            user_query = str(msg.content)
            break

    # 4. CHIA LUỒNG XỬ LÝ CHO THƯ KÝ
    if not reports_text.strip():
        # TRƯỜNG HỢP A: Không có báo cáo nào (Quản lý hô FINISH luôn)
        # Thư ký sẽ tự trả lời dựa vào Trí nhớ trong global_context
        print("   💬 Trả lời trực tiếp dựa trên Trí nhớ / Kiến thức chung...")
        summary_prompt = (
            f"Người dùng vừa hỏi: '{user_query}'.\n"
            "Nhiệm vụ: Hãy trả lời dựa TRỰC TIẾP vào 'Trí nhớ dài hạn/global_context' trong System Prompt bên trên. "
            "Nếu trong trí nhớ có thông tin, hãy trả lời chính xác. KHÔNG ĐƯỢC TỰ BỊA. "
            "Nếu không có thông tin, hãy lịch sự báo rằng bạn chưa được ghi nhớ điều này."
        )
    else:
        # TRƯỜNG HỢP B: Có báo cáo từ các Agent (Quy trình chuẩn)
        print("   📝 Đang tổng hợp báo cáo chuyên sâu...")
        summary_prompt = (
            "Bạn là Chuyên viên Tổng hợp Cao cấp. Nhiệm vụ của bạn là biến các báo cáo thô "
            "thành một báo cáo kết quả hoàn chỉnh, chuyên nghiệp và đầy đủ chi tiết cho người dùng.\n\n"
            "LUẬT BẮT BUỘC:\n"
            "1. TẬP TRUNG VÀO BÁO CÁO THÔ: CHỈ tổng hợp những thông tin nằm trong phần '=== DỮ LIỆU CẦN TỔNG HỢP ===' bên dưới, "
            "TUYỆT ĐỐI KHÔNG tự ý liệt kê hay bê nguyên các thông tin cũ trong 'Trí nhớ dài hạn/global_context' ra báo cáo nếu người dùng không yêu cầu.\n"
            "2. KHÔNG ĐƯỢC TÓM TẮT QUÁ MỨC: Hãy giữ lại các thông tin chi tiết như tên người, "
            "các tính năng kỹ thuật, các mốc thời gian và mục tiêu dự án. Đừng viết chung chung.\n"
            "3. ĐỊNH DẠNG MARKDOWN: Sử dụng tiêu đề (###), danh sách gạch đầu dòng và chữ in đậm "
            "để phân tách các hạng mục công việc cho phù hợp theo === DỮ LIỆU CẦN TỔNG HỢP === (ví dụ Email, Tài liệu, Lịch trình, v.v.).\n"
            f"4. TRÌNH BÀY: Xưng 'mình' gọi 'bạn'. Bắt đầu bằng lời chào và tóm tắt NGẮN GỌN lại yêu cầu của người dùng để xác nhận (dựa trên câu hỏi: '{user_query}'). Tiếp theo là báo cáo tổng hợp. Kết thúc bằng một lời chúc hoặc dặn dò.\n"
            "5. LOẠI BỎ RÁC: Tuyệt đối bỏ qua các câu đính chính chuyên môn của Agent (ví dụ: 'tôi không thể làm...', 'tôi là chuyên gia email...').\n"
            "6. GIỮ NGUYÊN LINK: Các đường link URL phải được trình bày rõ ràng, dễ bấm.\n\n"
            f"=== DỮ LIỆU CẦN TỔNG HỢP ===\n{reports_text}"
        )
    
    # 5. GỌI LLM ĐỂ TRẢ LỜI
    from langchain_core.messages import HumanMessage
    final_prompt = [system_msg] + chat_history + [HumanMessage(content=summary_prompt)]
    
    response = llm.invoke(final_prompt)
    # 6. LÀM SẠCH VÀ TRẢ VỀ
    parsed_content = clean_gemini_output(response.content)
    
    return {"messages": [AIMessage(content=parsed_content.strip())]}

import functools
from langgraph.graph import StateGraph, START, END

# -------------------------------------------------------------------
# 6. XÂY DỰNG ĐỒ THỊ LUỒNG (GRAPH ROUTING)
# -------------------------------------------------------------------
workflow = StateGraph(AgentState)

# 6.1. Bọc các nhân viên lại thành các Node tiêu chuẩn và gắn mô tả công việc
# Dùng functools.partial để gắn cố định "biển tên" cho từng nhân viên
calendar_node = functools.partial(
    agent_node, 
    agent=calendar_agent, 
    name="calendar_agent",
    system_instruction=(
        "Bạn là Chuyên gia Lịch. CHỈ làm việc về lịch. Chỉ lọc ra yêu cầu người dùng có liên quan đến mình để xử lý. "
        "BẮT BUỘC DÙNG CÔNG CỤ VÀ CHỜ KẾT QUẢ: Bạn BẮT BUỘC phải gọi công cụ (get_upcoming_events hoặc create_calendar_event) và dùng ĐÚNG dữ liệu công cụ trả về để báo cáo. TUYỆT ĐỐI KHÔNG tự bịa ra link mẫu (ví dụ: example_event_link) hay ảo giác ra sự kiện.\n"
        "ĐÍNH KÈM LINK THẬT: Công cụ sẽ luôn trả về link thật. Bạn phải đưa link đó vào báo cáo.\n"
        "Nếu người dùng có yêu cầu khác (tóm tắt email, đọc tài liệu, ghi nhớ,...), hãy bỏ qua và"
        "KHÔNG ĐƯỢC ĐỀ CẬP đến chúng trong câu trả lời dưới bất kỳ hình thức nào. "
        "Câu trả lời của bạn chỉ được chứa thông tin liên quan về lịch. Nếu có câu trả lời, BẮT BUỘC phải viết ra, không được để trống báo cáo!"
    )
)

mail_node = functools.partial(
    agent_node, 
    agent=mail_agent, 
    name="mail_agent",
    system_instruction=(
        "Bạn là Chuyên gia Email. CHỈ làm việc về email. Chỉ lọc ra yêu cầu người dùng có liên quan đến mình để xử lý. "
        "Nếu người dùng có yêu cầu khác (đọc tài liệu, lịch, ghi nhớ,...), hãy bỏ qua và"
        "KHÔNG ĐƯỢC ĐỀ CẬP đến chúng trong câu trả lời dưới bất kỳ hình thức nào. "
        "Câu trả lời của bạn chỉ được chứa thông tin liên quan về email. Nếu có câu trả lời, BẮT BUỘC phải viết ra, không được để trống báo cáo!"
    )
)

document_node = functools.partial(
    agent_node, 
    agent=document_agent, 
    name="document_agent",
    system_instruction=(
        "Bạn là Chuyên gia Tri thức kiêm Quản lý Trí nhớ. BẠN CHỈ ĐƯỢC PHÉP làm 2 việc: Đọc tài liệu và Ghi nhớ thông tin.\n"
        "LUẬT 'KỶ LUẬT THÉP' (TUYỆT ĐỐI TUÂN THỦ):\n"
        "1. LỜ ĐI YÊU CẦU NGOÀI CHUYÊN MÔN: Nếu người dùng yêu cầu kiểm tra email, lên lịch họp, hay TÍNH TOÁN TOÁN HỌC, bạn BẮT BUỘC PHẢI LỜ ĐI như chưa từng đọc thấy. TUYỆT ĐỐI KHÔNG tự tính toán hay trả lời thay các agent khác.\n"
        "2. KHÔNG BAO ĐỒNG: Báo cáo của bạn CHỈ được phép chứa thông tin trích xuất từ tài liệu hoặc xác nhận đã lưu trí nhớ. Cấm lặp lại các thông tin không liên quan.\n"
        "3. XỬ LÝ ĐA TÁC VỤ: Được phép dùng nhiều tool liên tiếp nếu có nhiều yêu cầu về tài liệu/trí nhớ.\n"
        "4. TÌM KIẾM THEO TÊN FILE: Khi gọi `query_document`, nếu người dùng hỏi chung chung, TUYỆT ĐỐI KHÔNG truyền tham số `file_name` (để trống).\n"
        "5. ĐỌC TÀI LIỆU: Bắt buộc dùng `query_document`. Trả lời dựa trên kết quả của tool.\n"
        "6. GHI NHỚ: Khi được yêu cầu phải ghi nhớ hoặc lưu trữ nội dung cụ thể, BẮT BUỘC dùng tool `save_long_term_memory`.\n"
        "7. KẾT LUẬN: Sau khi dùng xong tool, báo cáo ngắn gọn đúng trọng tâm chuyên môn của mình."
    )
)
math_node = functools.partial(
    agent_node, 
    agent=math_agent, 
    name="math_agent",
    system_instruction=(
        "Bạn là Chuyên gia Tính toán. CHỈ làm việc với các con số và phép tính. Chỉ lọc ra yêu cầu người dùng có liên quan đến mình để xử lý."
        "Nếu người dùng có yêu cầu khác (đọc tài liệu, lịch, ghi nhớ,...), hãy bỏ qua và"
        "KHÔNG ĐƯỢC ĐỀ CẬP đến chúng trong câu trả lời dưới bất kỳ hình thức nào. "
        "LUẬT BẮT BUỘC:\n"
        "1. SỬ DỤNG CÔNG CỤ: Bắt buộc gọi tool (add, minus, multiply, divide) để tính toán, KHÔNG TỰ NHẨM.\n"
        "2. XỬ LÝ ĐA BƯỚC (CHAIN OF THOUGHT): Nếu bài toán có nhiều bước, BẠN ĐƯỢC PHÉP gọi nhiều tool liên tiếp (ví dụ: lấy kết quả của phép cộng để làm tham số cho phép nhân tiếp theo) cho đến khi ra kết quả cuối cùng.\n"
        "3. CHỐNG LẶP VÔ TẬN (QUAN TRỌNG): TUYỆT ĐỐI KHÔNG gọi đi gọi lại cùng một phép tính với cùng một tham số nếu đã có kết quả. Khi đã tính ra đáp án cuối cùng của toàn bộ yêu cầu, phải kết thúc ngay.\n"
    )
)
# 6.2. Đưa tất cả vào Đồ thị
workflow.add_node("calendar_agent", calendar_node)
workflow.add_node("mail_agent", mail_node)
workflow.add_node("document_agent", document_node)
workflow.add_node("math_agent", math_node)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("final_node", final_node)

# 6.3. Vẽ đường đi (Edges)
# LUẬT 1: Mọi nhân viên làm xong việc đều phải trả kết quả về cho Quản lý
for member in members:
    workflow.add_edge(member, "supervisor")

# LUẬT 2: Quản lý là người nắm quyền sinh sát, quyết định đi đâu tiếp theo
# Tạo bản đồ định tuyến (Conditional Map)
conditional_map = {k: k for k in members}
conditional_map["FINISH"] = "final_node" # Nếu Quản lý bảo FINISH thì kết thúc chu trình

workflow.add_conditional_edges(
    "supervisor", 
    lambda state: state["next"], # Đọc biến 'next' (FINISH, mail_agent...) mà Quản lý vừa sinh ra
    conditional_map
)

# LUẬT 3: Điểm bắt đầu của ứng dụng luôn là phòng của Quản lý
workflow.add_edge(START, "supervisor")
# Thêm đường từ final_node ra END
workflow.add_edge("final_node", END)

# 6.4. Đóng gói (Compile) toàn bộ đồ thị thành một ứng dụng hoàn chỉnh
from langgraph.checkpoint.memory import MemorySaver

# Khởi tạo bộ nhớ tạm thời lưu vết trạng thái đồ thị
memory = MemorySaver()

# Biên dịch Đồ thị kèm theo hệ thống Checkpointer
multi_agent_app = workflow.compile(checkpointer=memory)

print("Đã biên dịch thành công Hệ Đa Tác Nhân với tính năng Memory Checkpointer!")