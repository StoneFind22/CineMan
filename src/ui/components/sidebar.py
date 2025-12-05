import flet as ft
from src.ui.theme import AppTheme
from src.utils.security import current_session

NAVIGATION_MAP = {
    "TRABAJADOR": [
        {"view_id": "sales", "title": "Ventas", "icon": ft.Icons.POINT_OF_SALE},
    ],
    "ADMINISTRADOR": [
        {"view_id": "sales", "title": "Ventas", "icon": ft.Icons.POINT_OF_SALE},
        {"view_id": "inventory", "title": "Inventario", "icon": ft.Icons.INVENTORY},
        {"view_id": "reports", "title": "Reportes", "icon": ft.Icons.BAR_CHART},
        {"view_id": "schedules", "title": "Horarios", "icon": ft.Icons.SCHEDULE},
    ],
    "GERENCIAL": [
        {"view_id": "users", "title": "Usuarios", "icon": ft.Icons.GROUP},
        {"view_id": "settings", "title": "Configuración", "icon": ft.Icons.SETTINGS},
    ],
}

class Sidebar(ft.Container):
    def __init__(self, main_screen, theme: AppTheme, expanded: bool = True):
        super().__init__()
        self.main_screen = main_screen
        self.theme = theme
        self.expanded = expanded
        
        # Build navigation items based on user role
        self.navigation_items = [
            {"view_id": "dashboard", "title": "Dashboard", "icon": ft.Icons.DASHBOARD}
        ]
        
        user_role = current_session.role
        role_permissions = NAVIGATION_MAP.get(user_role, [])
        
        self.navigation_items.extend(role_permissions)
        
        # Special case for GERENCIAL who can see all
        if user_role == "GERENCIAL":
            all_views = set(item['view_id'] for item in self.navigation_items)
            for role, items in NAVIGATION_MAP.items():
                if role != "GERENCIAL":
                    for item in items:
                        if item['view_id'] not in all_views:
                            self.navigation_items.append(item)
                            all_views.add(item['view_id'])
        
        self._configure()

    def _configure(self):
        if self.expanded:
            self.width = 250
            self.padding = 20
            self.content = self._build_expanded_content()
        else:
            self.width = 80
            self.padding = ft.padding.symmetric(vertical=20)
            self.content = self._build_compact_content()

        self.bgcolor = self.theme.color_scheme.surface
        self.border = ft.border.only(right=ft.BorderSide(1, self.theme.color_scheme.outline_variant))
        self.animate = ft.Animation(300, "ease")

    def _build_compact_content(self):
        """ aqui iran las nuevas opciones de navegacion compactas"""
        return ft.Column(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # zona superior
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Image(src="src/assets/logo.png", height=40, fit=ft.ImageFit.CONTAIN),
                    ]
                ),
                # zona media
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._build_compact_menu_item(item["view_id"], item["title"], item["icon"], self._navigate)
                        for item in self.navigation_items
                    ]
                ),
                # zona inferior
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._build_compact_menu_item("settings", "Settings", ft.Icons.SETTINGS, self._navigate),
                    ]
                )
            ]
        )

    def _build_expanded_content(self):
        """ aqui iran las nuevas opciones de navegacion expandidas"""
        return ft.Column(
            controls=[
                # Bloques de navegacion
                ft.Column(
                    controls=[
                        ft.Text("General", style=self.theme.text_theme.body_small, color=self.theme.color_scheme.outline),
                        *[self._build_expanded_menu_item(item["view_id"], item["title"], item["icon"], self._navigate) for item in self.navigation_items],
                    ],
                    spacing=10
                ),
                ft.Container(expand=True),
                self._build_user_card()
            ]
        )

    def _build_compact_menu_item(self, view_id: str, title: str, icon: str, on_click_action):
        is_selected = self.main_screen.current_view == view_id
        return ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=24, color=self.theme.color_scheme.primary if is_selected else self.theme.color_scheme.on_surface_variant),
                    ft.Text(title, size=9, text_align=ft.TextAlign.CENTER, color=self.theme.color_scheme.on_surface_variant, width=70, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
                ],
                spacing=5
            ),
            padding=ft.padding.all(10),
            border_radius=10,
            ink=True,
            on_click=lambda e, view_id=view_id: on_click_action(view_id),
            tooltip=title,
        )

    def _build_expanded_menu_item(self, view_id: str, title: str, icon: str, on_click_action):
        is_selected = self.main_screen.current_view == view_id
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=20, color=self.theme.color_scheme.primary if is_selected else self.theme.color_scheme.on_surface),
                    ft.Text(title, style=ft.TextStyle(
                        size=14,
                        weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.NORMAL,
                        color=self.theme.color_scheme.primary if is_selected else self.theme.color_scheme.on_surface
                    ))
                ],
                spacing=15
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            bgcolor=ft.Colors.with_opacity(0.1, self.theme.color_scheme.primary) if is_selected else ft.Colors.TRANSPARENT,
            border_radius=10,
            ink=True,
            on_click=lambda e, view_id=view_id: on_click_action(view_id)
        )

    def _build_user_card(self):
        return ft.Row(
            controls=[
                ft.CircleAvatar(content=ft.Icon(ft.Icons.PERSON), radius=20),
                ft.Column(
                    controls=[
                        ft.Text(current_session.username, weight=ft.FontWeight.BOLD),
                        ft.Text(current_session.role, size=12)
                    ],
                    spacing=0,
                )
            ]
        )
    
    def _navigate(self, view_id: str):
        self.main_screen.current_view = view_id
        self.main_screen._update_main_content()
        # actualiza el sidebar para reflejar la nueva seleccion
        self._configure()
        self.update()

    def toggle(self):
        self.expanded = not self.expanded
        self._configure()
        self.update()

    def update_theme(self, theme: AppTheme):
        """ actualiza el tema y redibuja el sidebar"""
        self.theme = theme
        self._configure()
        self.update()