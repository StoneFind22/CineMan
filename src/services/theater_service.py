import logging
from typing import List, Dict, Optional
from src.database.connection import DatabaseConnection, DatabaseError
from src.models.models import Theater, Seat, SeatType

logger = logging.getLogger(__name__)

class TheaterService:
    """
    Servicio para gestionar Salas y Asientos.
    """
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def get_all_theaters(self) -> List[Theater]:
        try:
            results = self.db.execute_query("SELECT * FROM theaters WHERE is_active = 1")
            return [Theater(**row) for row in results]
        except DatabaseError:
            return []

    def create_theater(self, theater: Theater, rows: int, cols: int) -> Optional[int]:
        """
        Crea una sala y genera automáticamente sus asientos en una cuadrícula.
        """
        try:
            with self.db.transaction() as cursor:
                # 1. Crear Sala
                cursor.execute(
                    "INSERT INTO theaters (name, total_capacity) VALUES (%s, %s)",
                    (theater.name, rows * cols)
                )
                theater_id = cursor.lastrowid
                
                # 2. Generar Asientos
                # Obtenemos ID de tipo General por defecto
                cursor.execute("SELECT id FROM seat_types WHERE name = 'General'")
                res = cursor.fetchone()
                general_type_id = res[0] if res else 1
                
                seats_data = []
                row_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                
                for r in range(rows):
                    row_label = row_labels[r] if r < len(row_labels) else f"R{r+1}"
                    for c in range(cols):
                        # (theater_id, row_label, number, seat_type_id, x, y)
                        seats_data.append(
                            (theater_id, row_label, c + 1, general_type_id, c, r)
                        )
                
                cursor.executemany(
                    """INSERT INTO seats (theater_id, row_label, number, seat_type_id, x_position, y_position)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    seats_data
                )
                
                return theater_id
        except DatabaseError as e:
            logger.exception(f"Error al crear sala: {e}")
            return None

    def get_theater_seats(self, theater_id: int) -> List[Seat]:
        try:
            query = """
                SELECT s.*, st.name as seat_type_name, st.price_modifier
                FROM seats s
                JOIN seat_types st ON s.seat_type_id = st.id
                WHERE s.theater_id = %s
                ORDER BY s.y_position, s.x_position
            """
            results = self.db.execute_query(query, (theater_id,))
            return [Seat(**row) for row in results]
        except DatabaseError:
            return []

    def update_seat_layout(self, seats: List[Seat]):
        """
        Actualiza el layout de asientos (tipos, estados, posiciones).
        Útil para el editor visual.
        """
        try:
            with self.db.transaction() as cursor:
                query = """
                    UPDATE seats 
                    SET seat_type_id = %s, status = %s, x_position = %s, y_position = %s,
                        row_label = %s, number = %s
                    WHERE id = %s
                """
                data = [
                    (s.seat_type_id, s.status, s.x_position, s.y_position, s.row_label, s.number, s.id)
                    for s in seats
                ]
                cursor.executemany(query, data)
        except DatabaseError as e:
            logger.exception(f"Error al actualizar layout: {e}")
