import flet as ft
import flet as ft
from typing import Callable

class DashboardView:
    """Vista del dashboard principal, que ahora incluye el botón de Nueva Venta."""
    
    def __init__(self, on_new_sale_click: Callable[[], None], theme):
        self.on_new_sale_click = on_new_sale_click
        self.theme = theme

    def build(self) -> ft.Control:
        """Construye y retorna el contenido del dashboard."""
        
        welcome_text = ft.Text(
            "Bienvenido al Sistema",
            style=self.theme.text_theme.headline_large,
            text_align=ft.TextAlign.CENTER
        )
        
        new_sale_button = ft.ElevatedButton(
            text="Nueva Venta",
            icon=ft.Icons.POINT_OF_SALE,
            on_click=lambda e: self.on_new_sale_click(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.padding.symmetric(horizontal=30, vertical=20),
                bgcolor=self.theme.color_scheme.primary,
                color=self.theme.color_scheme.on_primary,
            ),
            height=60,
        )

        return ft.Container(
            content=ft.Column(
                [
                    welcome_text,
                    ft.Container(height=40),
                    new_sale_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            expand=True,
            padding=30,
        )