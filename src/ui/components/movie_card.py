import flet as ft
from typing import Callable
from src.models.models import Movie

class MovieCard(ft.Container):
    def __init__(
        self,
        movie: Movie,
        theme,
        on_edit: Callable[[], None],
        on_delete: Callable[[], None],
    ):
        super().__init__(on_hover=self._on_hover, border_radius=ft.border_radius.all(15))
        self.movie = movie
        self.theme = theme
        self.on_edit = on_edit
        self.on_delete = on_delete
        self._is_hovered = False
        
        self.inner_card = ft.Card(
            elevation=4,
            content=self._build_content()
        )
        self.content = self.inner_card

    def _on_hover(self, e: ft.HoverEvent):
        self._is_hovered = e.data == "true"
        self.overlay_container.opacity = 0.6 if self._is_hovered else 0
        self.overlay_container.content.visible = self._is_hovered
        self.inner_card.elevation = 12 if self._is_hovered else 4
        self.scale = ft.Scale(1.03) if self._is_hovered else ft.Scale(1)
        self.update()

    def _build_content(self):
        actions = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=ft.Colors.WHITE70,
                    tooltip="Eliminar",
                    on_click=lambda e: self.on_delete(),
                ),
                ft.ElevatedButton(
                    "Editar",
                    icon=ft.Icons.EDIT_OUTLINED,
                    on_click=lambda e: self.on_edit(),
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(horizontal=12),
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
            visible=False,
        )

        self.overlay_container = ft.Container(
            content=actions,
            alignment=ft.alignment.center,
            border_radius=ft.border_radius.only(top_left=15, top_right=15),
            bgcolor=ft.Colors.BLACK,
            opacity=0,
            animate_opacity=ft.Animation(200, "easeIn"),
        )
        
        status_color = ft.Colors.GREEN_400 if self.movie.status == "ACTIVE" else ft.Colors.GREY_400
        
        image_stack = ft.Stack(
            controls=[
                ft.Container(
                    content=ft.Image(
                        src=self.movie.poster_url if self.movie.poster_url else f"https://via.placeholder.com/300x450/222/fff?text={self.movie.title.replace(' ', '+')}",
                        fit=ft.ImageFit.COVER,
                        height=220,
                    ),
                    border_radius=ft.border_radius.only(top_left=15, top_right=15)
                ),
                self.overlay_container,
                ft.Container(
                    content=ft.Text(self.movie.status, size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor=status_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=ft.border_radius.only(top_left=15, bottom_right=10),
                )
            ]
        )
        
        info_column = ft.Column(
            spacing=5,
            controls=[
                ft.Text(self.movie.title, weight=ft.FontWeight.BOLD, size=15, no_wrap=True),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.SCHEDULE, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(f"{self.movie.duration_minutes} min", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Container(width=5),
                        ft.Icon(ft.Icons.STAR_BORDER, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(self.movie.rating, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                    ]
                ),
                ft.Row(
                    controls=[ft.Chip(label=ft.Text(tag, size=10)) for tag in self.movie.tags[:3]] if self.movie.tags else []
                )
            ]
        )

        return ft.Column(
            spacing=10,
            controls=[
                image_stack,
                ft.Container(info_column, padding=ft.padding.symmetric(horizontal=12)),
                ft.Container(height=5) # Spacer for bottom padding.
            ]
        )

