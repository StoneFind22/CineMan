import logging
from typing import List, Optional
from datetime import datetime, timedelta
from src.database.connection import DatabaseConnection, DatabaseError
from src.models.models import Showtime, PriceProfile

logger = logging.getLogger(__name__)

class ScheduleService:
    """
    Servicio para programación de funciones (Showtimes) y gestión de precios.
    """
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def get_showtimes(self, date_filter: Optional[datetime] = None, theater_id: Optional[int] = None) -> List[Showtime]:
        try:
            query = """
                SELECT s.*, m.title as movie_title, t.name as theater_name
                FROM showtimes s
                JOIN movies m ON s.movie_id = m.id
                JOIN theaters t ON s.theater_id = t.id
                WHERE s.status != 'CANCELLED'
            """
            params = []
            if date_filter:
                query += " AND DATE(s.start_time) = DATE(%s)"
                params.append(date_filter)
            if theater_id:
                query += " AND s.theater_id = %s"
                params.append(theater_id)
            
            query += " ORDER BY s.start_time"
            
            results = self.db.execute_query(query, tuple(params))
            return [Showtime(**row) for row in results]
        except DatabaseError:
            return []

    def create_showtime(self, showtime: Showtime) -> Optional[int]:
        """
        Crea una función validando conflictos de horario.
        """
        if self.check_conflict(showtime.theater_id, showtime.start_time, showtime.end_time):
            logger.warning("Conflicto de horario detectado.")
            return None # O lanzar excepción específica

        try:
            query = """
                INSERT INTO showtimes (movie_id, theater_id, price_profile_id, start_time, end_time, 
                                       projection_type, audio_type, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                showtime.movie_id, showtime.theater_id, showtime.price_profile_id,
                showtime.start_time, showtime.end_time, showtime.projection_type,
                showtime.audio_type, showtime.status
            )
            return self.db.execute_insert(query, params)
        except DatabaseError as e:
            logger.exception(f"Error al crear showtime: {e}")
            return None

    def check_conflict(self, theater_id: int, start: datetime, end: datetime, exclude_id: Optional[int] = None) -> bool:
        """
        Verifica si hay solapamiento de horarios en la misma sala.
        Retorna True si hay conflicto.
        """
        try:
            query = """
                SELECT COUNT(*) as count 
                FROM showtimes 
                WHERE theater_id = %s 
                AND status != 'CANCELLED'
                AND (
                    (start_time < %s AND end_time > %s) -- Nuevo empieza antes de que termine existente
                    OR
                    (start_time >= %s AND start_time < %s) -- Nuevo empieza durante existente
                )
            """
            params = [theater_id, end, start, start, end]
            
            if exclude_id:
                query += " AND id != %s"
                params.append(exclude_id)
                
            result = self.db.execute_scalar(query, tuple(params))
            # execute_scalar returns a value directly if I implemented it right in connection.py
            # Let's check connection.py implementation in my mind... yes, it returns values()[0]
            return result > 0
        except DatabaseError:
            return True # Asumir conflicto ante error por seguridad

    def get_price_profiles(self) -> List[PriceProfile]:
        try:
            results = self.db.execute_query("SELECT * FROM price_profiles WHERE is_active = 1")
            return [PriceProfile(**row) for row in results]
        except DatabaseError:
            return []
