import flet as ft
from typing import Dict
from src.services.inventory_service import InventoryService
from src.ui.theme import AppTheme
from src.ui.components.dialogs import show_info_dialog

class ProductDialog(ft.AlertDialog):
    """
    Un diálogo para crear o editar un Item del Catálogo Comercial (Producto).
    YA NO GESTIONA RECETAS. Solo define "Qué se vende".
    """
    def __init__(self, page: ft.Page, inventory_service: InventoryService, theme: AppTheme, on_save: callable, product_data: dict = None):
        super().__init__()
        self.page = page
        self.inventory_service = inventory_service
        self.theme = theme
        self.on_save = on_save
        self.product_data = product_data
        self.is_edit = product_data is not None
        
        # Cargar datos necesarios para los dropdowns
        self.categories = self.inventory_service.get_product_categories()

        # --- Campos del formulario ---
        self.name_field = ft.TextField(label="Nombre Comercial", autofocus=True)
        self.description_field = ft.TextField(label="Descripción (para Menú Digital)", multiline=True, min_lines=2)
        self.price_field = ft.TextField(label="Precio de Venta", keyboard_type=ft.KeyboardType.NUMBER, prefix_text="$")
        self.category_dropdown = ft.Dropdown(
            label="Categoría",
            options=[ft.dropdown.Option(key=cat['id'], text=cat['name']) for cat in self.categories]
        )
        self.type_dropdown = ft.Dropdown(
            label="Tipo de Item",
            options=[
                ft.dropdown.Option("SIMPLE", text="Producto Estándar"),
                ft.dropdown.Option("COMBO", text="Combo / Kit"),
            ],
            value="SIMPLE",
            hint_text="Define si se compone de insumos o de otros productos"
        )
        self.track_stock_checkbox = ft.Checkbox(label="Controlar Stock", value=True, tooltip="Si se marca, el sistema impedirá la venta si no hay insumos suficientes.")
        self.is_active_checkbox = ft.Checkbox(label="Disponible para Venta", value=True)

        if self.is_edit:
            self._fill_fields()

        # --- Configuración del Diálogo ---
        self.modal = True
        self.title = ft.Text("Gestión de Catálogo Comercial" if not self.is_edit else f"Editar: {self.product_data.get('name')}")
        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    self.name_field,
                    self.description_field,
                    ft.Row([
                        self.price_field,
                        self.category_dropdown,
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    ft.Text("Configuración Operativa", style=ft.TextThemeStyle.LABEL_LARGE),
                    ft.Row([
                        self.type_dropdown,
                        ft.Column([
                            self.track_stock_checkbox,
                            self.is_active_checkbox,
                        ])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text("Nota: La receta (ingredientes) se define en la pestaña 'Ingeniería de Menú'.", 
                            size=12, italic=True, color=ft.Colors.GREY_500)
                ],
                spacing=15,
                tight=True
            ),
            width=500
        )
        self.actions = [
            ft.TextButton("Cancelar", on_click=self.close_dialog),
            ft.ElevatedButton("Guardar Ficha Comercial", on_click=self.save_product),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def _fill_fields(self):
        """Llena los campos del formulario si se está en modo edición."""
        self.name_field.value = self.product_data.get("name", "")
        self.description_field.value = self.product_data.get("description", "")
        self.price_field.value = str(self.product_data.get("price", "0.00"))
        self.category_dropdown.value = self.product_data.get("category_id")
        self.type_dropdown.value = self.product_data.get("product_type", "SIMPLE")
        self.track_stock_checkbox.value = self.product_data.get("track_stock", True)
        self.is_active_checkbox.value = self.product_data.get("is_active", True)

    def close_dialog(self, e):
        self.page.close(self)

    def save_product(self, e):
        """Valida y guarda SOLAMENTE la información comercial del producto."""
        if not all([self.name_field.value, self.price_field.value, self.category_dropdown.value]):
            show_info_dialog(self.page, "Validación", "Nombre, Precio y Categoría son obligatorios para el catálogo.")
            return

        try:
            data = {
                "name": self.name_field.value,
                "description": self.description_field.value,
                "price": float(self.price_field.value),
                "category_id": int(self.category_dropdown.value),
                "product_type": self.type_dropdown.value,
                "track_stock": self.track_stock_checkbox.value,
                "is_active": self.is_active_checkbox.value,
            }

            success = False
            if self.is_edit:
                success = self.inventory_service.update_product(self.product_data['id'], data)
            else:
                new_id = self.inventory_service.create_product(data)
                if new_id:
                    success = True
            
            if success:
                show_info_dialog(self.page, "Catálogo Actualizado", "La ficha comercial se ha guardado. Configure la receta en 'Ingeniería de Menú'.")
                self.on_save()
                self.page.close(self)
            else:
                show_info_dialog(self.page, "Error de Base de Datos", "No se pudo guardar. Verifique si el nombre ya existe.")

        except ValueError:
            show_info_dialog(self.page, "Error de Formato", "El precio debe ser un número válido.")
        except Exception as ex:
            show_info_dialog(self.page, "Error Inesperado", f"Detalle: {ex}")

    def show(self):
        self.page.open(self)
