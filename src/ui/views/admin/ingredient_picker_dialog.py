import flet as ft
from typing import Callable, Dict, Any
from src.services.inventory_service import InventoryService
from src.ui.theme import AppTheme

class IngredientPickerDialog(ft.AlertDialog):
    """
    Un diálogo para buscar, seleccionar y cuantificar un ingrediente para una receta.
    """
    def __init__(self, inventory_service: InventoryService, theme: AppTheme, on_ingredient_selected: Callable):
        super().__init__()
        self.inventory_service = inventory_service
        self.theme = theme
        self.on_ingredient_selected = on_ingredient_selected
        self.selected_ingredient = None

        self.modal = True
        self.title = ft.Text("Buscar Ingrediente")
        
        self.search_field = ft.TextField(
            label="Buscar insumo o producto...",
            on_change=self.perform_search,
            autofocus=True
        )
        self.results_list = ft.ListView(expand=True)
        self.quantity_field = ft.TextField(label="Cantidad", keyboard_type=ft.KeyboardType.NUMBER)

        # El contenido se cambiará dinámicamente entre búsqueda y confirmación
        self.search_view = ft.Column(
            controls=[
                self.search_field,
                ft.Container(content=self.results_list, expand=True)
            ],
            width=400,
            height=500
        )
        self.content = self.search_view
        
        self.actions = [
            ft.TextButton("Cancelar", on_click=self.close_dialog),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def perform_search(self, e):
        """Llama al servicio para buscar ingredientes y actualiza la lista."""
        search_term = e.control.value
        if len(search_term) < 2:
            self.results_list.controls.clear()
            self.update()
            return
        
        results = self.inventory_service.search_ingredients(search_term)
        self.results_list.controls.clear()
        for item in results:
            self.results_list.controls.append(
                ft.ListTile(
                    title=ft.Text(item['name']),
                    subtitle=ft.Text(f"Tipo: {item['type']}, Unidad: {item['unit']}"),
                    on_click=lambda e, i=item: self.select_ingredient(i)
                )
            )
        self.update()

    def select_ingredient(self, ingredient: Dict[str, Any]):
        """Muestra la vista para introducir la cantidad del ingrediente seleccionado."""
        self.selected_ingredient = ingredient
        self.title.value = f"Añadir {ingredient['name']}"
        
        self.content = ft.Column([
            ft.Text(f"Seleccionado: {ingredient['name']} ({ingredient['unit']})"),
            self.quantity_field
        ])
        
        self.actions = [
            ft.TextButton("Volver", on_click=self.show_search_view),
            ft.ElevatedButton("Confirmar", on_click=self.confirm_selection),
        ]
        self.update()

    def show_search_view(self, e):
        """Vuelve a la vista de búsqueda."""
        self.title.value = "Buscar Ingrediente"
        self.content = self.search_view
        self.actions = [
            ft.TextButton("Cancelar", on_click=self.close_dialog),
        ]
        self.update()

    def confirm_selection(self, e):
        """Confirma la selección y la cantidad, y llama al callback."""
        try:
            quantity = float(self.quantity_field.value)
            if quantity <= 0:
                self.quantity_field.error_text = "Debe ser mayor a 0"
                self.update()
                return

            # Preparar el diccionario del item de receta
            recipe_item = {
                "quantity": quantity,
                "inventory_item_id": self.selected_ingredient['id'] if self.selected_ingredient['type'] == 'INVENTORY' else None,
                "child_product_id": self.selected_ingredient['id'] if self.selected_ingredient['type'] == 'PRODUCT' else None,
                # Añadir info para la UI
                "item_name": self.selected_ingredient['name'] if self.selected_ingredient['type'] == 'INVENTORY' else None,
                "product_name": self.selected_ingredient['name'] if self.selected_ingredient['type'] == 'PRODUCT' else None,
            }

            self.on_ingredient_selected(recipe_item)
            self.close_dialog(e)

        except (ValueError, TypeError):
            self.quantity_field.error_text = "Cantidad inválida"
            self.update()

    def close_dialog(self, e):
        self.page.close(self)

    def show(self, page: ft.Page):
        self.page = page
        self.page.open(self)