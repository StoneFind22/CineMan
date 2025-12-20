import flet as ft
from typing import Dict, List
from src.services.inventory_service import InventoryService
from src.ui.theme import AppTheme
from src.ui.components.dialogs import show_info_dialog

class ProductDialog(ft.AlertDialog):
    """
    Un diálogo para crear o editar un Item del Catálogo Comercial (Producto).
    Incluye GESTOR INTELIGENTE DE CATEGORÍAS y CREACIÓN DE VARIANTES (Batch).
    """
    def __init__(self, page: ft.Page, inventory_service: InventoryService, theme: AppTheme, on_save: callable, product_data: dict = None):
        super().__init__()
        self.page = page
        self.inventory_service = inventory_service
        self.theme = theme
        self.on_save = on_save
        self.product_data = product_data
        self.is_edit = product_data is not None
        
        # --- Componentes de Categoría (Gestión Inteligente) ---
        self.categories_data = [] # Cache local
        self.category_dropdown = ft.Dropdown(
            label="Categoría",
            expand=True,
            enable_filter=True, # Permite escribir para buscar en la lista
            hint_text="Busque o seleccione..."
        )
        # Modo Creación: Campo de texto que aparece al dar click en "+"
        self.new_category_field = ft.TextField(
            label="Nueva Categoría (Enter para guardar)",
            expand=True,
            visible=False,
            autofocus=True,
            on_submit=self.save_new_category,
            suffix=ft.IconButton(icon=ft.Icons.CHECK, icon_color="green", tooltip="Guardar", on_click=self.save_new_category)
        )
        self.toggle_cat_btn = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE_OUTLINE, 
            tooltip="Crear nueva categoría", 
            on_click=self.toggle_category_mode
        )
        self.cancel_cat_btn = ft.IconButton(
            icon=ft.Icons.CANCEL, 
            tooltip="Cancelar creación", 
            icon_color="red",
            visible=False,
            on_click=self.toggle_category_mode
        )

        # Cargar categorías iniciales
        self.reload_categories()

        # --- Campos del formulario ---
        self.name_field = ft.TextField(label="Nombre Comercial (Base)", autofocus=True)
        self.description_field = ft.TextField(label="Descripción (para Menú Digital)", multiline=True, min_lines=2)
        
        # --- Lógica de Variantes ---
        self.has_variants_checkbox = ft.Checkbox(
            label="Crear múltiples tallas/presentaciones (Variantes)", 
            value=False,
            on_change=self.toggle_variants_mode,
            visible=not self.is_edit # Solo disponible al crear nuevo
        )
        
        # Contenedor para el precio único (Modo Normal)
        self.price_field = ft.TextField(label="Precio de Venta", keyboard_type=ft.KeyboardType.NUMBER, prefix_text="$", width=150)
        
        # Contenedor para múltiples variantes (Modo Variantes)
        self.variants_list = ft.Column(spacing=10)
        self.variants_container = ft.Container(
            content=ft.Column([
                ft.Text("Defina las variantes (ej: Pequeño, Mediano, Grande):", size=12, italic=True),
                self.variants_list,
                ft.TextButton("Añadir otra variante", icon=ft.Icons.ADD, on_click=self.add_variant_row)
            ]),
            visible=False,
            bgcolor="surfacevariant",
            padding=10,
            border_radius=5
        )

        # Configuraciones adicionales
        self.track_stock_checkbox = ft.Checkbox(label="Controlar Stock", value=True, tooltip="Si se marca, el sistema impedirá la venta si no hay insumos suficientes.")
        self.is_active_checkbox = ft.Checkbox(label="Disponible para Venta", value=True)

        if self.is_edit:
            self._fill_fields()
        else:
            # Si es nuevo, añadir al menos una fila de variante por defecto (aunque esté oculta)
            self.add_variant_row(None)

        # --- Configuración del Diálogo ---
        self.modal = True
        self.title = ft.Text("Gestión de Catálogo Comercial" if not self.is_edit else f"Editar: {self.product_data.get('name')}")
        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    self.name_field,
                    self.description_field,
                    
                    # Fila de Categoría Inteligente
                    ft.Row([
                        self.category_dropdown, 
                        self.new_category_field, 
                        self.toggle_cat_btn, 
                        self.cancel_cat_btn
                    ], expand=True, spacing=5),

                    # Sección de Precios / Variantes
                    self.has_variants_checkbox,
                    self.price_field,      # Visible solo si has_variants = False
                    self.variants_container, # Visible solo si has_variants = True

                    ft.Divider(),
                    ft.Text("Configuración Operativa", style=ft.TextThemeStyle.LABEL_LARGE),
                    ft.Row([
                        # Ya no mostramos el selector de tipo, asumimos SIMPLE por defecto
                        ft.Column([
                            self.track_stock_checkbox,
                            self.is_active_checkbox,
                        ])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text("Nota: La receta (ingredientes) se define en la pestaña 'Ingeniería de Menú'.", 
                            size=12, italic=True, color=ft.Colors.GREY_500)
                ],
                spacing=15,
                tight=True,
                scroll=ft.ScrollMode.AUTO
            ),
            width=600,
            height=600 if self.has_variants_checkbox.value else None
        )
        self.actions = [
            ft.TextButton("Cancelar", on_click=self.close_dialog),
            ft.ElevatedButton("Guardar Ficha Comercial", on_click=self.save_product),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def reload_categories(self, select_id=None):
        """Recarga la lista desde la BD y mantiene la selección si se indica."""
        self.categories_data = self.inventory_service.get_product_categories()
        self.category_dropdown.options = [
            ft.dropdown.Option(key=str(c['id']), text=c['name']) for c in self.categories_data
        ]
        if select_id:
            self.category_dropdown.value = str(select_id)
        
        # Solo actualizar visualmente si el control ya está montado en la página
        if self.category_dropdown.page:
            self.category_dropdown.update()

    def toggle_category_mode(self, e):
        """Alterna entre el Dropdown y el TextField de creación."""
        is_creating = self.new_category_field.visible
        
        # Invertir visibilidad
        self.category_dropdown.visible = is_creating
        self.toggle_cat_btn.visible = is_creating
        
        self.new_category_field.visible = not is_creating
        self.cancel_cat_btn.visible = not is_creating

        if not is_creating:
            # Entrando a modo creación
            self.new_category_field.value = ""
            self.new_category_field.error_text = None
            self.new_category_field.focus()
        else:
            # Cancelando creación
            self.new_category_field.value = ""
        
        self.content.update()

    def save_new_category(self, e):
        """Guarda la nueva categoría al presionar Enter o Check."""
        name = self.new_category_field.value
        if not name: return

        # Llamada al servicio inteligente (Validación y Normalización)
        result = self.inventory_service.create_product_category(name)

        if result['success']:
            # Éxito: Recargar lista, seleccionar la nueva, y volver a modo Dropdown
            self.reload_categories(select_id=result['id'])
            self.toggle_category_mode(None) # Cerrar modo creación
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Categoría '{result['name']}' creada."), bgcolor="green")
            self.page.snack_bar.open = True
            self.page.update()
        else:
            self.new_category_field.error_text = result['message']
            self.new_category_field.update()

    # --- Lógica de Variantes ---
    def toggle_variants_mode(self, e):
        use_variants = self.has_variants_checkbox.value
        self.price_field.visible = not use_variants
        self.variants_container.visible = use_variants
        self.content.update()

    def add_variant_row(self, e):
        row = ft.Row(controls=[
            ft.TextField(label="Sufijo / Talla (ej. Grande)", expand=2, dense=True),
            ft.TextField(label="Precio", expand=1, keyboard_type=ft.KeyboardType.NUMBER, prefix_text="$", dense=True),
            ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=lambda e: self.remove_variant_row(e.control.parent))
        ])
        self.variants_list.controls.append(row)
        if self.variants_list.page:
            self.variants_list.update()

    def remove_variant_row(self, row_control):
        if len(self.variants_list.controls) > 1:
            self.variants_list.controls.remove(row_control)
            self.variants_list.update()
        else:
            show_info_dialog(self.page, "Aviso", "Debe haber al menos una variante.")

    def _fill_fields(self):
        """Llena los campos del formulario si se está en modo edición."""
        # Sanitizar strings (evitar None)
        self.name_field.value = (self.product_data.get("name") or "").strip()
        self.description_field.value = (self.product_data.get("description") or "").strip()
        self.price_field.value = str(self.product_data.get("price", "0.00"))
        
        # Lógica Robusta para Dropdown de Categoría
        cat_id = self.product_data.get("category_id")
        if cat_id is not None:
            str_id = str(cat_id)
            # Verificar si el ID existe en las opciones actuales
            exists = any(opt.key == str_id for opt in self.category_dropdown.options)
            
            if not exists:
                self.category_dropdown.options.append(
                    ft.dropdown.Option(key=str_id, text=f"Categoría ID: {cat_id} (Archivada)")
                )
                if self.category_dropdown.page:
                    self.category_dropdown.update()
            
            self.category_dropdown.value = str_id

        self.track_stock_checkbox.value = self.product_data.get("track_stock", True)
        self.is_active_checkbox.value = self.product_data.get("is_active", True)

    def close_dialog(self, e):
        self.page.close(self)

    def save_product(self, e):
        """Valida y guarda los productos (Simple o Variantes)."""
        # 1. Verificar bloqueo de UI por creación de categoría pendiente
        if self.new_category_field.visible:
             show_info_dialog(self.page, "Acción Pendiente", "Termine de crear la categoría (presione Enter o Cancelar) antes de guardar.")
             return

        # 2. Validaciones Específicas (Feedback claro al usuario)
        if not self.name_field.value or not self.name_field.value.strip():
            self.name_field.error_text = "El nombre es obligatorio"
            self.name_field.update()
            return
        else:
            self.name_field.error_text = None # Limpiar error

        if not self.category_dropdown.value:
            show_info_dialog(self.page, "Campo Faltante", "Debe seleccionar una Categoría.")
            return

        # 3. Preparar datos comunes
        try:
            category_id = int(self.category_dropdown.value)
        except (ValueError, TypeError):
             show_info_dialog(self.page, "Error", "La categoría seleccionada no es válida.")
             return

        common_data = {
            "description": self.description_field.value.strip(),
            "category_id": category_id,
            "product_type": "SIMPLE", 
            "track_stock": self.track_stock_checkbox.value,
            "is_active": self.is_active_checkbox.value,
        }

        try:
            # MODO 1: Variantes (Solo creación)
            if self.has_variants_checkbox.value and not self.is_edit:
                # ... (Lógica de variantes se mantiene igual) ...
                base_name = self.name_field.value.strip()
                variants_to_create = []

                for row in self.variants_list.controls:
                    suffix = row.controls[0].value.strip()
                    price_str = row.controls[1].value
                    
                    if not suffix or not price_str:
                        show_info_dialog(self.page, "Error", "Todas las variantes deben tener Talla y Precio.")
                        return
                    
                    full_name = f"{base_name} - {suffix}"
                    variants_to_create.append({
                        **common_data,
                        "name": full_name,
                        "price": float(price_str)
                    })
                
                created_count = 0
                for v_data in variants_to_create:
                    if self.inventory_service.create_product(v_data):
                        created_count += 1
                
                if created_count > 0:
                    show_info_dialog(self.page, "Éxito", f"Se crearon {created_count} productos exitosamente.")
                    self.on_save()
                    self.page.close(self)
                else:
                    show_info_dialog(self.page, "Error", "No se pudo crear ningún producto.")

            # MODO 2: Producto Único
            else:
                # Validar precio solo si NO es variante
                price_val = 0.0
                if self.price_field.value:
                    try:
                        price_val = float(self.price_field.value)
                    except ValueError:
                        self.price_field.error_text = "Número inválido"
                        self.price_field.update()
                        return

                data = {
                    **common_data,
                    "name": self.name_field.value.strip(),
                    "price": price_val
                }

                success = False
                if self.is_edit:
                    success = self.inventory_service.update_product(self.product_data['id'], data)
                else:
                    new_id = self.inventory_service.create_product(data)
                    if new_id: success = True
                
                if success:
                    show_info_dialog(self.page, "Guardado", "Producto guardado exitosamente.")
                    self.on_save()
                    self.page.close(self)
                else:
                    show_info_dialog(self.page, "Error", "No se pudo guardar. Verifique si el nombre ya existe.")

        except Exception as ex:
            show_info_dialog(self.page, "Error Inesperado", f"Detalle: {ex}")

    def show(self):
        self.page.open(self)
