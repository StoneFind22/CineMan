import flet as ft
from src.services.inventory_service import InventoryService
from src.ui.theme import AppTheme
from src.ui.components.dialogs import show_confirm_dialog, show_info_dialog
from src.ui.views.admin.inventory_item_dialog import InventoryItemDialog
from src.ui.views.admin.product_dialog import ProductDialog
from src.ui.views.admin.inventory_import_dialog import InventoryImportDialog

class InventoryView:
    """
    Vista para gestionar el inventario.
    Reconstruida siguiendo el patrón de 'DashboardView' para solucionar el bug de renderizado.
    """
    def __init__(self, page: ft.Page, inventory_service: InventoryService, theme: AppTheme):
        self.page = page
        self.inventory_service = inventory_service
        self.theme = theme
        self.items = []
        self.products = []
        self.movements = []

        # Definir los controles aquí, pero construirlos en el método build
        self.insumos_table = ft.DataTable(columns=[])
        self.products_table = ft.DataTable(columns=[])
        self.movements_table = ft.DataTable(columns=[])

    def build(self):
        """
        Construye y retorna el control raíz de la vista de inventario.
        Este método es llamado por MainScreen.
        """
        self._setup_tables()
        
        # Cargar todos los datos al construir la vista
        self.load_data()
        self.load_products_data()
        self.load_movements_data()

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Gestión de Inventario", style=ft.TextThemeStyle.HEADLINE_LARGE),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Tabs(
                    selected_index=0,
                    animation_duration=300,
                    tabs=[
                        ft.Tab(text="Insumos", content=self._build_insumos_tab()),
                        ft.Tab(text="Productos y Recetas", content=self._build_products_tab()),
                        ft.Tab(text="Movimientos de Stock", content=self._build_movements_tab()),
                    ],
                    expand=1,
                ),
            ],
            expand=True
        )

    def _setup_tables(self):
        """Define las columnas para todas las tablas."""
        self.insumos_table.columns = [
            ft.DataColumn(ft.Text("Nombre")), ft.DataColumn(ft.Text("Stock Actual"), numeric=True),
            ft.DataColumn(ft.Text("Unidad")), ft.DataColumn(ft.Text("Punto de Reorden"), numeric=True),
            ft.DataColumn(ft.Text("Acciones")),
        ]
        self.products_table.columns = [
            ft.DataColumn(ft.Text("Nombre")), ft.DataColumn(ft.Text("Categoría")),
            ft.DataColumn(ft.Text("Precio"), numeric=True), ft.DataColumn(ft.Text("Tipo")),
            ft.DataColumn(ft.Text("Acciones")),
        ]
        self.movements_table.columns = [
            ft.DataColumn(ft.Text("Fecha")), ft.DataColumn(ft.Text("Insumo")),
            ft.DataColumn(ft.Text("Cantidad"), numeric=True), ft.DataColumn(ft.Text("Tipo")),
            ft.DataColumn(ft.Text("Usuario")), ft.DataColumn(ft.Text("Notas")),
        ]
    
    # --- Métodos para construir cada pestaña ---
    def _build_insumos_tab(self):
        return ft.Column([
            ft.Row([
                ft.ElevatedButton("Nuevo Insumo", icon=ft.Icons.ADD, on_click=self.open_create_dialog),
                ft.ElevatedButton("Importar desde CSV", icon=ft.Icons.UPLOAD_FILE, on_click=self.open_import_dialog),
            ]),
            ft.Container(content=ft.ListView([self.insumos_table], expand=True), expand=True),
        ], expand=True)

    def _build_products_tab(self):
        return ft.Column([
            ft.Row([ft.ElevatedButton("Nuevo Producto", icon=ft.Icons.ADD, on_click=self.open_create_product_dialog)]),
            ft.Container(content=ft.ListView([self.products_table], expand=True), expand=True),
        ], expand=True)

    def _build_movements_tab(self):
        return ft.Column([
            ft.Row([ft.ElevatedButton("Filtrar", icon=ft.Icons.FILTER_LIST, disabled=True)]),
            ft.Container(content=ft.ListView([self.movements_table], expand=True), expand=True),
        ], expand=True)

    # --- Métodos de carga de datos ---
    def load_data(self):
        self.items = self.inventory_service.get_inventory_items()
        self.insumos_table.rows.clear()
        if not self.items:
            self.insumos_table.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text("No se encontraron insumos.", text_align="center")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text(""))]))
        else:
            for item in self.items:
                item_copy = item.copy()
                stock_color = ft.Colors.RED_500 if item['current_stock'] <= item['reorder_point'] else ft.Colors.GREEN_500
                self.insumos_table.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(item['name'])),
                    ft.DataCell(ft.Row([ft.Icon(ft.Icons.CIRCLE, color=stock_color, size=12), ft.Text(f"{item['current_stock']:.2f}")])),
                    ft.DataCell(ft.Text(item['unit'])),
                    ft.DataCell(ft.Text(f"{item['reorder_point']:.2f}")),
                    ft.DataCell(ft.Row([
                        ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar", on_click=lambda e, i=item_copy: self.open_edit_dialog(i)),
                        ft.IconButton(icon=ft.Icons.DELETE, tooltip="Eliminar", on_click=lambda e, i=item_copy: self.delete_item(i)),
                    ]))
                ]))
        if self.page: self.page.update()

    def load_products_data(self):
        self.products = self.inventory_service.get_products_with_category()
        self.products_table.rows.clear()
        if not self.products:
            self.products_table.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text("No se encontraron productos.", text_align="center")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text(""))]))
        else:
            for product in self.products:
                self.products_table.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(product['name'])), ft.DataCell(ft.Text(product.get('category_name', 'N/A'))),
                    ft.DataCell(ft.Text(f"{product['price']:.2f}")), ft.DataCell(ft.Text(product['product_type'])),
                    ft.DataCell(ft.Row([
                        ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar Receta"), ft.IconButton(icon=ft.Icons.DELETE, tooltip="Eliminar Producto"),
                    ]))
                ]))
        if self.page: self.page.update()

    def load_movements_data(self):
        movements = self.inventory_service.get_stock_movements()
        self.movements_table.rows.clear()
        if not movements:
            self.movements_table.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text("No se encontraron movimientos.", text_align="center")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text(""))]))
        else:
            for movement in movements:
                quantity_str = f"+{movement['quantity']}" if movement['quantity'] > 0 else str(movement['quantity'])
                color = ft.Colors.GREEN_500 if movement['quantity'] > 0 else ft.Colors.RED_500
                self.movements_table.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(movement['created_at'].strftime("%Y-%m-%d %H:%M"))), ft.DataCell(ft.Text(movement['item_name'])),
                    ft.DataCell(ft.Text(quantity_str, color=color)), ft.DataCell(ft.Text(movement['movement_type'])),
                    ft.DataCell(ft.Text(movement.get('user_name', 'N/A'))), ft.DataCell(ft.Text(movement.get('notes', ''))),
                ]))
        if self.page: self.page.update()

    # --- Métodos de apertura de dialogos ---
    def open_create_dialog(self, e):
        dialog = InventoryItemDialog(page=self.page, inventory_service=self.inventory_service, theme=self.theme, on_save=self.load_data)
        dialog.show()

    def open_edit_dialog(self, item_data: dict):
        dialog = InventoryItemDialog(page=self.page, inventory_service=self.inventory_service, theme=self.theme, on_save=self.load_data, item_data=item_data)
        dialog.show()

    def delete_item(self, item_data: dict):
        def on_confirm(e):
            success = self.inventory_service.delete_inventory_item(item_data['id'])
            if success:
                show_info_dialog(self.page, "Éxito", "El insumo se ha eliminado correctamente.")
                self.load_data()
            else:
                show_info_dialog(self.page, "Error", "No se pudo eliminar el insumo. Es posible que esté en uso en alguna receta.")
        show_confirm_dialog(self.page, "Confirmar Eliminación", f"¿Está seguro que desea eliminar el insumo '{item_data['name']}'?", on_confirm)

    def open_create_product_dialog(self, e):
        dialog = ProductDialog(page=self.page, inventory_service=self.inventory_service, theme=self.theme, on_save=self.load_products_data)
        dialog.show()

    def open_import_dialog(self, e):
        dialog = InventoryImportDialog(inventory_service=self.inventory_service, theme=self.theme, on_complete=self.load_data)
        dialog.show(self.page)
