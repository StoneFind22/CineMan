import flet as ft
from typing import List, Dict, Any, Optional
from src.services.inventory_service import InventoryService
from src.ui.theme import AppTheme
from src.ui.components.dialogs import show_info_dialog
from src.ui.views.admin.ingredient_picker_dialog import IngredientPickerDialog

class ProductDialog(ft.AlertDialog):
    """
    Un diálogo para crear o editar un Producto y su receta.
    """
    def __init__(self, page: ft.Page, inventory_service: InventoryService, theme: AppTheme, on_save: callable, product_data: dict = None):
        super().__init__()
        self.page = page
        self.inventory_service = inventory_service
        self.theme = theme
        self.on_save = on_save
        self.product_data = product_data
        self.is_edit = product_data is not None
        
        self.recipe_items = []
        
        # Cargar datos necesarios para los dropdowns
        self.categories = self.inventory_service.get_product_categories()

        # --- Campos del formulario ---
        self.name_field = ft.TextField(label="Nombre del Producto", autofocus=True)
        self.description_field = ft.TextField(label="Descripción", multiline=True, min_lines=2)
        self.price_field = ft.TextField(label="Precio", keyboard_type=ft.KeyboardType.NUMBER, prefix_text="$")
        self.category_dropdown = ft.Dropdown(
            label="Categoría",
            options=[ft.dropdown.Option(key=cat['id'], text=cat['name']) for cat in self.categories]
        )
        self.type_dropdown = ft.Dropdown(
            label="Tipo de Producto",
            options=[
                ft.dropdown.Option("SIMPLE"),
                ft.dropdown.Option("COMBO"),
            ],
            value="SIMPLE"
        )
        self.track_stock_checkbox = ft.Checkbox(label="Rastrear Stock", value=True)
        self.is_active_checkbox = ft.Checkbox(label="Producto Activo", value=True)

        self.recipe_list_view = ft.ListView(expand=True)

        if self.is_edit:
            self._fill_fields()
            self._load_recipe()

        # --- Pestañas para Info y Receta ---
        self.tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Información General", content=self._build_info_tab()),
                ft.Tab(text="Receta", content=self._build_recipe_tab()),
            ],
            expand=True,
        )

        # --- Configuración del Diálogo ---
        self.modal = True
        self.title = ft.Text("Nuevo Producto" if not self.is_edit else "Editar Producto")
        self.content = self.tabs
        self.actions = [
            ft.TextButton("Cancelar", on_click=self.close_dialog),
            ft.ElevatedButton("Guardar", on_click=self.save_product),
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
        if self.type_dropdown.value == "COMBO":
            self.tabs.selected_index = 1

    def _load_recipe(self):
        """Carga la receta existente para un producto."""
        self.recipe_items = self.inventory_service.get_recipe_for_product(self.product_data['id'])
        self._update_recipe_list_ui()

    def _build_info_tab(self):
        """Construye la pestaña de información general del producto."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    self.name_field,
                    self.description_field,
                    ft.Row([
                        self.price_field,
                        self.category_dropdown,
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        self.type_dropdown,
                    ]),
                    self.track_stock_checkbox,
                    self.is_active_checkbox,
                ]
            ),
            padding=ft.padding.only(top=20)
        )

    def _build_recipe_tab(self):
        """Construye la pestaña para el constructor de recetas."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.ElevatedButton("Añadir Ingrediente", icon=ft.Icons.ADD, on_click=self.open_ingredient_picker),
                    ft.Container(
                        content=self.recipe_list_view,
                        expand=True,
                        border=ft.border.all(1, self.theme.color_scheme.outline),
                        border_radius=8,
                        padding=5
                    )
                ]
            ),
            padding=ft.padding.only(top=20)
        )
    
    def _update_recipe_list_ui(self):
        """Refresca la lista de ingredientes en la UI."""
        self.recipe_list_view.controls.clear()
        for item in self.recipe_items:
            # Determina el nombre del ingrediente
            name = item.get('item_name') or item.get('product_name')
            
            self.recipe_list_view.controls.append(
                ft.ListTile(
                    title=ft.Text(f"{name}"),
                    subtitle=ft.Text(f"Cantidad: {item['quantity']}"),
                    trailing=ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        tooltip="Quitar ingrediente",
                        on_click=lambda e, i=item: self._remove_recipe_item(i)
                    ),
                )
            )
        # Es importante actualizar el diálogo mismo para que los cambios se reflejen
        if self.open:
            self.update()

    def _remove_recipe_item(self, item_to_remove):
        self.recipe_items.remove(item_to_remove)
        self._update_recipe_list_ui()

    def open_ingredient_picker(self, e):
        """Abre el diálogo para seleccionar un ingrediente."""
        def on_selected(ingredient: Dict[str, Any]):
            # Evitar duplicados
            for item in self.recipe_items:
                if (item.get('inventory_item_id') and item.get('inventory_item_id') == ingredient.get('inventory_item_id')) or \
                   (item.get('child_product_id') and item.get('child_product_id') == ingredient.get('child_product_id')):
                    show_info_dialog(self.page, "Error", "Este ingrediente ya está en la receta.")
                    return
            
            self.recipe_items.append(ingredient)
            self._update_recipe_list_ui()
            
        picker = IngredientPickerDialog(
            inventory_service=self.inventory_service,
            theme=self.theme,
            on_ingredient_selected=on_selected
        )
        picker.show(self.page)

    def close_dialog(self, e):
        self.open = False
        self.page.update()

    def save_product(self, e):
        """Valida y guarda la información del producto y su receta."""
        if not all([self.name_field.value, self.price_field.value, self.category_dropdown.value]):
            show_info_dialog(self.page, "Error", "Nombre, Precio y Categoría son requeridos.")
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

            product_id = None
            if self.is_edit:
                success = self.inventory_service.update_product(self.product_data['id'], data)
                if success:
                    product_id = self.product_data['id']
            else:
                new_id = self.inventory_service.create_product(data)
                if new_id:
                    success = True
                    product_id = new_id
            
            if success and product_id:
                # Guardar la receta
                self.inventory_service.update_recipe_for_product(product_id, self.recipe_items)
                
                show_info_dialog(self.page, "Éxito", "Producto guardado correctamente.")
                self.on_save()
                self.close_dialog(e)
            else:
                show_info_dialog(self.page, "Error", "No se pudo guardar el producto. El nombre puede que ya exista.")

        except ValueError:
            show_info_dialog(self.page, "Error", "El precio debe ser un número válido.")
        except Exception as ex:
            show_info_dialog(self.page, "Error", f"Ocurrió un error inesperado: {ex}")

    def show(self):
        self.page.dialog = self
        self.open = True
        self.page.update()