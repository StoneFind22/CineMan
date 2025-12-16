import logging
from typing import List, Dict, Any
from src.database.connection import DatabaseConnection, DatabaseError
from src.services.inventory_service import InventoryService
from src.utils.security import current_session

logger = logging.getLogger(__name__)

class SalesService:
    """
    Servicio para manejar la lógica de negocio relacionada con las ventas.
    """
    def __init__(self, db_connection: DatabaseConnection, inventory_service: InventoryService):
        self.db = db_connection
        self.inventory_service = inventory_service

    def get_active_movies_with_showtimes(self) -> List[Dict[str, Any]]:
        """
        Obtiene una lista de películas activas y sus funciones para el día de hoy.
        """
        try:
            query = """
                SELECT m.id AS movie_id, m.title, m.poster_url, m.duration_minutes,
                       s.id AS showtime_id, s.start_time, t.name AS theater_name,
                       s.projection_type, s.audio_type
                FROM movies m
                JOIN showtimes s ON m.id = s.movie_id
                JOIN theaters t ON s.theater_id = t.id
                WHERE m.status = 'ACTIVE' AND DATE(s.start_time) = CURDATE()
                ORDER BY m.title, s.start_time;
            """
            results = self.db.execute_query(query)
            
            movies = {}
            for row in results:
                movie_id = row['movie_id']
                if movie_id not in movies:
                    movies[movie_id] = {
                        "movie_id": movie_id, "title": row['title'], "poster_url": row['poster_url'],
                        "duration_minutes": row['duration_minutes'], "showtimes": []
                    }
                
                time_str = row['start_time'].strftime('%H:%M') if row['start_time'] else "00:00"
                
                movies[movie_id]["showtimes"].append({
                    "showtime_id": row['showtime_id'], "show_time": time_str,
                    "room_name": row['theater_name'], 
                    "format": f"{row['projection_type']} {row['audio_type']}"
                })
            return list(movies.values())
        except (DatabaseError, Exception) as e:
            logger.exception(f"Error al obtener películas y horarios: {e}")
            return []

    def get_seat_map(self, showtime_id: int) -> Dict[str, Any]:
        """
        Obtiene el mapa de asientos para una función específica.
        """
        try:
            query = """
                SELECT t.id as theater_id, t.name as theater_name, s.id as seat_id,
                       s.row_label as seat_row, s.number as seat_col,
                       CASE WHEN tic.id IS NOT NULL THEN 'occupied' ELSE 'available' END as status
                FROM showtimes st
                JOIN theaters t ON st.theater_id = t.id
                JOIN seats s ON t.id = s.theater_id
                LEFT JOIN tickets tic ON s.id = tic.seat_id AND tic.showtime_id = st.id
                WHERE st.id = ?
                ORDER BY s.y_position, s.x_position;
            """
            results = self.db.execute_query(query, (showtime_id,))
            if not results: return {"layout": {}, "seats": []}
            
            layout_info = {"room_id": results[0]['theater_id'], "room_name": results[0]['theater_name']}
            return {"layout": layout_info, "seats": results}
        except (DatabaseError, Exception) as e:
            logger.exception(f"Error al obtener mapa de asientos para showtime_id {showtime_id}: {e}")
            return {}

    def get_ticket_prices_for_showtime(self, showtime_id: int) -> Dict[str, float]:
        """
        Obtiene los precios de los boletos para una función específica.
        """
        try:
            query = """
                SELECT pp.base_price_general, pp.base_price_child, pp.base_price_senior
                FROM showtimes s
                JOIN price_profiles pp ON s.price_profile_id = pp.id
                WHERE s.id = ?;
            """
            result = self.db.execute_query(query, (showtime_id,), fetch_one=True)
            
            if not result:
                logger.warning(f"No se encontró perfil de precios para showtime_id {showtime_id}. Usando precios de respaldo.")
                return {"Adulto": 15.00, "Niño": 10.00, "3ra Edad": 8.00}

            return {
                "Adulto": float(result['base_price_general']),
                "Niño": float(result['base_price_child']),
                "3ra Edad": float(result['base_price_senior'])
            }
        except (DatabaseError, Exception) as e:
            logger.exception(f"Error al obtener precios para showtime_id {showtime_id}: {e}")
            # Fallback a precios por defecto en caso de error de BD
            return {"Adulto": 15.00, "Niño": 10.00, "3ra Edad": 8.00}

    def get_concession_products(self) -> List[Dict[str, Any]]:
        """
        Obtiene una lista de todos los productos de confitería activos (no combos).
        """
        try:
            query = """
                SELECT p.id, p.name, p.price, p.image_url
                FROM products p
                JOIN product_categories pc ON p.category_id = pc.id
                WHERE p.is_active = 1 
                  AND p.product_type = 'SIMPLE'
                  AND pc.name IN ('Bebidas', 'Popcorn', 'Dulces', 'Golosinas', 'Snacks')
                ORDER BY p.name;
            """
            return self.db.execute_query(query) or []
        except (DatabaseError, Exception) as e:
            logger.exception(f"Error al obtener productos de confitería: {e}")
            return []

    def save_transaction(self, transaction, user_id: int) -> bool:
        """
        Guarda una transacción completa y luego deduce el stock correspondiente.
        """

        sale_id = None
        sale_items_for_stock_deduction = []

        try:
            with self.db.transaction() as cursor:
                # 1. Crear la venta principal
                sale_query = "INSERT INTO sales (user_id, total_amount, payment_method, status) VALUES (%s, %s, %s, 'COMPLETED')"
                total = transaction.get('total', 0)
                payment_method = transaction.get('payment_method', 'CASH')
                cursor.execute(sale_query, (user_id, total, payment_method))
                sale_id = cursor.lastrowid
                if not sale_id: raise DatabaseError("No se pudo crear el registro de venta.")

                # 2. Guardar los tickets
                if transaction.get('tickets'):
                    ticket_query = "INSERT INTO tickets (sale_id, showtime_id, seat_id, price_sold, ticket_type) VALUES (%s, %s, %s, %s, %s)"
                    ticket_data = [(sale_id, t['showtime_id'], t['seat']['seat_id'], t['price'], t['type']) for t in transaction['tickets']]
                    cursor.executemany(ticket_query, ticket_data)

                # 3. Guardar los productos de confitería y preparar para deducción de stock
                if transaction.get('concessions'):
                    item_query = "INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, subtotal) VALUES (%s, %s, %s, %s, %s)"
                    for item in transaction['concessions']:
                        subtotal = item['price'] * item['quantity']
                        item_data = (sale_id, item['id'], item['quantity'], item['price'], subtotal)
                        cursor.execute(item_query, item_data)
                        sale_items_for_stock_deduction.append({'product_id': item['id'], 'quantity': item['quantity']})

            logger.info(f"Transacción {sale_id} guardada exitosamente en la BD.")

            # 4. Deducir stock (después de que la transacción principal fue exitosa)
            if sale_items_for_stock_deduction:
                logger.info(f"Iniciando deducción de stock para la venta {sale_id}.")
                self.inventory_service.deduct_stock_for_sale(sale_id, sale_items_for_stock_deduction, user_id)
            
            return True

        except (DatabaseError, Exception) as e:
            logger.exception(f"Error al guardar la transacción. Venta ID (si se creó): {sale_id}. Error: {e}")
            return False
