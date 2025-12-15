import flet as ft
from src.utils.security import current_session
from src.services.user_service import UserManager
from src.ui.theme import AppTheme

class ChangePasswordDialog:
    """Diálogo para cambiar contraseña del usuario actual."""
    
    def __init__(self, page: ft.Page, user_manager: UserManager, theme: AppTheme):
        self.page = page
        self.user_manager = user_manager
        self.theme = theme
        self.dialog = None
        self._create_dialog()

    def _create_dialog(self):
        """Crea el diálogo de cambio de contraseña usando el tema."""

        def themed_textfield(label, is_password=True):
            return ft.TextField(
                label=label,
                password=is_password,
                width=300,
                border_color=self.theme.color_scheme.outline,
                focused_border_color=self.theme.color_scheme.primary,
                label_style=ft.TextStyle(color=self.theme.color_scheme.on_surface),
                text_style=ft.TextStyle(color=self.theme.color_scheme.on_surface)
            )

        self.current_password = themed_textfield("Contraseña actual")
        self.current_password.autofocus = True
        
        self.new_password = themed_textfield("Nueva contraseña")
        
        self.confirm_password = themed_textfield("Confirmar nueva contraseña")
        
        self.error_text = ft.Text("", color=self.theme.color_scheme.error, visible=False)
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cambiar Contraseña", style=self.theme.text_theme.title_large),
            content=ft.Container(
                content=ft.Column(
                    [self.current_password, self.new_password, self.confirm_password, self.error_text],
                    tight=True
                ),
                width=300,
                height=210
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close_dialog),
                ft.ElevatedButton("Cambiar", on_click=self.change_password)
            ],
            bgcolor=self.theme.color_scheme.surface,
        )
    
    def show(self):
        """Muestra el diálogo."""
        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()
    
    def close_dialog(self, e):
        """Cierra el diálogo."""
        self.dialog.open = False
        self.page.update()
    
    def change_password(self, e):
        """Procesa el cambio de contraseña."""
        current = self.current_password.value
        new_pass = self.new_password.value
        confirm = self.confirm_password.value
        
        if not current or not new_pass or not confirm:
            self.show_error("Todos los campos son requeridos")
            return
        
        if new_pass != confirm:
            self.show_error("Las contraseñas no coinciden")
            return
        
        if len(new_pass) < 6:
            self.show_error("La contraseña debe tener al menos 6 caracteres")
            return
        
        success = self.user_manager.change_password(
            current_session.user_id,
            current,
            new_pass
        )
        
        if success:
            self.close_dialog(None)
        else:
            self.show_error("Contraseña actual incorrecta")
    
    def show_error(self, message: str):
        """Muestra mensaje de error."""
        self.error_text.value = message
        self.error_text.visible = True
        self.page.update()


# --- Funciones de Diálogo Genéricas ---

def close_dialog_helper(page: ft.Page, dialog: ft.AlertDialog):
    """Función auxiliar para cerrar un diálogo."""
    dialog.open = False
    page.update()

def show_info_dialog(page: ft.Page, title: str, content: str):
    """
    Muestra un diálogo de información simple.
    """
    info_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(content),
        actions=[
            ft.TextButton("OK", on_click=lambda e: close_dialog_helper(page, info_dialog)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.dialog = info_dialog
    info_dialog.open = True
    page.update()

def show_confirm_dialog(page: ft.Page, title: str, content: str, on_confirm: callable):
    """
    Muestra un diálogo de confirmación con acciones.
    """
    def on_confirm_wrapper(e):
        close_dialog_helper(page, confirm_dialog)
        on_confirm(e)

    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(content),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: close_dialog_helper(page, confirm_dialog)),
            ft.ElevatedButton("Confirmar", on_click=on_confirm_wrapper),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.dialog = confirm_dialog
    confirm_dialog.open = True
    page.update()