from dataclasses import dataclass, field
from typing import List, Optional

# Definición de las estructuras de datos para los ítems de la venta.

@dataclass
class Seat:
    """Representa un asiento específico en una sala."""
    row: str
    number: int
    seat_id: int # ID del asiento en la BD

@dataclass
class Ticket:
    """Representa una entrada de cine en el pedido."""
    movie_title: str
    showtime: str
    showtime_id: int
    seat: Seat
    ticket_type: str # Adulto, Niño, etc.
    price: float

@dataclass
class ConcessionItem:
    """Representa un ítem de confitería en el pedido."""
    name: str
    size: Optional[str]
    quantity: int
    price_per_unit: float

    @property
    def total_price(self) -> float:
        return self.quantity * self.price_per_unit

class Transaction:
    """
    Gestiona el estado de una transacción de venta en curso.
    Mantiene la lista de productos, calcula totales y maneja descuentos.
    Es el "cerebro" del flujo de venta.
    """
    def __init__(self):
        self.tickets: List[Ticket] = []
        self.concessions: List[ConcessionItem] = []
        # self.discounts = [] # Placeholder for future implementation
        self.tax_rate = 0.18 # IGV del 18%

    def add_ticket(self, ticket: Ticket):
        """Añade una entrada al pedido."""
        self.tickets.append(ticket)

    def remove_ticket_by_seat(self, seat_id: int):
        """Remueve una entrada del pedido basado en el ID del asiento."""
        self.tickets = [t for t in self.tickets if t.seat.seat_id != seat_id]

    def update_concession_quantity(self, product: dict, new_quantity: int):
        """
        Añade, actualiza o elimina un ítem de confitería basado en su cantidad.
        Si la cantidad es 0, el ítem se elimina.
        """
        # Buscar si el ítem ya existe en la transacción
        existing_item = next((item for item in self.concessions if item.name == product["name"]), None)

        if new_quantity > 0:
            if existing_item:
                # Si existe, solo actualiza la cantidad
                existing_item.quantity = new_quantity
            else:
                # Si no existe, crea uno nuevo y lo añade
                new_item = ConcessionItem(
                    name=product["name"],
                    size=product.get("size"), # Asume que el producto puede tener un tamaño
                    quantity=new_quantity,
                    price_per_unit=product["price"]
                )
                self.concessions.append(new_item)
        elif new_quantity == 0 and existing_item:
            # Si la cantidad es 0 y el ítem existe, lo elimina
            self.concessions.remove(existing_item)

    def calculate_subtotal(self) -> float:
        """Calcula el subtotal de todos los ítems antes de impuestos."""
        ticket_total = sum(t.price for t in self.tickets)
        concession_total = sum(c.total_price for c in self.concessions)
        return ticket_total + concession_total

    def calculate_total(self) -> (float, float, float):
        """
        Calcula el total de la venta.
        Retorna (subtotal, impuestos, total_final).
        """
        subtotal = self.calculate_subtotal()
        # Asumiendo que los precios de los productos ya incluyen IGV, lo calculamos a la inversa.
        # Subtotal = Base Imponible + Impuestos
        # Subtotal = Base Imponible + (Base Imponible * Tasa)
        # Subtotal = Base Imponible * (1 + Tasa)
        # Base Imponible = Subtotal / (1 + Tasa)
        base_amount = subtotal / (1 + self.tax_rate)
        taxes = subtotal - base_amount
        return base_amount, taxes, subtotal

    def is_empty(self) -> bool:
        """Verifica si la transacción no tiene ítems."""
        return not self.tickets and not self.concessions

    def clear(self):
        """Limpia la transacción para una nueva venta."""
        self.tickets.clear()
        self.concessions.clear()
