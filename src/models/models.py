from dataclasses import dataclass, field
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import List, Optional

# ================================
# ENUMERACIONES
# ================================

class MovieStatus(Enum):
    ACTIVE = "Active"
    ARCHIVED = "Archived"
    COMING_SOON = "Coming Soon"

class SeatTypeName(Enum):
    GENERAL = "General"
    VIP = "VIP"
    DISCAPACITADOS = "Discapacitados"

class SeatStatus(Enum):
    ACTIVE = "Active"
    BROKEN = "Broken"
    MAINTENANCE = "Maintenance"

class ProjectionType(Enum):
    D2 = "2D"
    D3 = "3D"
    IMAX = "IMAX"

class AudioType(Enum):
    SUB = "SUB"
    DUB = "DUB"
    ORIGINAL = "ORIGINAL"

class ProductType(Enum):
    SIMPLE = "SIMPLE"
    COMBO = "COMBO"
    SERVICE = "SERVICE"

class StockMovementType(Enum):
    SALE = "SALE"
    RESTOCK = "RESTOCK"
    ADJUSTMENT = "ADJUSTMENT"
    LOSS = "LOSS"

# ================================
# MODELOS DE DATOS (DATACLASSES)
# ================================

@dataclass
class Movie:
    """Modelo de película (Catálogo)"""
    id: Optional[int] = None
    title: str = ""
    original_title: str = ""
    duration_minutes: int = 0
    rating: str = "" # G, PG, R, etc.
    genre: str = ""
    synopsis: str = ""
    poster_url: str = ""
    trailer_url: str = ""
    status: str = MovieStatus.ACTIVE.value
    created_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

@dataclass
class Theater:
    """Modelo de sala de cine"""
    id: Optional[int] = None
    name: str = ""
    total_capacity: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None

@dataclass
class SeatType:
    """Modelo para tipos de asiento"""
    id: int
    name: str
    price_modifier: Decimal

@dataclass
class Seat:
    """Modelo de asiento físico"""
    id: Optional[int] = None
    theater_id: int = 0
    row_label: str = ""
    number: int = 0
    seat_type_id: int = 0
    status: str = SeatStatus.ACTIVE.value
    x_position: int = 0
    y_position: int = 0
    # Campos auxiliares para UI
    seat_type_name: str = ""
    price_modifier: Decimal = Decimal('1.00')

@dataclass
class PriceProfile:
    """Perfil de precios (ej: Matinee)"""
    id: Optional[int] = None
    name: str = ""
    base_price_general: Decimal = Decimal('0.00')
    base_price_child: Decimal = Decimal('0.00')
    base_price_senior: Decimal = Decimal('0.00')
    is_active: bool = True

@dataclass
class Showtime:
    """Modelo de función programada"""
    id: Optional[int] = None
    movie_id: int = 0
    theater_id: int = 0
    price_profile_id: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    projection_type: str = ProjectionType.D2.value
    audio_type: str = AudioType.DUB.value
    status: str = "OPEN"
    # Campos auxiliares (joins)
    movie_title: str = ""
    theater_name: str = ""

@dataclass
class InventoryItem:
    """Insumo de inventario (Stock físico)"""
    id: Optional[int] = None
    name: str = ""
    unit: str = "" # kg, lt, unit
    current_stock: Decimal = Decimal('0.000')
    reorder_point: Decimal = Decimal('0.000')
    cost_per_unit: Decimal = Decimal('0.00')

@dataclass
class Product:
    """Producto de venta (Confitería)"""
    id: Optional[int] = None
    category_id: int = 0
    name: str = ""
    description: str = ""
    price: Decimal = Decimal('0.00')
    product_type: str = ProductType.SIMPLE.value
    track_stock: bool = True
    image_url: str = ""
    is_active: bool = True
    # Campos auxiliares
    category_name: str = ""

@dataclass
class Sale:
    """Venta realizada"""
    id: Optional[int] = None
    user_id: int = 0
    customer_id: Optional[int] = None
    total_amount: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    payment_method: str = ""
    status: str = "COMPLETED"
    sale_date: Optional[datetime] = None

@dataclass
class Ticket:
    """Ticket vendido"""
    id: Optional[int] = None
    sale_id: int = 0
    showtime_id: int = 0
    seat_id: int = 0
    price_sold: Decimal = Decimal('0.00')
    ticket_type: str = "" # General, VIP, etc.
    status: str = "VALID"
