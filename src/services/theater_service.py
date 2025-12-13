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
            results = self.db.execute_query("SELECT * FROM theaters WHERE is_active = 1 ORDER BY name")
            return [Theater(**row) for row in results]
        except DatabaseError:
            return []

    def get_all_seat_types(self) -> List[SeatType]:
        """Recupera todos los tipos de asientos de la base de datos."""
        try:
            results = self.db.execute_query("SELECT * FROM seat_types ORDER BY id")
            return [SeatType(**row) for row in results]
        except DatabaseError:
            return []

    def create_theater(self, theater: Theater, rows: int, cols: int) -> Optional[int]:
        """
        Crea una sala y genera automáticamente sus asientos en una cuadrícula.
        """
        try:
            # Se usa una transacción para asegurar la atomicidad de la operación.
            with self.db.transaction() as cursor:
                # 1. Crear la entidad de la sala.
                cursor.execute(
                    "INSERT INTO theaters (name, total_capacity) VALUES (%s, %s)",
                    (theater.name, rows * cols)
                )
                theater_id = cursor.lastrowid
                
                # 2. Generar los asientos por defecto para la nueva sala.
                cursor.execute("SELECT id FROM seat_types WHERE name = 'General'")
                res = cursor.fetchone()
                general_type_id = res['id'] if res else 1 # Fallback a 1 si no se encuentra.
                
                seats_data = []
                row_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                
                for r in range(rows):
                    row_label = row_labels[r] if r < len(row_labels) else f"R{r+1}"
                    for c in range(cols):
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

    def update_theater(self, theater: Theater) -> bool:
        """Actualiza la información de una sala (ej. el nombre)."""
        try:
            rows_affected = self.db.execute_command(
                "UPDATE theaters SET name = %s WHERE id = %s",
                (theater.name, theater.id)
            )
            return rows_affected > 0
        except DatabaseError as e:
            logger.exception(f"Error al actualizar sala: {e}")
            return False

    def delete_theater(self, theater_id: int) -> bool:
        """Desactiva una sala (borrado lógico) para que no aparezca en la UI."""
        try:
            rows_affected = self.db.execute_command(
                "UPDATE theaters SET is_active = 0 WHERE id = %s",
                (theater_id,)
            )
            return rows_affected > 0
        except DatabaseError as e:
            logger.exception(f"Error al desactivar sala: {e}")
            return False

    def get_theater_seats(self, theater_id: int) -> List[Seat]:
        """Obtiene todos los asientos de una sala específica con su tipo."""
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

    def update_seat_layout(self, theater_id: int, new_layout: List[Seat]):
        """
        Sincroniza el layout de asientos, manejando creaciones, actualizaciones y borrados.
        """
        try:
            with self.db.transaction() as cursor:
                # 1. Obtiene el estado actual de los asientos desde la BD.
                cursor.execute("SELECT * FROM seats WHERE theater_id = %s", (theater_id,))
                db_seats_raw = cursor.fetchall()
                db_seats_map = {s['id']: Seat(**s) for s in db_seats_raw}

                # 2. Separa los asientos del editor en nuevos y existentes.
                editor_seats_map = {s.id: s for s in new_layout if s.id is not None}
                new_seats_to_create = [s for s in new_layout if s.id is None]

                # 3. Identifica y elimina los asientos que ya no existen en el nuevo layout.
                db_ids = set(db_seats_map.keys())
                editor_ids = set(editor_seats_map.keys())
                ids_to_delete = db_ids - editor_ids
                
                if ids_to_delete:
                    placeholders = ', '.join(['%s'] * len(ids_to_delete))
                    delete_query = f"DELETE FROM seats WHERE id IN ({placeholders})"
                    cursor.execute(delete_query, list(ids_to_delete))

                # 4. Identifica y actualiza los asientos que han cambiado.
                seats_to_update = []
                for seat_id, editor_seat in editor_seats_map.items():
                    db_seat = db_seats_map.get(seat_id)
                    if db_seat and (
                        db_seat.seat_type_id != editor_seat.seat_type_id
                        or db_seat.status != editor_seat.status
                    ):
                        seats_to_update.append(editor_seat)

                if seats_to_update:
                    update_query = "UPDATE seats SET seat_type_id = %s, status = %s WHERE id = %s"
                    update_data = [(s.seat_type_id, s.status, s.id) for s in seats_to_update]
                    cursor.executemany(update_query, update_data)
                
                # 5. Inserta los nuevos asientos creados en el editor.
                if new_seats_to_create:
                    insert_query = """
                        INSERT INTO seats (theater_id, row_label, number, seat_type_id, status, x_position, y_position)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    insert_data = [
                        (theater_id, s.row_label, s.number, s.seat_type_id, s.status, s.x_position, s.y_position)
                        for s in new_seats_to_create
                    ]
                    cursor.executemany(insert_query, insert_data)

                # 6. Actualiza la capacidad total de la sala.
                total_capacity = len(editor_ids) + len(new_seats_to_create)
                cursor.execute(
                    "UPDATE theaters SET total_capacity = %s WHERE id = %s",
                    (total_capacity, theater_id)
                )

        except DatabaseError as e:
            logger.exception(f"Error al sincronizar layout: {e}")
            raise
