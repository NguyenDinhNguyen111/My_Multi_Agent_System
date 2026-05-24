import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Danh sách SCOPES để xin các quyền cần thiết
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar'
]

# ĐỊNH NGHĨA TÊN FILE TẠI ĐÂY (Dễ dàng thay đổi sau này)
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'             # File token tương ứng sẽ được sinh ra

def main():
    creds = None
    # Kiểm tra xem token của tài khoản đã có chưa
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Nếu chưa có hoặc hết hạn
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"LỖI: Không tìm thấy file {CREDENTIALS_FILE}!")
                return
                
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Lưu token mới
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            print("--- ĐĂNG NHẬP THÀNH CÔNG! ---")
            print(f"File {TOKEN_FILE} đã được tạo.")

if __name__ == '__main__':
    main()