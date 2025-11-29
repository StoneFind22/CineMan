from dataclasses import dataclass
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum

# ================================
# ENUMERACIONES
# ================================

class MovieGenre(Enum):
    """Géneros de películas"""
    ACCION = "Acción"
    AVENTURA = "Aventura"
    COMEDIA = "Comedia"
    DRAMA = "Drama"
    TERROR = "Terror"
    CIENCIA_FICCION = "Ciencia Ficción"
    FANTASIA = "Fantasía"
    ROMANCE = "Romance"
    THRILLER = "Thriller"
    ANIMACION = "Animación"
    DOCUMENTAL = "Documental"
    MUSICAL = "Musical"

class MovieRating(Enum):
    """Clasificaciones de películas"""
    AA = "AA - Apta para todo público"
    A = "A - Apta para mayores de 12 años"
    B = "B - Apta para mayores de 15 años"
    C = "C - Apta para mayores de 18 años"
    D = "D - Sólo para adultos"

class SeatStatus(Enum):
    """Estados de asientos"""
    DISPONIBLE = "Disponible"
    OCUPADO = "Ocupado"
    MANTENIMIENTO = "Mantenimiento"
    BLOQUEADO = "Bloqueado"

class TicketType(Enum):
    """Tipos de boletos"""
    GENERAL = "General"
    ESTUDIANTE = "Estudiante"
    TERCERA_EDAD = "Tercera Edad"
    NIÑO = "Niño"
    VIP = "VIP"


# ================================
# MODELOS DE DATOS
# ================================

@dataclass
class Movie:
    """Modelo de película"""
    id: int = None
    title: str = ""
    description: str = ""
    genre: str = ""
    rating: str = ""
    duration_minutes: int = 0
    director: str = ""
    cast: str = ""
    release_date: date = None
    poster_url: str = ""
    trailer_url: str = ""
    is_active: bool = True
    created_date: datetime = None


@dataclass
class Theater:
    """Modelo de sala de cine"""
    id: int = None
    name: str = ""
    total_seats: int = 0
    rows: int = 0
    seats_per_row: int = 0
    has_vip_section: bool = False
    vip_seats: int = 0
    is_active: bool = True
    created_date: datetime = None


@dataclass
class Showtime:
    """Modelo de función de película"""
    id: int = None
    movie_id: int = None
    theater_id: int = None
    show_date: date = None
    show_time: time = None
    price_general: Decimal = Decimal('0.00')
    price_student: Decimal = Decimal('0.00')
    price_senior: Decimal = Decimal('0.00')
    price_child: Decimal = Decimal('0.00')
    price_vip: Decimal = Decimal('0.00')
    available_seats: int = 0
    is_active: bool = True
    created_date: datetime = None


@dataclass
class Customer:
    """Modelo de cliente"""
    id: int = None
    full_name: str = ""
    email: str = ""
    phone: str = ""
    document_number: str = ""
    birth_date: date = None
    is_frequent_customer: bool = False
    total_purchases: Decimal = Decimal('0.00')
    created_date: datetime = None


@dataclass
class Sale:
    """Modelo de venta"""
    id: int = None
    customer_id: int = None
    user_id: int = None
    sale_date: datetime = None
    total_amount: Decimal = Decimal('0.00')
    payment_method: str = ""
    discount_amount: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    status: str = "COMPLETED"
    notes: str = ""


@dataclass
class Ticket:
    """Modelo de boleto"""
    id: int = None
    sale_id: int = None
    showtime_id: int = None
    seat_number: str = ""
    ticket_type: str = ""
    price: Decimal = Decimal('0.00')
    qr_code: str = ""
    is_used: bool = False
    used_date: datetime = None
