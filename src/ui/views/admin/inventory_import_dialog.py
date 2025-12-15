import flet as ft
import csv
import io
from typing import Callable, Dict, Any
from src.services.inventory_service import InventoryService
from src.ui.theme import AppTheme
from src.utils.security import current_session

class InventoryImportDialog(ft.AlertDialog):
    """
    Diálogo de varios pasos para importar insumos desde un archivo CSV.
    """
    def __init__(self, inventory_service: InventoryService, theme: AppTheme, on_complete: Callable):
        super().__init__()
        self.inventory_service = inventory_service
        self.theme = theme
        self.on_complete = on_complete
        self.parsed_data = None
        self.analysis_result = None

        self.modal = True
        self.title = ft.Text("Importar Insumos desde CSV")
        
        # --- File Picker ---
        self.file_picker = ft.FilePicker(on_result=self.on_file_selected)
        
        # --- Vistas del Diálogo ---
        self.upload_view = self._build_upload_view()
        self.preview_view = self._build_preview_view()
        self.loading_view = ft.Column([ft.ProgressRing(), ft.Text("Procesando...")], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self.content = self.upload_view
        self.actions = [ft.TextButton("Cancelar", on_click=self.close_dialog)]
        self.actions_alignment = ft.MainAxisAlignment.END

    def _build_upload_view(self):
        return ft.Column(
            [
                ft.Text("Selecciona un archivo CSV con las siguientes columnas:"),
                ft.Text("nombre, unidad_medida, cantidad_a_añadir, punto_reorden, costo_unitario", font_family="monospace"),
                ft.Text("Nota: 'nombre' y 'cantidad_a_añadir' son obligatorias.", size=12),
                ft.ElevatedButton(
                    "Seleccionar Archivo",
                    icon=ft.icons.UPLOAD_FILE,
                    on_click=lambda _: self.file_picker.pick_files(allow_multiple=False, allowed_extensions=["csv"]),
                ),
            ],
            width=500,
            spacing=10
        )

    def _build_preview_view(self):
        self.summary_text = ft.Text()
        self.to_create_list = ft.ListView(expand=True)
        self.to_update_list = ft.ListView(expand=True)
        self.errors_list = ft.ListView(expand=True)

        return ft.Column(
            [
                self.summary_text,
                ft.Tabs(
                    expand=True,
                    tabs=[
                        ft.Tab("Nuevos", content=self.to_create_list),
                        ft.Tab("Actualizar", content=self.to_update_list),
                        ft.Tab("Errores", content=self.errors_list),
                    ]
                )
            ],
            width=500,
            height=400,
            expand=True
        )

    def on_file_selected(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return

        file_path = e.files[0].path
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Usar DictReader para facilitar el acceso por nombre de columna
                reader = csv.DictReader(f)
                self.parsed_data = [row for row in reader]
            
            self.analyze_data()

        except Exception as ex:
            self.title.value = "Error al leer archivo"
            self.content = ft.Text(f"No se pudo procesar el archivo CSV. Asegúrate de que es un CSV válido y está codificado en UTF-8.\nDetalle: {ex}")
            self.actions = [ft.TextButton("Cerrar", on_click=self.close_dialog)]
            self.update()

    def analyze_data(self):
        self.content = self.loading_view
        self.update()

        self.analysis_result = self.inventory_service.analyze_inventory_csv(self.parsed_data)
        
        # Poblar la vista de previsualización
        summary = f"Resumen: {len(self.analysis_result['to_create'])} a crear, {len(self.analysis_result['to_update'])} a actualizar, {len(self.analysis_result['errors'])} errores."
        self.summary_text.value = summary

        self.to_create_list.controls = [ft.ListTile(title=ft.Text(item['name']), subtitle=ft.Text(f"Cantidad: {item['current_stock']} {item['unit']}")) for item in self.analysis_result['to_create']]
        self.to_update_list.controls = [ft.ListTile(title=ft.Text(item['name']), subtitle=ft.Text(f"Añadir: {item['quantity']}")) for item in self.analysis_result['to_update']]
        self.errors_list.controls = [ft.ListTile(title=ft.Text(f"Fila {err['row']}: {err.get('name', '')}"), subtitle=ft.Text(err['error'], color=ft.colors.ERROR)) for err in self.analysis_result['errors']]
        
        self.content = self.preview_view
        self.actions = [
            ft.TextButton("Cancelar", on_click=self.close_dialog),
            ft.ElevatedButton("Confirmar e Importar", on_click=self.execute_import, disabled=bool(self.analysis_result['errors'])),
        ]
        self.update()

    def execute_import(self, e):
        self.content = self.loading_view
        self.actions = []
        self.update()

        success = self.inventory_service.execute_inventory_import(self.analysis_result, current_session.user_id)
        
        if success:
            self.title.value = "Éxito"
            self.content = ft.Text("La importación se completó correctamente.")
            self.on_complete() # Llama al callback para refrescar la vista principal
        else:
            self.title.value = "Error"
            self.content = ft.Text("Ocurrió un error en la base de datos durante la importación.")

        self.actions = [ft.TextButton("Cerrar", on_click=self.close_dialog)]
        self.update()

    def close_dialog(self, e):
        self.open = False
        self.page.update()

    def show(self, page: ft.Page):
        self.page = page
        # El FilePicker debe estar en la overlay de la página para funcionar
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)
        self.page.dialog = self
        self.open = True
        self.page.update()
