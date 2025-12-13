import flet as ft
from src.ui.theme import AppTheme
from src.services.theater_service import TheaterService
from src.database.connection import DatabaseConnection
from src.models.models import Theater
from src.ui.views.admin.theater_dialog import TheaterDialog
from src.ui.views.admin.seat_editor_dialog import SeatEditorDialog

class TheatersView(ft.Container):
    def __init__(self, page: ft.Page, theme: AppTheme):
        super().__init__(expand=True)
        self.page = page
        self.theme = theme
        self.db = DatabaseConnection()
        self.theater_service = TheaterService(self.db)
        self.theaters = []
        self.content = self._build_ui()

    def build(self):
        return self

    def _build_ui(self):
        return ft.Column(
            controls=[
                self._build_header(),
                self._build_toolbar(),
                self._build_theater_list(),
            ],
            spacing=20,
            expand=True
        )

    def _build_header(self):
        return ft.Row(
            controls=[
                ft.Icon(ft.Icons.CHAIR, size=32, color=self.theme.color_scheme.primary),
                ft.Text("Gestión de Salas", style=self.theme.text_theme.headline_medium, color=self.theme.color_scheme.on_surface),
            ],
            alignment=ft.MainAxisAlignment.START
        )

    def _build_toolbar(self):
        return ft.Row(
            controls=[
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Nueva Sala",
                    icon=ft.Icons.ADD,
                    style=ft.ButtonStyle(
                        bgcolor=self.theme.color_scheme.primary,
                        color=self.theme.color_scheme.on_primary,
                    ),
                    on_click=lambda e: self._open_theater_dialog()
                )
            ]
        )

    def _build_theater_list(self):
        self.list_view = ft.ListView(expand=True, spacing=10)
        self._load_theaters()
        return self.list_view

    def _load_theaters(self):
        self.theaters = self.theater_service.get_all_theaters()
        self.list_view.controls = [self._build_theater_item(t) for t in self.theaters]
        if self.page:
            self.page.update()

    def _build_theater_item(self, theater: Theater):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.MEETING_ROOM, size=40, color=self.theme.color_scheme.secondary),
                    ft.Column(
                        controls=[
                            ft.Text(theater.name, weight=ft.FontWeight.BOLD, size=16),
                            ft.Text(f"Capacidad: {theater.total_capacity} butacas", size=12, color=self.theme.color_scheme.outline),
                        ],
                        spacing=2
                    ),
                    ft.Container(expand=True),
                    ft.OutlinedButton("Diseñar Layout", icon=ft.Icons.GRID_ON, on_click=lambda e: self._open_layout_editor(theater)),
                    ft.IconButton(ft.Icons.EDIT, tooltip="Editar Info", on_click=lambda e: self._open_theater_dialog(theater)),
                    ft.IconButton(ft.Icons.DELETE, tooltip="Eliminar Sala", on_click=lambda e: self._open_delete_dialog(theater), icon_color=self.theme.color_scheme.error),
                ],
                alignment=ft.MainAxisAlignment.START
            ),
            padding=15,
            bgcolor=self.theme.color_scheme.surface_variant,
            border_radius=10
        )

    def _open_theater_dialog(self, theater: Theater = None):
        """Abre el diálogo para crear una nueva sala o editar una existente."""
        dialog = TheaterDialog(
            page=self.page,
            theme=self.theme,
            theater_service=self.theater_service,
            on_save=self._load_theaters, # Callback para refrescar la lista.
            theater=theater
        )
        self.page.open(dialog)

    def _open_delete_dialog(self, theater: Theater):
        """Abre un diálogo de confirmación antes de eliminar una sala."""
        def on_delete_confirm(e):
            try:
                self.theater_service.delete_theater(theater.id)
                self.page.close(delete_dialog)
                self._load_theaters()
                self.page.snack_bar = ft.SnackBar(ft.Text("Sala eliminada con éxito"), bgcolor=ft.Colors.GREEN)
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error al eliminar: {ex}"), bgcolor=ft.Colors.RED)
            self.page.snack_bar.open = True
            self.page.update()

        delete_dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Estás seguro de que quieres eliminar la sala '{theater.name}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(delete_dialog)),
                ft.ElevatedButton("Eliminar", on_click=on_delete_confirm, bgcolor=self.theme.color_scheme.error, color=self.theme.color_scheme.on_error),
            ],
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        self.page.open(delete_dialog)

    def _open_layout_editor(self, theater: Theater):
        """Abre el editor visual de layout de asientos para una sala."""
        def on_save():
            # Muestra feedback y recarga la lista para actualizar la capacidad.
            self.page.snack_bar = ft.SnackBar(ft.Text("Layout guardado exitosamente", color=ft.Colors.WHITE), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
            self._load_theaters()
            if self.page:
                self.page.update()

        dlg = SeatEditorDialog(self.page, self.theme, theater, self.theater_service, on_save)
        self.page.open(dlg)
