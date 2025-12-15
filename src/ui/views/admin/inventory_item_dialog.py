import flet as ft
from src.services.inventory_service import InventoryService
from src.ui.theme import AppTheme

class InventoryItemDialog(ft.AlertDialog):
    """
    Un diálogo para crear o editar un Insumo de Inventario (InventoryItem).
    """
    def __init__(self, page: ft.Page, inventory_service: InventoryService, theme: AppTheme, on_save: callable, item_data: dict = None):
        super().__init__()
        self.page = page
        self.inventory_service = inventory_service
        self.theme = theme
        self.on_save = on_save
        self.item_data = item_data
        
        self.is_edit = item_data is not None

        # Campos del formulario
        self.name_field = ft.TextField(label="Nombre del Insumo", autofocus=True)
        self.unit_field = ft.TextField(label="Unidad de Medida (ej: kg, un, lt)")
        self.stock_field = ft.TextField(label="Stock Inicial", keyboard_type=ft.KeyboardType.NUMBER)
        self.reorder_point_field = ft.TextField(label="Punto de Reorden", keyboard_type=ft.KeyboardType.NUMBER)
        self.cost_field = ft.TextField(label="Costo por Unidad", keyboard_type=ft.KeyboardType.NUMBER, value="0.00")

        if self.is_edit:
            self.name_field.value = self.item_data.get("name", "")
            self.unit_field.value = self.item_data.get("unit", "")
            self.stock_field.value = str(self.item_data.get("current_stock", "0"))
            self.stock_field.label = "Stock Actual" # No se puede editar, pero se muestra
            self.stock_field.read_only = True # No se permite editar el stock directamente aquí
            self.reorder_point_field.value = str(self.item_data.get("reorder_point", "0"))
            self.cost_field.value = str(self.item_data.get("cost_per_unit", "0.00"))


        self.modal = True
        self.title = ft.Text("Nuevo Insumo" if not self.is_edit else "Editar Insumo")
        self.content = ft.Column(
            controls=[
                self.name_field,
                self.unit_field,
                self.stock_field,
                self.reorder_point_field,
                self.cost_field,
            ],
            spacing=15,
            tight=True,
        )
        self.actions = [
            ft.TextButton("Cancelar", on_click=self.close_dialog),
            ft.ElevatedButton("Guardar", on_click=self.save_item),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def close_dialog(self, e):
        self.open = False
        self.page.update()

    def save_item(self, e):
        """
        Valida los datos del formulario y llama al servicio para guardar el insumo.
        """
        # Limpiar errores previos
        self.name_field.error_text = None
        self.unit_field.error_text = None
        self.stock_field.error_text = None
        self.reorder_point_field.error_text = None
        self.cost_field.error_text = None

        # Validación de datos
        if not self.name_field.value:
            self.name_field.error_text = "El nombre es requerido."
        if not self.unit_field.value:
            self.unit_field.error_text = "La unidad es requerida."
        
        try:
            float(self.reorder_point_field.value)
        except (ValueError, TypeError):
            self.reorder_point_field.error_text = "Debe ser un número."
        
        try:
            float(self.cost_field.value)
        except (ValueError, TypeError):
            self.cost_field.error_text = "Debe ser un número."

        if not self.is_edit:
            try:
                float(self.stock_field.value)
            except (ValueError, TypeError):
                self.stock_field.error_text = "Debe ser un número."

        self.update()
        if (self.name_field.error_text or self.unit_field.error_text or 
            self.reorder_point_field.error_text or self.cost_field.error_text or self.stock_field.error_text):
            return

        try:
            data = {
                "name": self.name_field.value,
                "unit": self.unit_field.value,
                "reorder_point": float(self.reorder_point_field.value),
                "cost_per_unit": float(self.cost_field.value),
            }
            
            success = False
            if self.is_edit:
                item_id = self.item_data['id']
                success = self.inventory_service.update_inventory_item(item_id, data)
            else:
                data["current_stock"] = float(self.stock_field.value)
                new_id = self.inventory_service.create_inventory_item(data)
                if new_id:
                    success = True
            # show_info_dialog aun no se a definido
            if success:
                self.on_save()  # Llama al callback para refrescar la tabla
                self.close_dialog(e)
                show_info_dialog(self.page, "Éxito", "El insumo se ha guardado correctamente.")
            else:
                # El error más común aquí sería un nombre duplicado
                show_info_dialog(self.page, "Error", "No se pudo guardar el insumo. Es posible que el nombre ya exista.")

        except Exception as ex:
            show_info_dialog(self.page, "Error", f"Ocurrió un error inesperado: {ex}")
            print(ex)

    def show(self):
        self.page.dialog = self
        self.open = True
        self.page.update()
