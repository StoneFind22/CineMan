import flet as ft
from src.ui.theme import AppTheme

class SettingsView:
    def __init__(self, page: ft.Page, theme: AppTheme):
        self.page = page
        self.theme = theme

    def build(self):
        return ft.Column(
            controls=[
                ft.Text("Vista de Configuración", style=self.theme.text_theme.headline_medium)
            ]
        )
