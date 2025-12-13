import flet as ft
from src.ui.theme import AppTheme
from src.services.theater_service import TheaterService
from src.database.connection import DatabaseConnection
from src.models.models import Theater

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
                    on_click=self._open_new_theater_dialog
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
        if self.list_view.page:
            self.list_view.update()

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
                    ft.IconButton(ft.Icons.EDIT, tooltip="Editar Info"),
                ],
                alignment=ft.MainAxisAlignment.START
            ),
            padding=15,
            bgcolor=self.theme.color_scheme.surface_variant,
            border_radius=10
        )

    def _open_new_theater_dialog(self, e):
        print("Abriendo diálogo de nueva sala...")
        # Diálogo simple para crear sala (Nombre, Filas, Columnas)
        name_field = ft.TextField(label="Nombre de Sala", border_radius=8)
        rows_field = ft.TextField(label="Filas", value="10", keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
        cols_field = ft.TextField(label="Columnas", value="15", keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
        
        def on_create(e):
            print("Botón Crear Sala presionado.")
            try:
                t = Theater(name=name_field.value)
                rows = int(rows_field.value)
                cols = int(cols_field.value)
                print(f"Intentando crear sala: {t.name}, {rows}x{cols}")
                
                res = self.theater_service.create_theater(t, rows, cols)
                print(f"Resultado create_theater: {res}")
                
                self.page.close(dlg) # Close the specific dialog
                self._load_theaters()
                
                self.page.snack_bar = ft.SnackBar(ft.Text("Sala creada", color=ft.Colors.WHITE), bgcolor=ft.Colors.GREEN)
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                print(f"Excepción en on_create: {ex}")
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}", color=ft.Colors.WHITE), bgcolor=ft.Colors.RED)
                self.page.snack_bar.open = True
                self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Nueva Sala", weight=ft.FontWeight.BOLD),
            content=ft.Column([name_field, rows_field, cols_field], height=200, spacing=15),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Crear", on_click=on_create, bgcolor=self.theme.color_scheme.primary, color=self.theme.color_scheme.on_primary)
            ],
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        self.page.open(dlg)

    def _open_layout_editor(self, theater: Theater):
        from src.ui.views.admin.seat_editor_dialog import SeatEditorDialog
        
        def on_save():
            self.page.snack_bar = ft.SnackBar(ft.Text("Layout guardado exitosamente", color=ft.Colors.WHITE), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
            self.page.update()
            self._load_theaters()

        dlg = SeatEditorDialog(self.page, self.theme, theater, self.theater_service, on_save)
        self.page.open(dlg)
