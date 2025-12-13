import flet as ft
import logging
from src.models.models import Theater
from src.services.theater_service import TheaterService
from src.ui.theme import AppTheme

logger = logging.getLogger(__name__)

class TheaterDialog(ft.AlertDialog):
    """Diálogo para crear o editar una sala de cine."""

    def __init__(self, page: ft.Page, theme: AppTheme, theater_service: TheaterService, on_save, theater: Theater = None):
        # Inicializa el diálogo en modo 'edición' o 'creación'.
        super().__init__(
            modal=True,
            title=ft.Text("Editar Sala" if theater else "Nueva Sala"),
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        self.page = page
        self.theme = theme
        self.theater_service = theater_service
        self.on_save = on_save
        self.theater = theater
        self.is_edit_mode = theater is not None

        self.content = self._build_content()
        self.actions = self._build_actions()

    def _build_content(self):
        """Construye el formulario del diálogo."""
        self.name_field = ft.TextField(
            label="Nombre de Sala",
            value=self.theater.name if self.is_edit_mode else "",
            border_radius=8
        )
        
        controls = [self.name_field]
        height = 100

        # Añade campos de filas y columnas solo en modo 'creación'.
        if not self.is_edit_mode:
            self.rows_field = ft.TextField(label="Filas", value="10", keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
            self.cols_field = ft.TextField(label="Columnas", value="15", keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
            controls.extend([self.rows_field, self.cols_field])
            height = 200
        
        return ft.Column(controls, height=height, spacing=15)

    def _build_actions(self):
        """Construye los botones de acción del diálogo."""
        return [
            ft.TextButton("Cancelar", on_click=self.close),
            ft.ElevatedButton(
                "Guardar" if self.is_edit_mode else "Crear",
                on_click=self._save_or_create,
                bgcolor=self.theme.color_scheme.primary,
                color=self.theme.color_scheme.on_primary
            )
        ]

    def _save_or_create(self, e):
        """Maneja la lógica de guardar o crear la sala."""
        try:
            if self.is_edit_mode:
                self.theater.name = self.name_field.value
                self.theater_service.update_theater(self.theater)
                message = "Sala actualizada"
            else:
                new_theater = Theater(name=self.name_field.value)
                rows = int(self.rows_field.value)
                cols = int(self.cols_field.value)
                self.theater_service.create_theater(new_theater, rows, cols)
                message = "Sala creada"
            
            # Muestra feedback al usuario y actualiza la vista principal.
            self.page.snack_bar = ft.SnackBar(ft.Text(message, color=ft.Colors.WHITE), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
            self.on_save()
            self.close(e)

        except Exception as ex:
            logger.exception(f"Error al guardar sala: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}", color=ft.Colors.WHITE), bgcolor=ft.Colors.RED)
            self.page.snack_bar.open = True
        
        self.page.update()

    def close(self, e):
        """Cierra el diálogo."""
        self.page.close(self)