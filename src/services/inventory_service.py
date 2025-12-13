import logging
from typing import List, Dict, Optional, Any
from decimal import Decimal
from src.database.connection import DatabaseConnection, DatabaseError
from src.models.models import InventoryItem, Product, ProductType, StockMovementType

logger = logging.getLogger(__name__)

class InventoryService:
    """
    Servicio para gestión de inventario avanzado.
    Maneja Productos, Insumos, Recetas, Combos y Movimientos de Stock (Kardex).
    """
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    # ==========================
    # INSUMOS (Inventory Items)
    # ==========================
    def get_inventory_items(self) -> List[InventoryItem]:
        try:
            query = "SELECT * FROM inventory_items ORDER BY name"
            results = self.db.execute_query(query)
            return [InventoryItem(**row) for row in results]
        except DatabaseError as e:
            logger.exception(f"Error al obtener insumos: {e}")
            return []

    def create_inventory_item(self, item: InventoryItem) -> Optional[int]:
        try:
            query = """
                INSERT INTO inventory_items (name, unit, current_stock, reorder_point, cost_per_unit)
                VALUES (%s, %s, %s, %s, %s)
            """
            params = (item.name, item.unit, item.current_stock, item.reorder_point, item.cost_per_unit)
            return self.db.execute_insert(query, params)
        except DatabaseError as e:
            logger.exception(f"Error al crear insumo: {e}")
            return None

    def register_stock_movement(self, item_id: int, quantity: Decimal, movement_type: str, 
                                user_id: int, reference_id: Optional[int] = None, notes: str = ""):
        """
        Registra un movimiento de stock y actualiza el stock actual del ítem.
        """
        try:
            with self.db.transaction() as cursor:
                # 1. Insertar movimiento en Kardex
                kardex_query = """
                    INSERT INTO stock_movements (inventory_item_id, quantity, movement_type, 
                                                 reference_id, user_id, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(kardex_query, (item_id, quantity, movement_type, reference_id, user_id, notes))
                
                # 2. Actualizar stock actual
                update_query = """
                    UPDATE inventory_items 
                    SET current_stock = current_stock + %s 
                    WHERE id = %s
                """
                cursor.execute(update_query, (quantity, item_id))
                
        except DatabaseError as e:
            logger.exception(f"Error al registrar movimiento de stock para item {item_id}: {e}")
            raise

    # ==========================
    # PRODUCTOS Y RECETAS
    # ==========================
    def get_products(self, category_id: Optional[int] = None) -> List[Product]:
        try:
            query = """
                SELECT p.*, c.name as category_name 
                FROM products p
                JOIN product_categories c ON p.category_id = c.id
                WHERE p.is_active = 1
            """
            params = []
            if category_id:
                query += " AND p.category_id = %s"
                params.append(category_id)
            
            query += " ORDER BY p.name"
            results = self.db.execute_query(query, tuple(params))
            return [Product(**row) for row in results]
        except DatabaseError as e:
            logger.exception(f"Error al obtener productos: {e}")
            return []

    def process_sale_stock_deduction(self, sale_id: int, items: List[Dict[str, Any]], user_id: int):
        """
        Procesa la deducción de stock para una venta completa.
        Maneja recursividad para Combos y Recetas.
        items: lista de dicts con {'product_id': int, 'quantity': int}
        """
        try:
            for item in items:
                self._deduct_product_stock(item['product_id'], item['quantity'], sale_id, user_id)
        except Exception as e:
            logger.exception(f"Error crítico al procesar stock de venta {sale_id}: {e}")
            # Aquí se debería considerar si hacer rollback de la venta o marcarla con error de stock
            raise

    def _deduct_product_stock(self, product_id: int, quantity: int, sale_id: int, user_id: int):
        """
        Lógica recursiva para descontar stock.
        Si es SIMPLE -> Busca receta y descuenta insumos.
        Si es COMBO -> Busca receta (hijos) y llama recursivamente a _deduct_product_stock.
        """
        # Obtener tipo de producto y si trackea stock
        product = self.get_product_by_id(product_id)
        if not product or not product.track_stock:
            return

        # Obtener receta
        recipes = self.get_product_recipe(product_id)
        
        for component in recipes:
            qty_needed = component['quantity'] * quantity
            
            if component['inventory_item_id']:
                # Es un insumo directo (ej: Vaso, Maiz)
                self.register_stock_movement(
                    item_id=component['inventory_item_id'],
                    quantity=-qty_needed, # Salida es negativa
                    movement_type=StockMovementType.SALE.value,
                    user_id=user_id,
                    reference_id=sale_id,
                    notes=f"Venta de producto {product.name}"
                )
            elif component['child_product_id']:
                # Es un sub-producto (ej: Combo tiene Refresco)
                # Recursión
                self._deduct_product_stock(component['child_product_id'], int(qty_needed), sale_id, user_id)

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        # Helper simple
        res = self.db.execute_query("SELECT * FROM products WHERE id = %s", (product_id,))
        return Product(**res[0]) if res else None

    def get_product_recipe(self, product_id: int) -> List[Dict]:
        """Retorna los componentes de la receta de un producto."""
        query = "SELECT * FROM product_recipes WHERE parent_product_id = %s"
        return self.db.execute_query(query, (product_id,))
