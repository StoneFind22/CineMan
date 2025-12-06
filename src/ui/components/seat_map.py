import flet as ft
from typing import Callable, Dict, Any, List

class SeatMap(ft.Container):
    """
    Un control de Flet para mostrar un mapa de asientos interactivo.
    """
    def __init__(
        self,
        seat_data: Dict[str, Any],
        on_seat_selection_change: Callable[[Dict[str, Any], bool], None],
        theme,
    ):
        super().__init__()
        self.seat_data = seat_data
        self.on_seat_selection_change = on_seat_selection_change
        self.theme = theme
        self.selected_seats = set()

        self.padding = 20
        self.alignment = ft.alignment.center
        self.content = self._build_map()

    def _build_map(self) -> ft.Control:
        """Construye la cuadrícula de asientos."""
        layout = self.seat_data.get("layout", {})
        seats = self.seat_data.get("seats", [])
        
        if not layout or not seats:
            return ft.Text("No se pudo cargar la información de la sala.")

        rows = []
        seats_by_row = {}
        for seat in seats:
            row = seat['seat_row']
            if row not in seats_by_row:
                seats_by_row[row] = []
            seats_by_row[row].append(seat)

        for row_letter in sorted(seats_by_row.keys()):
            seat_controls = [self._build_seat(seat) for seat in seats_by_row[row_letter]]
            rows.append(ft.Row(controls=seat_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=5))

        screen_display = ft.Container(
            content=ft.Text("PANTALLA", color=self.theme.color_scheme.on_surface),
            width=400,
            height=30,
            alignment=ft.alignment.center,
            border=ft.border.only(bottom=ft.BorderSide(4, self.theme.color_scheme.primary))
        )
        
        return ft.Column([screen_display, ft.Container(height=30)] + rows, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)

    def _build_seat(self, seat: Dict[str, Any]) -> ft.Control:
        """Construye un único control de asiento."""
        seat_id = seat["seat_id"]
        status = seat["status"]
        is_selected = seat_id in self.selected_seats

        color = self.theme.color_scheme.surface_variant
        if status == 'occupied':
            color = self.theme.color_scheme.outline
        elif is_selected:
            color = self.theme.color_scheme.primary

        return ft.Container(
            content=ft.Text(
                f"{seat['seat_row']}{seat['seat_col']}",
                size=10,
                color=self.theme.color_scheme.on_surface if not is_selected else self.theme.color_scheme.on_primary,
            ),
            width=40,
            height=40,
            alignment=ft.alignment.center,
            bgcolor=color,
            border_radius=5,
            on_click=lambda e, s=seat: self._on_seat_click(s),
            tooltip=f"Asiento {seat['seat_row']}{seat['seat_col']}"
        )

    def _on_seat_click(self, seat: Dict[str, Any]):
        """Maneja el evento de clic en un asiento."""
        seat_id = seat["seat_id"]
        if seat["status"] == 'occupied':
            return

        is_currently_selected = seat_id in self.selected_seats
        if is_currently_selected:
            self.selected_seats.remove(seat_id)
        else:
            self.selected_seats.add(seat_id)
        
        self.on_seat_selection_change(seat, not is_currently_selected)
        
        self.content = self._build_map()
        self.update()
