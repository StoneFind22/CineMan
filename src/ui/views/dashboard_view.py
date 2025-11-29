import flet as ft
from datetime import datetime
from src.ui.theme import AppTheme # For type hint

class DashboardView:
    """Vista del dashboard principal, compatible con el nuevo sistema de temas."""
    
    def __init__(self, page: ft.Page, theme: AppTheme):
        self.page = page
        self.theme = theme

    def build(self):
        """Construye y retorna el contenido del dashboard."""
        
        welcome_text = ft.Text(
            "Bienvenido al Sistema POS Cinema",
            style=self.theme.text_theme.headline_medium
        )
        
        date_text = ft.Text(
            f"Hoy es {datetime.now().strftime('%A, %d de %B de %Y')}",
            style=self.theme.text_theme.title_medium
        )

        initial_message = ft.Text(
            "Actualmente, solo la funcionalidad de inicio de sesión está activa. "
            "Más módulos estarán disponibles en futuras versiones.",
            style=self.theme.text_theme.body_medium,
            color=self.theme.color_scheme.outline,
            italic=True,
            text_align=ft.TextAlign.CENTER
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    welcome_text,
                    ft.Container(height=10),
                    date_text,
                    ft.Container(height=50),
                    initial_message,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            expand=True,
            padding=20,
        )