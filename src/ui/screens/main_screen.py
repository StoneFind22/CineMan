import flet as ft
from datetime import datetime
from src.utils.security import current_session
from src.ui.views.dashboard_view import DashboardView
from src.ui.components.dialogs import ChangePasswordDialog
from src.services.user_service import UserManager
from src.ui.theme import AppTheme
from src.ui.components.sidebar import Sidebar

class MainScreen:
    """
    Pantalla principal del sistema, rediseñada para ser dinámica y compatible
    con el nuevo sistema de temas y router.
    """
    
    def __init__(self, page: ft.Page, user_manager: UserManager, toggle_theme_callback, router, theme: AppTheme, open_logout_dialog_callback):
        self.page = page
        self.user_manager = user_manager
        self.toggle_theme_callback = toggle_theme_callback
        self.router = router
        self.theme = theme
        self.open_logout_dialog_callback = open_logout_dialog_callback
        self.current_view = "dashboard"
        self.content_area = ft.Container(expand=True)
        self.sidebar_expanded = True
        self.sidebar = Sidebar(self, self.theme, self.sidebar_expanded)

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
                        self.sidebar,
                        self.content_area
                    ],
                    expand=True,
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.START
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
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.MENU,
                            tooltip="Toggle Sidebar",
                            on_click=self._toggle_sidebar,
                            icon_color=self.theme.color_scheme.on_primary
                        ),
                        ft.Image(src="src/assets/logoweb.webp", height=40, fit=ft.ImageFit.CONTAIN),
                        ft.Text("POS CINEMA", style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                    ], spacing=10),
                    ft.Container(expand=True),
                    user_info,
                    ft.Container(width=20),
                    ft.Row([
                        theme_button,
                        ft.IconButton(icon=ft.Icons.LOCK_RESET, tooltip="Cambiar contraseña", on_click=self.show_change_password, icon_color=ft.Colors.WHITE),
                        ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Cerrar sesión", on_click=self.show_logout_dialog, icon_color=ft.Colors.WHITE)
                    ])
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            gradient=ft.LinearGradient(
                begin=ft.alignment.center_left,
                end=ft.alignment.center_right,
                colors=[
                    self.theme.palette["primary"],
                    self.theme.palette["primary_container"]
                ]
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            height=70,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            )
        )

    def _toggle_sidebar(self, e):
        self.sidebar.toggle()
        self.page.update()

    def _update_main_content(self):
        """Actualiza el área de contenido principal."""
        if self.current_view == "dashboard":
             dashboard_view = DashboardView(self.page, self.theme)
             self.content_area.content = dashboard_view.build()
        else:
             self.content_area.content = ft.Text(f"Vista '{self.current_view}' no implementada.")
        
        
        self.content_area.bgcolor = self.theme.color_scheme.surface
        self.page.update()
    
    def show_change_password(self, e):
        """Muestra el diálogo de cambio de contraseña."""
        dialog = ChangePasswordDialog(self.page, self.user_manager, self.theme)
        dialog.show()
    
    def show_logout_dialog(self, e):
        """Llama al callback de nivel superior para mostrar el diálogo de logout."""
        self.open_logout_dialog_callback(e)