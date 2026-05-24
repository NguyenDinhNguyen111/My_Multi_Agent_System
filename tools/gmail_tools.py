from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.tools.gmail.utils import build_resource_service, get_gmail_credentials

def get_gmail_tools():
    """Hàm lấy danh sách các công cụ tương tác với Gmail."""
    credentials = get_gmail_credentials(
        token_file="token.json", 
        scopes=[
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/calendar'
        ],
        client_secrets_file="credentials.json", 
    )
    api_resource = build_resource_service(credentials=credentials)
    toolkit = GmailToolkit(api_resource=api_resource)
    return toolkit.get_tools()