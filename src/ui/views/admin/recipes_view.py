import flet as ft
from src.services.inventory_service import InventoryService
from src.ui.theme import AppTheme
from src.ui.components.dialogs import show_info_dialog, show_confirm_dialog
from src.ui.views.admin.ingredient_picker_dialog import IngredientPickerDialog

class RecipesView(ft.Container):
    """
    Vista de 'Ingeniería de Menú'.
    Permite seleccionar un producto del catálogo y definir su composición (Receta/BOM).
    """
    def __init__(self, page: ft.Page, inventory_service: InventoryService, theme: AppTheme):
        super().__init__()
        self.page = page
        self.inventory_service = inventory_service
        self.theme = theme
        self.expand = True
        
        # Estado
        self.selected_product = None
        self.current_recipe = []

        # --- Controles UI ---
        
        # Panel Izquierdo: Lista de Productos
        self.product_list = ft.ListView(expand=True, spacing=2)
        self.product_search = ft.TextField(
            label="Buscar Producto...", 
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.filter_products
        )
        
        # Panel Derecho: Editor de Receta
        self.recipe_header = ft.Text("Seleccione un producto para editar su receta", style=ft.TextThemeStyle.TITLE_MEDIUM, italic=True)
        self.recipe_list = ft.ListView(expand=True, spacing=5)
        self.add_ingredient_btn = ft.ElevatedButton(
            "Añadir Componente", 
            icon=ft.Icons.ADD_CIRCLE_OUTLINE, 
            on_click=self.open_ingredient_picker,
            disabled=True
        )
        self.save_recipe_btn = ft.ElevatedButton(
            "Guardar Estructura", 
            icon=ft.Icons.SAVE, 
            on_click=self.save_current_recipe,
            disabled=True
        )

        self._build_ui()
        # self.load_products() se moverá a did_mount

    def did_mount(self):
        """Se ejecuta cuando el control es añadido a la página."""
        self.load_products()

    def _build_ui(self):
        # Panel Izquierdo
        left_panel = ft.Container(
            content=ft.Column([
                ft.Text("Catálogo Comercial", style=ft.TextThemeStyle.TITLE_SMALL, weight=ft.FontWeight.BOLD),
                self.product_search,
                ft.Container(self.product_list, expand=True, border=ft.border.all(1, ft.Colors.OUTLINE), border_radius=5)
            ]),
            width=300,
            padding=10,
            bgcolor=self.theme.color_scheme.surface_variant,
            border_radius=10
        )

        # Panel Derecho
        right_panel = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=self.recipe_header,
                    padding=10,
                    bgcolor=self.theme.color_scheme.primary_container,
                    border_radius=5
                ),
                ft.Divider(),
                ft.Row([self.add_ingredient_btn, self.save_recipe_btn], alignment=ft.MainAxisAlignment.END),
                ft.Container(
                    content=self.recipe_list,
                    expand=True,
                    border=ft.border.all(1, ft.Colors.OUTLINE),
                    border_radius=5,
                    padding=10
                )
            ]),
            expand=True,
            padding=10
        )

        self.content = ft.Row([left_panel, ft.VerticalDivider(width=1), right_panel], expand=True)

    def load_products(self):
        self.all_products = self.inventory_service.get_products_with_category()
        self.render_product_list(self.all_products)

    def filter_products(self, e):
        term = e.control.value.lower()
        filtered = [p for p in self.all_products if term in p['name'].lower()]
        self.render_product_list(filtered)

    def render_product_list(self, products):
        self.product_list.controls.clear()
        for p in products:
            # Indicador visual si ya tiene receta
            has_recipe_icon = ft.Icons.CHECK_CIRCLE if self._product_has_recipe(p['id']) else ft.Icons.RADIO_BUTTON_UNCHECKED
            color = ft.Colors.GREEN if self._product_has_recipe(p['id']) else ft.Colors.GREY
            
            tile = ft.ListTile(
                leading=ft.Icon(has_recipe_icon, color=color, size=16),
                title=ft.Text(p['name'], size=14, weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(f"{p['product_type']} - ${p['price']}", size=12),
                on_click=lambda e, prod=p: self.select_product(prod),
                selected=self.selected_product and self.selected_product['id'] == p['id']
            )
            self.product_list.controls.append(tile)
        
        # Solo actualizar si el control ya está montado en la página
        if self.page:
            self.product_list.update()

    def _product_has_recipe(self, product_id):
        # Esta lógica idealmente vendría del servicio para no hacer N+1 queries, 
        # pero por ahora lo simulamos o asumimos que 'products' trae un flag.
        # TODO: Optimizar en InventoryService
        return False 

    def select_product(self, product):
        self.selected_product = product
        
        # Actualizar Header
        self.recipe_header.value = f"Editando Estructura de: {product['name']} ({product['product_type']})"
        self.recipe_header.style = ft.TextThemeStyle.TITLE_LARGE
        self.recipe_header.update()

        # Cargar Receta
        self.current_recipe = self.inventory_service.get_recipe_for_product(product['id'])
        self.render_recipe_table()

        # Habilitar botones
        self.add_ingredient_btn.disabled = False
        self.save_recipe_btn.disabled = False
        self.update()

    def render_recipe_table(self):
        self.recipe_list.controls.clear()
        
        if not self.current_recipe:
            self.recipe_list.controls.append(
                ft.Text("Este producto no tiene componentes asignados. Es un producto 'vacío'.", italic=True, text_align=ft.TextAlign.CENTER)
            )
            return

        # Crear tabla de items
        for idx, item in enumerate(self.current_recipe):
            name = item.get('item_name') or item.get('product_name')
            type_label = "INSUMO" if item.get('inventory_item_id') else "SUB-PRODUCTO"
            qty = float(item['quantity'])
            unit = item.get('unit', 'un')

            card = ft.Card(
                content=ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CATEGORY if type_label == "INSUMO" else ft.Icons.FASTFOOD, color=ft.Colors.BLUE_GREY),
                        ft.Column([
                            ft.Text(name, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{type_label}", size=10, color=ft.Colors.GREY),
                        ], expand=True),
                        ft.Text(f"{qty} {unit}", weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.Icons.DELETE, 
                            icon_color=ft.Colors.RED, 
                            tooltip="Quitar",
                            on_click=lambda e, i=idx: self.remove_component(i)
                        )
                    ]),
                    padding=10
                )
            )
            self.recipe_list.controls.append(card)
        self.recipe_list.update()

    def open_ingredient_picker(self, e):
        def on_selected(component):
            # Validar que no se agregue a sí mismo ni cree ciclos simples (TODO: Validación profunda en backend)
            if component.get('child_product_id') == self.selected_product['id']:
                show_info_dialog(self.page, "Error Circular", "Un producto no puede contenerse a sí mismo.")
                return

            self.current_recipe.append(component)
            self.render_recipe_table()

        picker = IngredientPickerDialog(
            inventory_service=self.inventory_service, 
            theme=self.theme, 
            on_ingredient_selected=on_selected
        )
        # Mostrar solo Insumos si es SIMPLE, o Ambos si es COMBO?
        # Por regla de negocio anterior: SIMPLE -> Insumos, COMBO -> Productos.
        # Pero permitiremos flexibilidad por ahora.
        picker.show(self.page)

    def remove_component(self, index):
        self.current_recipe.pop(index)
        self.render_recipe_table()

    def save_current_recipe(self, e):
        if not self.selected_product: return
        
        success = self.inventory_service.update_recipe_for_product(
            self.selected_product['id'], 
            self.current_recipe
        )
        
        if success:
            show_info_dialog(self.page, "Estructura Guardada", f"La receta de '{self.selected_product['name']}' ha sido actualizada.")
            self.load_products() # Recargar lista para actualizar iconos
        else:
            show_info_dialog(self.page, "Error", "No se pudo guardar la estructura.")

