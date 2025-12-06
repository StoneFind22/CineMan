import logging
from typing import List, Dict, Any
from src.database.connection import DatabaseConnection, DatabaseError

logger = logging.getLogger(__name__)

class SalesService:
    """
    Servicio para manejar la lógica de negocio relacionada con las ventas,
    como obtener información de películas, horarios y productos.
    """
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def get_active_movies_with_showtimes(self) -> List[Dict[str, Any]]:
        """
        Obtiene una lista de películas activas y sus funciones para el día de hoy.
        Cada película incluye una lista de sus horarios, salas y formatos.
        """
        try:
            query = """
            SELECT
                m.id AS movie_id,
                m.title,
                m.poster_url,
                m.duration_minutes,
                s.id AS showtime_id,
                s.show_time,
                r.name AS room_name,
                s.format -- e.g., '2D', '3D', 'SUB', 'DOB'
            FROM
                movies m
            JOIN
                showtimes s ON m.id = s.movie_id
            JOIN
                rooms r ON s.room_id = r.id
            WHERE
                m.is_active = 1
                AND DATE(s.show_time) = CURDATE()
            ORDER BY
                m.title, s.show_time;
            """
            results = self.db.execute_query(query)
            
            # Agrupar resultados por película
            movies = {}
            for row in results:
                movie_id = row['movie_id']
                if movie_id not in movies:
                    movies[movie_id] = {
                        "movie_id": movie_id,
                        "title": row['title'],
                        "poster_url": row['poster_url'],
                        "duration_minutes": row['duration_minutes'],
                        "showtimes": []
                    }
                
                movies[movie_id]["showtimes"].append({
                    "showtime_id": row['showtime_id'],
                    "show_time": row['show_time'].strftime('%H:%M'), # Formatear solo la hora
                    "room_name": row['room_name'],
                    "format": row['format']
                })
            
            return list(movies.values())

        except DatabaseError as e:
            logger.exception(f"Error de base de datos al obtener películas y horarios: {e}")
            return []
        except Exception as e:
            logger.exception(f"Error inesperado al obtener películas y horarios: {e}")
            return []

    def get_seat_map(self, showtime_id: int) -> Dict[str, Any]:
        """
        Obtiene el mapa de asientos para una función específica, incluyendo el
        estado de cada asiento (disponible u ocupado).

        Retorna un diccionario con el layout de la sala y una lista de asientos.
        """
        try:
            query = """
            SELECT
                r.id as room_id,
                r.name as room_name,
                r.rows as room_rows,
                r.cols as room_cols,
                s.id as seat_id,
                s.row as seat_row,
                s.col as seat_col,
                CASE
                    WHEN t.id IS NOT NULL THEN 'occupied'
                    ELSE 'available'
                END as status
            FROM
                showtimes st
            JOIN
                rooms r ON st.room_id = r.id
            JOIN
                seats s ON r.id = s.room_id
            LEFT JOIN
                tickets t ON s.id = t.seat_id AND t.showtime_id = st.id
            WHERE
                st.id = ?
            ORDER BY
                s.row, s.col;
            """
            results = self.db.execute_query(query, (showtime_id,))

            if not results:
                return {"layout": {}, "seats": []}
            
            layout_info = {
                "room_id": results[0]['room_id'],
                "room_name": results[0]['room_name'],
                "rows": results[0]['room_rows'],
                "cols": results[0]['room_cols'],
            }
            
            return {
                "layout": layout_info,
                "seats": results
            }

        except DatabaseError as e:
            logger.exception(f"Error de BD al obtener mapa de asientos para showtime_id {showtime_id}: {e}")
            return {}
        except Exception as e:
            logger.exception(f"Error inesperado al obtener mapa de asientos: {e}")
            return {}

    def get_concession_products(self) -> List[Dict[str, Any]]:
        """
        Obtiene una lista de todos los productos de confitería activos.
        """
        try:
            query = """
            SELECT
                id,
                name,
                price,
                stock,
                image_url
            FROM
                products
            WHERE
                category = 'CONCESSION' AND is_active = 1
            ORDER BY
                name;
            """
            results = self.db.execute_query(query)
            return results if results else []

        except DatabaseError as e:
            logger.exception(f"Error de base de datos al obtener productos de confitería: {e}")
            return []
        except Exception as e:
            logger.exception(f"Error inesperado al obtener productos de confitería: {e}")
            return []

    def save_transaction(self, transaction, user_id: int) -> bool:
        """
        Guarda una transacción completa en la base de datos.
        Esto incluye la venta principal, los tickets y los ítems de venta.
        Utiliza una transacción de base de datos para garantizar la atomicidad.
        """
        _, _, total_amount = transaction.calculate_total()

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                sale_query = "INSERT INTO sales (user_id, total_amount, sale_date) VALUES (%s, %s, NOW())"
                cursor.execute(sale_query, (user_id, total_amount))
                sale_id = cursor.lastrowid
                
                if not sale_id:
                    raise DatabaseError("Failed to insert sale record.")

                if transaction.tickets:
                    ticket_query = "INSERT INTO tickets (sale_id, showtime_id, seat_id, ticket_type, price) VALUES (%s, %s, %s, %s, %s)"
                    ticket_data = [
                        (sale_id, t.showtime_id, t.seat.seat_id, t.ticket_type, t.price)
                        for t in transaction.tickets
                    ]
                    cursor.executemany(ticket_query, ticket_data)

                if transaction.concessions:
                    item_query = "INSERT INTO sale_items (sale_id, product_id, quantity, price_at_sale) VALUES (%s, %s, %s, %s)"
                    update_stock_query = "UPDATE products SET stock = stock - %s WHERE id = %s"
                    
                    for item in transaction.concessions:
                        cursor.execute("SELECT id, stock FROM products WHERE name = %s", (item.name,))
                        product_record = cursor.fetchone()
                        if not product_record or product_record['stock'] < item.quantity:
                            raise DatabaseError(f"Stock insuficiente para {item.name}")
                        
                        product_id = product_record['id']
                        
                        cursor.execute(item_query, (sale_id, product_id, item.quantity, item.price_per_unit))
                        cursor.execute(update_stock_query, (item.quantity, product_id))
                
                conn.commit()
                logger.info(f"Transacción {sale_id} guardada exitosamente.")
                return True

        except DatabaseError as e:
            logger.exception(f"Error de base de datos al guardar la transacción: {e}")
            return False
        except Exception as e:
            logger.exception(f"Error inesperado al guardar la transacción: {e}")
            return False
