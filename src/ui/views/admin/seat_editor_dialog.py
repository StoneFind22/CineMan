import flet as ft
from src.models.models import Theater, Seat, SeatType, SeatStatus
from src.services.theater_service import TheaterService
from src.ui.theme import AppTheme

class SeatEditorDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page, theme: AppTheme, theater: Theater, theater_service: TheaterService, on_save):
        self.page = page
        self.theme = theme
        self.theater = theater
        self.theater_service = theater_service
        self.on_save = on_save
        self.seats = []
        self.current_tool = "select" # select, general, vip, disabled, broken, delete
        
        super().__init__(
            modal=True,
            title=ft.Text(f"Editor de Layout: {theater.name}"),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close),
                ft.ElevatedButton("Guardar Layout", on_click=self._save)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.content = self._build_editor()

    def _build_editor(self):
        self.seats = self.theater_service.get_theater_seats(self.theater.id)
        
        # Determine grid size
        max_x = max([s.x_position for s in self.seats]) if self.seats else 0
        max_y = max([s.y_position for s in self.seats]) if self.seats else 0
        
        self.grid_container = ft.Container(
            content=self._build_grid(max_x, max_y),
            width=800,
            height=500,
            border=ft.border.all(1, self.theme.color_scheme.outline),
            border_radius=10,
            padding=20,
            alignment=ft.alignment.center
        )
        
        return ft.Row(
            controls=[
                self._build_toolbar(),
                self.grid_container
            ],
            vertical_alignment=ft.CrossAxisAlignment.START
        )

    def _build_toolbar(self):
        tools = [
            ("select", ft.Icons.TOUCH_APP, "Seleccionar"),
            ("general", ft.Icons.EVENT_SEAT, "General"),
            ("vip", ft.Icons.CHAIR, "VIP"),
            ("disabled", ft.Icons.ACCESSIBLE, "Discapacitados"),
            ("broken", ft.Icons.BLOCK, "Bloqueado/Roto"),
            ("delete", ft.Icons.DELETE, "Borrar (Pasillo)"),
        ]
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Herramientas", weight=ft.FontWeight.BOLD),
                    *[self._build_tool_button(t[0], t[1], t[2]) for t in tools]
                ],
                spacing=10
            ),
            width=150,
            padding=10,
            bgcolor=self.theme.color_scheme.surface_variant,
            border_radius=10
        )

    def _build_tool_button(self, tool_id, icon, label):
        is_selected = self.current_tool == tool_id
        return ft.Container(
            content=ft.Row([ft.Icon(icon, size=20), ft.Text(label, size=12)], spacing=5),
            padding=10,
            bgcolor=self.theme.color_scheme.primary_container if is_selected else ft.Colors.TRANSPARENT,
            border_radius=5,
            ink=True,
            on_click=lambda e: self._select_tool(tool_id)
        )

    def _select_tool(self, tool_id):
        self.current_tool = tool_id
        self.content = self._build_editor() # Rebuild to update toolbar selection
        self.page.update()

    def _build_grid(self, max_x, max_y):
        # Create a map for quick access
        seat_map = {(s.x_position, s.y_position): s for s in self.seats}
        
        rows = []
        for y in range(max_y + 1):
            row_controls = []
            for x in range(max_x + 1):
                seat = seat_map.get((x, y))
                row_controls.append(self._build_seat_control(x, y, seat))
            rows.append(ft.Row(row_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=5))
            
        return ft.Column(rows, alignment=ft.MainAxisAlignment.CENTER, spacing=5, scroll=ft.ScrollMode.AUTO)

    def _build_seat_control(self, x, y, seat: Seat):
        color = ft.Colors.TRANSPARENT
        icon = None
        
        if seat:
            if seat.status != SeatStatus.ACTIVE.value:
                color = ft.Colors.RED_200
                icon = ft.Icons.BLOCK
            elif seat.seat_type_name == "VIP":
                color = ft.Colors.PURPLE_200
            elif seat.seat_type_name == "Discapacitados":
                color = ft.Colors.BLUE_200
                icon = ft.Icons.ACCESSIBLE
            else:
                color = ft.Colors.GREEN_200
        else:
            color = ft.Colors.GREY_100 # Empty space/aisle

        return ft.Container(
            content=ft.Icon(icon, size=16, color=ft.Colors.WHITE) if icon else None,
            width=30,
            height=30,
            bgcolor=color,
            border_radius=4,
            on_click=lambda e: self._on_seat_click(x, y, seat),
            tooltip=f"{seat.row_label}{seat.number}" if seat else f"Pos: {x},{y}"
        )

    def _on_seat_click(self, x, y, seat: Seat):
        if self.current_tool == "select":
            return # Info only
            
        if self.current_tool == "delete":
            if seat:
                self.seats.remove(seat)
                # TODO: Mark for deletion in DB or just remove from list and update layout
                # Actually, we might just mark it as inactive or remove row/col
                # For simplicity, let's say we just hide it (remove from list)
        
        elif self.current_tool in ["general", "vip", "disabled"]:
            # Find type ID
            # This is a bit hacky, ideally we have a map of type IDs
            type_map = {"general": 1, "vip": 2, "disabled": 3} # Assuming IDs from migration
            type_id = type_map.get(self.current_tool)
            
            if seat:
                seat.seat_type_id = type_id
                seat.seat_type_name = self.current_tool.upper() # Update for display
            else:
                # Create new seat at this position?
                # Complex logic for row/number assignment
                pass
        
        elif self.current_tool == "broken":
            if seat:
                seat.status = SeatStatus.BROKEN.value if seat.status == SeatStatus.ACTIVE.value else SeatStatus.ACTIVE.value

        self.content = self._build_editor()
        self.page.update()

    def _save(self, e):
        self.theater_service.update_seat_layout(self.seats)
        self.on_save()
        self.close(None)

    def close(self, e):
        self.page.close(self)
