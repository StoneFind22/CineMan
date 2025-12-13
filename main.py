import flet as ft
from src.config.settings import Config
from src.database.connection import DatabaseConnection
from src.services.user_service import UserManager
from src.services.sales_service import SalesService
from src.ui.theme import light_theme, dark_theme
from src.ui.router import ViewProvider
from src.utils.security import current_session

def main(page: ft.Page):
    """Función principal de la aplicación"""

    # --- Configuración de la página ---
    page.title = Config.APP_TITLE
    page.window_resizable = True
    page.window_min_width = 800
    page.window_min_height = 600
    
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = light_theme.text_theme
    page.dark_theme = dark_theme.text_theme
    page.padding = 0

    # --- Creación de instancias y DI ---
    # Verifica la conexión a la base de datos al instanciar DatabaseConnection.
    print("Verificando conexión a base de datos...")
    try:
        db_connection = DatabaseConnection(pool_name="app_main_pool")
        print("Conexión a base de datos exitosa.")
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        # Muestra un mensaje de error en la UI y detiene la carga si la conexión falla.
        page.add(ft.Column([
            ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED, size=64),
            ft.Text("Error Crítico de Conexión", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            ft.Text("No se pudo conectar a la base de datos. Verifique la configuración y reinicie la aplicación.", style=ft.TextThemeStyle.BODY_MEDIUM),
            ft.Text(f"Detalle: {e}", style=ft.TextThemeStyle.BODY_SMALL, color=ft.Colors.GREY_500),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True, spacing=10))
        page.update()
        return

    user_manager = UserManager(db_connection)
    sales_service = SalesService(db_connection)

    animated_switcher = ft.AnimatedSwitcher(
        content=ft.Container(),
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=300,
        reverse_duration=100,
        expand=True
    )
    
    view_provider = ViewProvider(page, user_manager, sales_service)

    # --- Lógica de Navegación Principal ---
    current_view_name = "login"

    def show_login():
        nonlocal current_view_name
        current_view_name = "login"
        animated_switcher.content = view_provider.build_login_view(on_login_success=show_main)
        page.update()

    def show_main():
        nonlocal current_view_name
        current_view_name = "main"
        animated_switcher.content = view_provider.build_main_view(on_navigate_to_sales=show_sales)
        page.update()

    def show_sales():
        nonlocal current_view_name
        current_view_name = "sales"
        animated_switcher.content = view_provider.build_sales_view(on_exit_sales=show_main)
        page.update()

    # --- Callbacks ---
    def open_logout_dialog(e):
        def confirm_logout(e_confirm):
            current_session.logout()
            page.close(dialog)
            show_login()
        
        def cancel_logout(e_cancel):
            page.close(dialog)

        is_light = page.theme_mode == ft.ThemeMode.LIGHT
        current_theme = light_theme if is_light else dark_theme
        confirm_text_color = ft.Colors.WHITE if is_light else ft.Colors.BLACK
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING_ROUNDED, color=current_theme.color_scheme.error),
                ft.Text("Cerrar Sesión", style=current_theme.text_theme.title_large)
            ], spacing=10, alignment=ft.MainAxisAlignment.START),
            content=ft.Text("¿Está seguro que desea cerrar la sesión?", style=current_theme.text_theme.body_medium),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel_logout, style=ft.ButtonStyle(color=current_theme.color_scheme.on_surface)),
                ft.ElevatedButton("Cerrar Sesión", on_click=confirm_logout, bgcolor=current_theme.color_scheme.error, color=confirm_text_color)
            ],
            bgcolor=current_theme.color_scheme.surface,
            shape=ft.RoundedRectangleBorder(radius=10),
        )
        page.open(dialog)

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        page.theme = light_theme.text_theme if page.theme_mode == ft.ThemeMode.LIGHT else dark_theme.text_theme
        
        # Re-render the current view with the new theme
        view_provider.update_theme()
        if current_view_name == "login":
            show_login()
        elif current_view_name == "main":
            show_main()
        elif current_view_name == "sales":
            show_sales()
        else:
            page.update()

    view_provider.toggle_theme_callback = toggle_theme
    view_provider.open_logout_dialog_callback = open_logout_dialog
    
    # --- Lógica de inicialización ---
    def window_event_handler(e):
        if e.data == "close":
            print("Evento de cierre recibido. (IGNORADO TEMPORALMENTE)")
            # try:
            #     db_connection.close()
            # except:
            #     pass
            # page.window.destroy()

    page.window.on_event = window_event_handler
    page.window.prevent_close = True

    page.add(animated_switcher)
    
    print("Mostrando login...")
    try:
        show_login()
        print("Login mostrado.")
    except Exception as e:
        print(f"Error al mostrar login: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Iniciando main...")
    try:
        ft.app(target=main)
    except Exception as e:
        print(f"Error fatal en ft.app: {e}")
        import traceback
        traceback.print_exc()
