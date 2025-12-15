import logging
import csv
from typing import List, Dict, Any, Optional
from src.database.connection import DatabaseConnection, DatabaseError

logger = logging.getLogger(__name__)

class InventoryService:
    """
    Servicio para gestionar toda la lógica de negocio relacionada con el inventario,
    incluyendo insumos, productos y recetas.
    """
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def get_inventory_items(self) -> List[Dict[str, Any]]:
        """
        Obtiene una lista de todos los insumos (inventory_items) del inventario.
        """
        try:
            query = "SELECT id, name, unit, current_stock, reorder_point, cost_per_unit FROM inventory_items ORDER BY name;"
            items = self.db.execute_query(query)
            return items if items else []
        except DatabaseError as e:
            logger.exception(f"Error de base de datos al obtener los insumos: {e}")
            return []

    def create_inventory_item(self, data: Dict[str, Any]) -> Optional[int]:
        """Crea un nuevo insumo en la base de datos."""
        try:
            query = "INSERT INTO inventory_items (name, unit, current_stock, reorder_point, cost_per_unit) VALUES (?, ?, ?, ?, ?)"
            params = (data['name'], data['unit'], data.get('current_stock', 0), data['reorder_point'], data['cost_per_unit'])
            new_id = self.db.execute_insert(query, params)
            if new_id and data.get('current_stock', 0) != 0:
                self.add_stock_movement(item_id=new_id, quantity=data['current_stock'], movement_type="INITIAL", notes="Stock inicial")
            return new_id
        except DatabaseError as e:
            logger.exception(f"Error de BD al crear el insumo '{data.get('name')}': {e}")
            return None
    
    def update_inventory_item(self, item_id: int, data: Dict[str, Any]) -> bool:
        """Actualiza un insumo existente."""
        try:
            query = "UPDATE inventory_items SET name = ?, unit = ?, reorder_point = ?, cost_per_unit = ? WHERE id = ?"
            params = (data['name'], data['unit'], data['reorder_point'], data['cost_per_unit'], item_id)
            return self.db.execute_command(query, params) > 0
        except DatabaseError as e:
            logger.exception(f"Error de BD al actualizar el insumo ID {item_id}: {e}")
            return False

    def add_stock_movement(self, item_id: int, quantity: float, movement_type: str, user_id: Optional[int] = None, reference_id: Optional[int] = None, notes: Optional[str] = None) -> bool:
        """Registra un movimiento de stock y actualiza el conteo en 'inventory_items'."""
        try:
            with self.db.transaction() as cursor:
                update_query = "UPDATE inventory_items SET current_stock = current_stock + %s WHERE id = %s"
                cursor.execute(update_query, (quantity, item_id))
                movement_query = "INSERT INTO stock_movements (inventory_item_id, quantity, movement_type, user_id, reference_id, notes) VALUES (%s, %s, %s, %s, %s, %s)"
                mov_params = (item_id, quantity, movement_type, user_id, reference_id, notes)
                cursor.execute(movement_query, mov_params)
            return True
        except DatabaseError as e:
            logger.exception(f"Error de BD al añadir movimiento de stock para el insumo ID {item_id}: {e}")
            return False

    def delete_inventory_item(self, item_id: int) -> bool:
        """Elimina un insumo si no está en uso en una receta."""
        try:
            in_use_count = self.db.execute_scalar("SELECT COUNT(*) FROM product_recipes WHERE inventory_item_id = ?", (item_id,))
            if in_use_count > 0:
                logger.warning(f"Intento de eliminar el insumo ID {item_id}, pero está en uso en {in_use_count} recetas.")
                return False
            return self.db.execute_command("DELETE FROM inventory_items WHERE id = ?", (item_id,)) > 0
        except DatabaseError as e:
            logger.exception(f"Error de BD al eliminar el insumo ID {item_id}: {e}")
            return False

    # --- Métodos de Productos y Recetas ---
    def get_products_with_category(self) -> List[Dict[str, Any]]:
        try:
            query = "SELECT p.id, p.name, p.description, p.price, p.product_type, p.track_stock, p.is_active, pc.name AS category_name FROM products p JOIN product_categories pc ON p.category_id = pc.id ORDER BY p.name;"
            return self.db.execute_query(query) or []
        except DatabaseError as e:
            logger.exception(f"Error de BD al obtener los productos: {e}")
            return []

    def get_product_categories(self) -> List[Dict[str, Any]]:
        try:
            return self.db.execute_query("SELECT id, name FROM product_categories WHERE is_active = 1 ORDER BY name") or []
        except DatabaseError as e:
            logger.exception("Error de BD al obtener las categorías de productos.")
            return []

    def create_product(self, data: Dict[str, Any]) -> Optional[int]:
        try:
            query = "INSERT INTO products (name, description, price, category_id, product_type, track_stock, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)"
            params = (data['name'], data.get('description'), data['price'], data['category_id'], data.get('product_type', 'SIMPLE'), data.get('track_stock', True), data.get('is_active', True))
            return self.db.execute_insert(query, params)
        except DatabaseError as e:
            logger.exception(f"Error de BD al crear el producto '{data.get('name')}'.")
            return None

    def update_product(self, product_id: int, data: Dict[str, Any]) -> bool:
        try:
            query = "UPDATE products SET name = ?, description = ?, price = ?, category_id = ?, product_type = ?, track_stock = ?, is_active = ? WHERE id = ?"
            params = (data['name'], data.get('description'), data['price'], data['category_id'], data.get('product_type', 'SIMPLE'), data.get('track_stock', True), data.get('is_active', True), product_id)
            return self.db.execute_command(query, params) > 0
        except DatabaseError as e:
            logger.exception(f"Error de BD al actualizar el producto ID {product_id}.")
            return False
            
    def delete_product(self, product_id: int) -> bool:
        try:
            in_use_count = self.db.execute_scalar("SELECT COUNT(*) FROM product_recipes WHERE child_product_id = ?", (product_id,))
            if in_use_count > 0:
                logger.warning(f"Intento de eliminar producto ID {product_id}, pero es parte de {in_use_count} combos.")
                return False
            return self.db.execute_command("DELETE FROM products WHERE id = ?", (product_id,)) > 0
        except DatabaseError as e:
            logger.exception(f"Error de BD al eliminar el producto ID {product_id}.")
            return False

    def get_recipe_for_product(self, product_id: int) -> List[Dict[str, Any]]:
        try:
            query = "SELECT pr.quantity, pr.inventory_item_id, ii.name AS item_name, ii.unit, pr.child_product_id, p.name AS product_name FROM product_recipes pr LEFT JOIN inventory_items ii ON pr.inventory_item_id = ii.id LEFT JOIN products p ON pr.child_product_id = p.id WHERE pr.parent_product_id = ?"
            return self.db.execute_query(query, (product_id,))
        except DatabaseError as e:
            logger.exception(f"Error de BD al obtener la receta para el producto ID {product_id}.")
            return []

    def update_recipe_for_product(self, product_id: int, recipe_items: List[Dict[str, Any]]) -> bool:
        try:
            with self.db.transaction() as cursor:
                cursor.execute("DELETE FROM product_recipes WHERE parent_product_id = %s", (product_id,))
                if not recipe_items: return True
                insert_query = "INSERT INTO product_recipes (parent_product_id, inventory_item_id, child_product_id, quantity) VALUES (%s, %s, %s, %s)"
                for item in recipe_items:
                    if not item.get('quantity'): continue
                    params = (product_id, item.get('inventory_item_id'), item.get('child_product_id'), item.get('quantity'))
                    cursor.execute(insert_query, params)
            return True
        except DatabaseError: return False

    def search_ingredients(self, term: str) -> List[Dict[str, Any]]:
        if not term: return []
        try:
            query = "(SELECT id, name, unit, 'INVENTORY' as type FROM inventory_items WHERE name LIKE ?) UNION ALL (SELECT id, name, 'un' as unit, 'PRODUCT' as type FROM products WHERE name LIKE ? AND product_type != 'COMBO' AND track_stock = 1) ORDER BY name LIMIT 20"
            like_term = f"%{term}%"
            return self.db.execute_query(query, (like_term, like_term))
        except DatabaseError as e:
            logger.exception(f"Error de BD al buscar ingredientes con el término '{term}'.")
            return []

    # --- Métodos de Lógica de Stock y Auditoría ---
    def deduct_stock_for_sale(self, sale_id: int, items_sold: List[Dict[str, Any]], user_id: int):
        """
        Deduce el stock para una venta, procesando las recetas de cada producto vendido.
        Esta es la implementación de la lógica recursiva de inventario.
        """
        try:
            with self.db.transaction():
                for sale_item in items_sold:
                    product_id = sale_item['product_id']
                    quantity_sold = sale_item['quantity']
                    self._process_product_deduction(product_id, quantity_sold, sale_id, user_id)
            return True
        except DatabaseError as e:
            logger.exception(f"Fallo al deducir el stock para la venta ID {sale_id}.")
            # La transacción hará rollback automáticamente.
            return False

    def _process_product_deduction(self, product_id: int, quantity_sold: float, sale_id: int, user_id: int):
        """
        Método recursivo auxiliar para procesar el descuento de stock de un producto.
        """
        # 1. Obtener la receta del producto
        recipe = self.get_recipe_for_product(product_id)

        # 2. Si no hay receta, no hay nada que descontar
        if not recipe:
            product_info = self.db.execute_query("SELECT name, track_stock FROM products WHERE id = ?", (product_id,))
            if product_info and product_info[0]['track_stock']:
                logger.warning(f"El producto '{product_info[0]['name']}' (ID: {product_id}) está configurado para rastrear stock, pero no tiene receta. No se descontará nada.")
            return

        # 3. Procesar cada item de la receta
        for component in recipe:
            quantity_to_deduct = component['quantity'] * quantity_sold

            # Si el componente es un INSUMO (inventory_item)
            if component['inventory_item_id']:
                self.add_stock_movement(
                    item_id=component['inventory_item_id'],
                    quantity=-quantity_to_deduct, # Negativo porque es una salida
                    movement_type='SALE',
                    user_id=user_id,
                    reference_id=sale_id,
                    notes=f"Venta #{sale_id}"
                )
            
            # Si el componente es otro PRODUCTO (sub-producto de un combo)
            elif component['child_product_id']:
                # Llamada recursiva para procesar el sub-producto
                self._process_product_deduction(component['child_product_id'], quantity_to_deduct, sale_id, user_id)

    def get_stock_movements(self, start_date: Optional[str] = None, end_date: Optional[str] = None, item_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Obtiene un log de los movimientos de stock, con filtros opcionales."""
        try:
            query = "SELECT sm.id, sm.created_at, ii.name AS item_name, sm.quantity, sm.movement_type, u.username AS user_name, sm.notes FROM stock_movements sm JOIN inventory_items ii ON sm.inventory_item_id = ii.id LEFT JOIN users u ON sm.user_id = u.id"
            filters = []
            params = []
            if start_date:
                filters.append("sm.created_at >= ?")
                params.append(start_date)
            if end_date:
                filters.append("sm.created_at <= ?")
                params.append(end_date)
            if item_id:
                filters.append("sm.inventory_item_id = ?")
                params.append(item_id)
            if filters:
                query += " WHERE " + " AND ".join(filters)
            query += " ORDER BY sm.created_at DESC"
            return self.db.execute_query(query, tuple(params))
        except DatabaseError as e:
            logger.exception("Error de BD al obtener los movimientos de stock.")
            return []

    # --- Métodos de Importación CSV ---
    def analyze_inventory_csv(self, csv_data: List[Dict]) -> Dict[str, Any]:
        """Analiza datos de un CSV, valida y prepara un resumen sin modificar la BD."""
        analysis = {'to_create': [], 'to_update': [], 'errors': []}
        existing_items = {item['name']: item for item in self.get_inventory_items()}
        for i, row in enumerate(csv_data, 1):
            name = row.get('nombre')
            if not name:
                analysis['errors'].append({'row': i, 'error': "La columna 'nombre' no puede estar vacía."})
                continue
            try:
                quantity = float(row.get('cantidad_a_añadir', 0))
                cost = float(row.get('costo_unitario', 0))
                reorder = float(row.get('punto_reorden', 0))
                unit = row.get('unidad_medida')
            except (ValueError, TypeError):
                analysis['errors'].append({'row': i, 'name': name, 'error': "Cantidad, costo o punto de reorden contienen valores no numéricos."})
                continue
            if name in existing_items:
                item = existing_items[name]
                analysis['to_update'].append({'id': item['id'], 'name': name, 'quantity': quantity, 'notes': f"Reabastecimiento por CSV. Costo actualizado a {cost:.2f}"})
            else:
                if not unit:
                    analysis['errors'].append({'row': i, 'name': name, 'error': "La 'unidad_medida' es requerida para insumos nuevos."})
                    continue
                analysis['to_create'].append({'name': name, 'unit': unit, 'current_stock': quantity, 'reorder_point': reorder, 'cost_per_unit': cost})
        return analysis

    def execute_inventory_import(self, validated_data: Dict[str, Any], user_id: int) -> bool:
        """Ejecuta la importación de inventario validada en una sola transacción."""
        try:
            for item_data in validated_data.get('to_create', []):
                self.create_inventory_item(item_data)
            for item_data in validated_data.get('to_update', []):
                self.add_stock_movement(item_id=item_data['id'], quantity=item_data['quantity'], movement_type='RESTOCK', user_id=user_id, notes=item_data.get('notes'))
            return True
        except DatabaseError as e:
            logger.exception("Falló la ejecución de la importación de inventario.")
            return False