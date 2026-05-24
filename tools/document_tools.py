import os
from typing import Optional
from langchain_core.tools import tool
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

# Nơi lưu trữ Vector DB cục bộ
INDEX_PATH = "local_faiss_index"

def process_and_vectorize(file_path: str) -> bool:
    """Hàm dành cho giao diện UI: Đọc file và lưu vào FAISS Vector DB."""
    try:
        # 1. Đọc file
        print("\n--- BẮT ĐẦU XỬ LÝ FILE ---")
        print(f"1. Đang nạp file: {file_path}")
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx'):
            loader = Docx2txtLoader(file_path)
        else:
            return False
            
        docs = loader.load()
       
        print("2. Đã nạp xong. Đang cắt văn bản...")
        # 2. Cắt nhỏ văn bản (Chunking)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        
        print(f"3. Đã cắt thành {len(splits)} đoạn (chunks). Đang gọi API Google Embedding...")
        # 3. Mã hóa (Embedding) và lưu vào FAISS
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

        # 4. Lưu trữ thông minh (Gộp Vector thay vì ghi đè)
        if os.path.exists(os.path.join(INDEX_PATH, "index.faiss")):
            print("4. Đã thấy Tủ tài liệu cũ. Đang chuẩn bị gộp...")
            # Nạp tủ tài liệu cũ
            existing_vectorstore = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
            # Tạo tủ vector mới cho file hiện tại
            new_vectorstore = FAISS.from_documents(splits, embeddings)
            # GỘP tủ mới vào tủ cũ
            existing_vectorstore.merge_from(new_vectorstore)
            # Cất lại toàn bộ vào ổ cứng
            existing_vectorstore.save_local(INDEX_PATH)
            print("5. Đã gộp thêm tài liệu mới vào kho tri thức.")
        else:
            # Nếu chưa có tủ, tạo tủ mới tinh
            print("4. Chưa có Tủ tài liệu. Đang tạo Tủ mới...")
            vectorstore = FAISS.from_documents(splits, embeddings)
            vectorstore.save_local(INDEX_PATH)
            print("5. Đã khởi tạo kho tri thức mới.")
            
        print("--- HOÀN TẤT ---")    
        return True
    except Exception as e:
        print(f"Lỗi xử lý file: {e}")
        return False

@tool
def query_document(query: str, file_name: Optional[str] = None) -> str:
    """
    Hàm dùng để tìm kiếm và trích xuất thông tin từ tài liệu đã tải lên.
    - query: Câu hỏi hoặc từ khóa cần tìm (Bắt buộc).
    - file_name: Tên file cụ thể nếu người dùng có nhắc đến (Ví dụ: 'test.docx', 'Quy_trinh.pdf'). Để trống nếu người dùng hỏi chung chung.
    """
    if not os.path.exists(INDEX_PATH):
        return "Chưa có tài liệu nào được tải lên hệ thống."
        
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vectorstore = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        
        # CHỨC NĂNG MỚI: Lọc theo Metadata (Tên file)
        if file_name and str(file_name).strip().lower() not in ["none", "null", ""]:
            source_path = os.path.join("temp", file_name)
            try:
                docs = vectorstore.similarity_search(query, k=3, filter={"source": source_path})
            except Exception: docs = vectorstore.similarity_search(query, k=3) # fallback
        else:
            docs = vectorstore.similarity_search(query, k=3)
            
        if not docs:
            return f"Không tìm thấy đoạn văn nào khớp với từ khóa trong tài liệu (File lọc: {file_name if file_name else 'Toàn bộ hệ thống'})."

        context = "\n\n---\n\n".join([doc.page_content for doc in docs])
        return f"Kết quả tìm kiếm:\n{context}"
        
    except Exception as e:
        return f"Lỗi khi đọc Vector DB: {str(e)}"
    