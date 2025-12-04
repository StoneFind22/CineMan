import flet as ft
from src.ui.screens.login_screen import LoginScreen
from src.ui.screens.main_screen import MainScreen
from src.services.user_service import UserManager
from src.ui.theme import light_theme, dark_theme

class Router:
    def __init__(self, page: ft.Page, user_manager: UserManager, animated_switcher: ft.AnimatedSwitcher, open_logout_dialog_callback):
        self.page = page
        self.user_manager = user_manager
        self.switcher = animated_switcher
        self.open_logout_dialog_callback = open_logout_dialog_callback
        self.toggle_theme_callback = None
        self.current_route = None
        self.routes = {
            "/login": self._build_login_screen,
            "/main": self._build_main_screen,
        }

    def navigate(self, route: str):
        """Navega a una ruta específica, actualizando el contenido del AnimatedSwitcher."""
        self.current_route = route
        
        view_builder = self.routes.get(route)
        if view_builder:
            self.switcher.content = view_builder()
        else:
            self.switcher.content = ft.Text(f"Error 404: Ruta '{route}' no encontrada.")
        
        self.page.update()

    def update_view(self):
        """Reconstruye la vista actual para reflejar cambios (ej. tema)."""
        if self.current_route:
            self.navigate(self.current_route)

    def _get_current_theme(self):
        """Retorna el objeto de tema actual (light o dark)."""
        return light_theme if self.page.theme_mode == ft.ThemeMode.LIGHT else dark_theme

    def _build_login_screen(self):
        """Construye y retorna el layout de la pantalla de login."""
        self.page.window_width = 800
        self.page.window_height = 600
        self.page.window.center()

        return LoginScreen(
            page=self.page,
            user_manager=self.user_manager, 
            toggle_theme_callback=self.toggle_theme_callback,
            router=self,
            theme=self._get_current_theme()
        ).build()

    def _build_main_screen(self):
        """Construye y retorna el layout de la pantalla principal."""
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.window.center()

        return MainScreen(
            page=self.page,
            user_manager=self.user_manager,
            toggle_theme_callback=self.toggle_theme_callback,
            router=self,
            theme=self._get_current_theme(),
            open_logout_dialog_callback=self.open_logout_dialog_callback
        ).build()