from langchain_core.tools import tool

@tool
def multiply(a: float, b: float) -> float:
    """Hàm nhân hai số."""
    return a * b

@tool
def add(a: float, b: float) -> float:
    """Hàm cộng hai số."""
    return a + b

@tool
def divide(a: float, b: float) -> str | float:
    """Hàm chia số a cho số b."""
    if b == 0:
        return "Lỗi: Không thể chia cho 0. Vui lòng kiểm tra lại phép tính."
    return a / b

@tool
def minus(a: float, b: float) -> float:
    """Hàm trừ số a cho số b."""
    return a - b