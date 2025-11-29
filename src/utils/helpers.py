import datetime
import re

def format_currency(amount: float) -> str:
    """Formatea cantidad como moneda"""
    try:
        return f"${amount:,.2f}"
    except:
        return "$0.00"

def format_datetime(dt: datetime.datetime) -> str:
    """Formatea fecha y hora para mostrar"""
    try:
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return ""

def format_date(dt: datetime.date) -> str:
    """Formatea solo fecha"""
    try:
        return dt.strftime("%d/%m/%Y")
    except:
        return ""

def validate_email(email: str) -> bool:
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Valida formato de teléfono"""
    # Acepta formatos como: 123-456-7890, (123) 456-7890, 1234567890
    pattern = r'^[\d\s\-\(\)]{10,15}$'
    return re.match(pattern, phone) is not None
