import flet as ft
from typing import Callable
from src.ui.screens.login_screen import LoginScreen
from src.ui.screens.main_screen import MainScreen
from src.ui.views.sales_view import SalesView 
from src.services.user_service import UserManager
from src.services.inventory_service import InventoryService
from src.ui.theme import light_theme, dark_theme

class ViewProvider:
    """
    Provee y construye las vistas/pantallas principales de la aplicación,
    inyectando las dependencias y callbacks necesarios.
    """
    def __init__(self, page: ft.Page, user_manager: UserManager, sales_service, inventory_service: InventoryService):
        self.page = page
        self.user_manager = user_manager
        self.sales_service = sales_service
        self.inventory_service = inventory_service
        self.toggle_theme_callback = None
        self.open_logout_dialog_callback = None
        self._main_screen_instance = None

    def _get_current_theme(self):
        """Retorna el objeto de tema actual (light o dark)."""
        return light_theme if self.page.theme_mode == ft.ThemeMode.LIGHT else dark_theme

    def build_login_view(self, on_login_success: Callable[[], None]) -> ft.Control:
        """Construye y retorna la pantalla de login."""
        self.page.window_width = 800
        self.page.window_height = 600
        self.page.window.center()
        
        class FakeRouter:
            def navigate(self, route):
                if route == "/main":
                    on_login_success()
        
        return LoginScreen(
            page=self.page,
            user_manager=self.user_manager,
            toggle_theme_callback=self.toggle_theme_callback,
            router=FakeRouter(),
            theme=self._get_current_theme()
        ).build()

    def build_main_view(self, on_navigate_to_sales: Callable[[], None]) -> ft.Control:
        """Construye y retorna la pantalla principal (Dashboard, etc.)."""
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.window.center()

        class SalesViewRouter:
            def go_to_sales_view(self):
                on_navigate_to_sales()

        self._main_screen_instance = MainScreen(
            page=self.page,
            user_manager=self.user_manager,
            inventory_service=self.inventory_service,
            toggle_theme_callback=self.toggle_theme_callback,
            router=SalesViewRouter(),
            theme=self._get_current_theme(),
            open_logout_dialog_callback=self.open_logout_dialog_callback
        )
        return self._main_screen_instance.build()

    def build_sales_view(self, on_exit_sales: Callable[[], None]) -> ft.Control:
        """Construye y retorna la vista de ventas de pantalla completa."""
        self.page.window_width = 1280
        self.page.window_height = 720
        self.page.window.center()

        return SalesView(
            on_exit_sale_mode=on_exit_sales,
            theme=self._get_current_theme(),
            sales_service=self.sales_service
        )

    def update_theme(self):
        """Informa a las vistas activas sobre el cambio de tema."""
        if self._main_screen_instance:
            self._main_screen_instance.theme = self._get_current_theme()
            self._main_screen_instance.sidebar.update_theme(self._get_current_theme())
            self._main_screen_instance._update_main_content()
        self.page.update()