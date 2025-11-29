import flet as ft
from src.config.settings import Config
from src.database.connection import db
from src.services.user_service import UserManager
from src.ui.theme import light_theme, dark_theme
from src.ui.router import Router
from src.utils.security import current_session

def main(page: ft.Page):
    """Función principal de la aplicación"""
    
    page.title = Config.APP_TITLE
    page.window_resizable = True
    page.window_min_width = 800
    page.window_min_height = 600
    
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = light_theme.text_theme
    page.dark_theme = dark_theme.text_theme
    page.padding = 0

    animated_switcher = ft.AnimatedSwitcher(
        content=ft.Container(),
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=500,
        reverse_duration=200,
        expand=True
    )
    
    def open_logout_dialog(e):
        def confirm_logout(e_confirm):
            current_session.logout()
            page.close(dialog)
            router.navigate("/login")
        
        def cancel_logout(e_cancel):
            page.close(dialog)

        current_theme = light_theme if page.theme_mode == ft.ThemeMode.LIGHT else dark_theme
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cerrar Sesión", style=current_theme.text_theme.title_large),
            content=ft.Text("¿Está seguro que desea cerrar la sesión?", style=current_theme.text_theme.body_medium),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel_logout),
                ft.ElevatedButton("Cerrar Sesión", on_click=confirm_logout, bgcolor=current_theme.color_scheme.error)
            ],
            bgcolor=current_theme.color_scheme.surface,
        )
        page.open(dialog)

    user_manager = UserManager(db)
    router = Router(page, user_manager, animated_switcher, open_logout_dialog)

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        page.theme = light_theme.text_theme if page.theme_mode == ft.ThemeMode.LIGHT else dark_theme.text_theme
        router.update_view()

    router.toggle_theme_callback = toggle_theme
    
    page.add(animated_switcher)

    if not db.test_connection():
        animated_switcher.content = ft.Text("Error de conexión a la base de datos. Revise .env")
        page.update()
        return
    
    router.navigate("/login")

if __name__ == "__main__":
    ft.app(target=main)
