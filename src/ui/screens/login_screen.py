import flet as ft
from src.config.settings import Config
from src.services.user_service import UserManager
from src.utils.security import current_session
from src.ui.theme import AppTheme

class LoginScreen:
    """Pantalla de autenticación del sistema, compatible con reconstrucción."""
    
    def __init__(self, page: ft.Page, user_manager: UserManager, toggle_theme_callback, router, theme: AppTheme):
        self.page = page
        self.user_manager = user_manager
        self.toggle_theme = toggle_theme_callback
        self.router = router
        self.theme = theme
        self._create_controls()

    def _create_controls(self):
        """Crea los controles de la pantalla de login usando el tema."""
        # Logo for the left side
        self.logo = ft.Image(src="src/assets/logoweb.webp", width=400, fit=ft.ImageFit.CONTAIN)
        
        # Form elements for the right side
        self.form_title = ft.Text("Bienvenido", style=self.theme.text_theme.headline_large, color=self.theme.color_scheme.primary)
        self.subtitle = ft.Text("Ingresa tus credenciales para continuar", style=self.theme.text_theme.body_medium)
        
        self.username_field = ft.TextField(label="Usuario", prefix_icon=ft.Icons.PERSON, width=350, autofocus=True, on_submit=self.on_login_click)
        self.password_field = ft.TextField(label="Contraseña", prefix_icon=ft.Icons.LOCK, password=True, can_reveal_password=True, width=350, on_submit=self.on_login_click)
        
        self.login_button = ft.ElevatedButton(
            text="Iniciar Sesión", 
            width=350, 
            height=50, 
            on_click=self.on_login_click, 
            style=ft.ButtonStyle(
                bgcolor=self.theme.color_scheme.primary, 
                color=self.theme.color_scheme.on_primary,
                shape=ft.RoundedRectangleBorder(radius=10)
            )
        )
        self.exit_button = ft.TextButton("Salir del Sistema", width=350, on_click=self.on_exit_click)
        self.error_message = ft.Text("", color=self.theme.color_scheme.error, text_align=ft.TextAlign.CENTER, visible=False)
        self.progress = ft.ProgressRing(visible=False)
        self.theme_button = ft.IconButton(icon=ft.Icons.LIGHT_MODE if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.DARK_MODE, tooltip="Alternar tema", on_click=self.toggle_theme)

    def build(self):
        """Construye y retorna el layout de la pantalla de login."""
        
        # Left Side: Branding
        left_side = ft.Container(
            content=ft.Column(
                controls=[
                    self.logo,
                    ft.Text("POS CINEMA", style=ft.TextStyle(size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                    ft.Text("Gestión Integral de Cines", style=ft.TextStyle(size=18, color=ft.Colors.WHITE70))
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[
                    self.theme.palette["primary"],
                    self.theme.palette["primary_container"]
                ]
            )
        )

        # Right Side: Login Form
        login_form = ft.Column(
            controls=[
                self.form_title, 
                self.subtitle, 
                ft.Container(height=30), 
                self.username_field, 
                self.password_field, 
                ft.Container(height=10), 
                self.error_message, 
                self.progress, 
                ft.Container(height=20), 
                self.login_button, 
                self.exit_button
            ],
            spacing=10, 
            width=400, 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        )

        right_side = ft.Container(
            content=ft.Stack(
                controls=[
                    ft.Container(content=login_form, alignment=ft.alignment.center),
                    ft.Container(content=self.theme_button, top=20, right=20),
                    ft.Container(content=ft.Text(f"v{Config.APP_VERSION}", color=self.theme.color_scheme.outline), bottom=20, right=20)
                ]
            ),
            expand=True,
            bgcolor=self.theme.color_scheme.surface
        )

        return ft.Row(
            controls=[left_side, right_side],
            spacing=0,
            expand=True
        )
    
    def on_login_click(self, e):
        self.attempt_login()
    
    def attempt_login(self):
        username = self.username_field.value.strip()
        password = self.password_field.value
        
        if not username or not password:
            self.show_error("Usuario y contraseña son requeridos")
            return
        
        self.show_progress(True)
        self.hide_error()
        
        user_data = self.user_manager.authenticate_user(username, password)
        
        self.show_progress(False)
        
        if user_data:
            current_session.login(user_data["id"], user_data["username"], user_data["role"])
            self.router.navigate("/main")
        else:
            self.show_error("Usuario o contraseña incorrectos")
            self.password_field.value = ""
            self.username_field.focus()
    
    def show_error(self, message: str):
        self.error_message.value = message
        self.error_message.visible = True
        self.page.update()
    
    def hide_error(self):
        self.error_message.visible = False
        self.page.update()
    
    def show_progress(self, show: bool):
        self.progress.visible = show
        self.login_button.disabled = show
        self.page.update()
    
    def on_exit_click(self, e):
        self.page.window.close()