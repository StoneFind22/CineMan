import flet as ft
from datetime import datetime
from src.config.settings import Config
from src.utils.security import current_session
from src.ui.views.dashboard_view import DashboardView
from src.ui.components.dialogs import ChangePasswordDialog
from src.services.user_service import UserManager
from src.database.connection import db
from src.ui.theme import AppTheme

class MainScreen:
    """
    Pantalla principal del sistema, rediseñada para ser dinámica y compatible
    con el nuevo sistema de temas y router.
    """
    
    def __init__(self, page: ft.Page, toggle_theme_callback, router, theme: AppTheme, open_logout_dialog_callback):
        self.page = page
        self.toggle_theme_callback = toggle_theme_callback
        self.router = router
        self.theme = theme
        self.open_logout_dialog_callback = open_logout_dialog_callback
        self.current_view = "dashboard"
        self.content_area = ft.Container(expand=True)

    def show(self):
        """Construye y muestra la UI de la pantalla principal en la página."""
        self.page.add(self.build())
        self._update_main_content()

    def build(self):
        """Construye y retorna el layout completo de la pantalla principal."""
        self.page.bgcolor = self.theme.color_scheme.background
        
        return ft.Column(
            controls=[
                self._build_app_bar(),
                ft.Row(
                    controls=[
                        self._build_sidebar(),
                        ft.VerticalDivider(width=1, color=self.theme.color_scheme.outline),
                        self.content_area
                    ],
                    expand=True,
                    spacing=0
                )
            ],
            spacing=0
        )

    def _build_app_bar(self):
        """Construye y retorna la barra superior usando el tema actual."""
        user_info = ft.Row([
            ft.Icon(ft.Icons.PERSON, size=20, color=self.theme.color_scheme.on_primary),
            ft.Text(current_session.username, weight=ft.FontWeight.BOLD, color=self.theme.color_scheme.on_primary),
            ft.Text(f"({current_session.role})", size=12, color=self.theme.color_scheme.on_primary),
            ft.Text("|", color=self.theme.color_scheme.on_primary),
            ft.Text(datetime.now().strftime("%d/%m/%Y %H:%M"), size=12, color=self.theme.color_scheme.on_primary)
        ], spacing=10)

        theme_button = ft.IconButton(
            icon=ft.Icons.LIGHT_MODE if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.DARK_MODE,
            tooltip="Alternar tema",
            on_click=self.toggle_theme_callback,
            icon_color=self.theme.color_scheme.on_primary
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("POS CINEMA", style=self.theme.text_theme.headline_small, color=self.theme.color_scheme.on_primary),
                    ft.Container(expand=True),
                    user_info,
                    ft.Container(width=20),
                    ft.Row([
                        theme_button,
                        ft.IconButton(icon=ft.Icons.LOCK_RESET, tooltip="Cambiar contraseña", on_click=self.show_change_password, icon_color=self.theme.color_scheme.on_primary),
                        ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Cerrar sesión", on_click=self.show_logout_dialog, icon_color=self.theme.color_scheme.on_primary)
                    ])
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor=self.theme.color_scheme.primary,
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            height=70
        )

    def _build_sidebar(self):
        """Construye y retorna el menú lateral."""
        return ft.Container(
            content=ft.Column(
                [self._build_menu_item("dashboard", "Dashboard", ft.Icons.DASHBOARD, self._navigate_to_dashboard)],
                spacing=5,
                scroll=ft.ScrollMode.AUTO
            ),
            width=250,
            bgcolor=self.theme.palette["surface"],
            padding=15
        )

    def _build_menu_item(self, view_id: str, title: str, icon: str, on_click_action):
        """Construye un elemento del menú."""
        is_selected = self.current_view == view_id
        
        return ft.Container(
            content=ft.Row(
                [ft.Icon(icon, size=20), ft.Text(title, style=self.theme.text_theme.title_medium)],
                spacing=15
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            bgcolor=self.theme.color_scheme.primary_container if is_selected else ft.Colors.TRANSPARENT,
            border_radius=8,
            ink=True,
            on_click=lambda e: on_click_action(view_id)
        )

    def _update_main_content(self):
        """Actualiza el área de contenido principal."""
        if self.current_view == "dashboard":
            dashboard_view = DashboardView(self.page, self.theme)
            self.content_area.content = dashboard_view.build()
        else:
            self.content_area.content = ft.Text(f"Vista '{self.current_view}' no implementada.")
        
        self.content_area.bgcolor = self.theme.color_scheme.surface
        self.page.update()

    def _navigate_to_dashboard(self, view_id: str):
        """Navega a la vista del dashboard."""
        self.current_view = view_id
        self._update_main_content()
    
    def show_change_password(self, e):
        """Muestra el diálogo de cambio de contraseña."""
        user_manager = UserManager(db)
        dialog = ChangePasswordDialog(self.page, user_manager, self.theme)
        dialog.show()
    
    def show_logout_dialog(self, e):
        """Llama al callback de nivel superior para mostrar el diálogo de logout."""
        self.open_logout_dialog_callback(e)