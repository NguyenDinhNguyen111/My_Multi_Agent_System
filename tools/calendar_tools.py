import datetime
from langchain_core.tools import tool
from googleapiclient.discovery import build
from langchain_community.tools.gmail.utils import get_gmail_credentials

# Dùng chung credentials để khởi tạo service Calendar
credentials = get_gmail_credentials(
    token_file="token.json", 
    scopes=[
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/calendar'
    ],
    client_secrets_file="credentials.json", 
)
calendar_service = build('calendar', 'v3', credentials=credentials)

@tool
def get_upcoming_events(max_results: int = 5) -> str:
    """Hàm kiểm tra lịch trình. Trả về danh sách các sự kiện sắp tới trên Google Calendar."""
    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = calendar_service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=max_results, singleEvents=True,
            orderBy='startTime').execute()
        events = events_result.get('items', [])
        
        if not events:
            return "Không có lịch trình hoặc sự kiện nào sắp tới."
        
        result = "Các sự kiện sắp tới:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'Sự kiện không tên')
            event_link = event.get('htmlLink', 'Không có link')
            result += f"- Tên: {summary} | Bắt đầu: {start} | Link: {event_link}\n"
        return result
    except Exception as e:
        return f"Lỗi khi truy xuất Google Calendar: {str(e)}"

@tool
def create_calendar_event(summary: str, start_datetime: str, end_datetime: str, description: str = "", attendee_emails: str = "") -> str:
    """
    Hàm tạo sự kiện/lịch họp mới trên Google Calendar.
    Tham số:
    - summary: Tiêu đề sự kiện.
    - start_datetime: Thời gian bắt đầu. BẮT BUỘC định dạng ISO 8601 kèm múi giờ Việt Nam +07:00 (VD: 2026-05-06T09:00:00+07:00).
    - end_datetime: Thời gian kết thúc. BẮT BUỘC định dạng ISO 8601 kèm múi giờ Việt Nam +07:00 (VD: 2026-05-06T10:00:00+07:00).
    - description: Nội dung/Mô tả chi tiết sự kiện (không bắt buộc).
    - attendee_emails: Danh sách email người tham dự, cách nhau bằng dấu phẩy (VD: 'a@gmail.com, b@gmail.com'). Để trống nếu không có.
    """
    try:
        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_datetime, 'timeZone': 'Asia/Ho_Chi_Minh'},
            'end': {'dateTime': end_datetime, 'timeZone': 'Asia/Ho_Chi_Minh'},
        }
        
        # Xử lý danh sách khách mời nếu có
        if attendee_emails:
            emails = [email.strip() for email in attendee_emails.split(',')]
            event['attendees'] = [{'email': email} for email in emails]
            
        # Thêm sendUpdates='all' để Google tự động gửi email thông báo cho khách mời
        event_result = calendar_service.events().insert(
            calendarId='primary', 
            body=event, 
            sendUpdates='all'
        ).execute()
        
        return f"Đã tạo thành công sự kiện! Link xem lịch: {event_result.get('htmlLink')}"
    except Exception as e:
        return f"Lỗi khi tạo sự kiện: {str(e)}"