import flet as ft
from typing import Optional
from src.ui.theme import AppTheme
from src.services.movie_service import MovieService
from src.database.connection import DatabaseConnection
from src.models.models import Movie, MovieStatus
from src.ui.views.admin.movie_dialog import MovieDialog
from src.ui.components.movie_card import MovieCard

class MoviesView(ft.Container):
    def __init__(self, page: ft.Page, theme: AppTheme):
        super().__init__(expand=True)
        self.page = page
        self.theme = theme
        self.db = DatabaseConnection()
        self.movie_service = MovieService(self.db)
        self.movies = []
        self.content = self._build_ui()
        self._load_movies()

    def build(self):
        return self

    def _build_ui(self):
        self.main_content = ft.Column(
            controls=[
                self._build_header(),
                self._build_toolbar(),
                self._build_movie_grid(),
            ],
            spacing=20,
            expand=True,
            visible=False
        )

        self.loader = ft.Container(
            content=ft.ProgressRing(width=48, height=48, stroke_width=4),
            alignment=ft.alignment.center,
            visible=True
        )

        return ft.Stack(
            controls=[
                self.main_content,
                self.loader
            ]
        )

    def _build_header(self):
        return ft.Row(
            controls=[
                ft.Icon(ft.Icons.MOVIE, size=32, color=self.theme.color_scheme.primary),
                ft.Text("Catálogo de Películas", style=self.theme.text_theme.headline_medium, color=self.theme.color_scheme.on_surface),
            ],
            alignment=ft.MainAxisAlignment.START
        )

    def _build_toolbar(self):
        self.status_filter = ft.Dropdown(
            hint_text="Filtrar por estado",
            value=MovieStatus.ACTIVE.value,
            options=[ft.dropdown.Option(s.value) for s in MovieStatus],
            width=200,
            border_radius=10,
            bgcolor=self.theme.color_scheme.surface_variant,
            on_change=self._filter_by_status,
        )
        return ft.Row(
            controls=[
                ft.Container(expand=True), # Pushes controls to the right
                ft.TextField(
                    hint_text="Buscar película...",
                    prefix_icon=ft.Icons.SEARCH,
                    width=250,
                    border_radius=10,
                    bgcolor=self.theme.color_scheme.surface_variant,
                    on_change=self._filter_movies
                ),
                self.status_filter,
                ft.ElevatedButton(
                    "Nueva Película",
                    icon=ft.Icons.ADD,
                    style=ft.ButtonStyle(
                        bgcolor=self.theme.color_scheme.primary,
                        color=self.theme.color_scheme.on_primary,
                    ),
                    on_click=self._open_movie_dialog
                )
            ],
            spacing=10
        )

    def _build_movie_grid(self):
        self.grid = ft.GridView(
            expand=True,
            runs_count=5,
            max_extent=220,
            child_aspect_ratio=0.85, # Adjusted for new card height
            spacing=15,
            run_spacing=15,
        )
        return self.grid

    def _load_movies(self, status: Optional[str] = MovieStatus.ACTIVE.value):
        if self.loader:
            self.loader.visible = True
            self.main_content.visible = False
            if self.page: self.page.update()

        self.movies = self.movie_service.get_all_movies(status=status)
        self._render_grid(self.movies)

        if self.loader:
            self.loader.visible = False
            self.main_content.visible = True
            if self.page: self.page.update()

    def _filter_by_status(self, e):
        status_to_filter = e.control.value
        self._load_movies(status=status_to_filter)

    def _render_grid(self, movies):
        self.grid.controls = [self._build_movie_card(m) for m in movies]
        if self.grid.page:
            self.grid.update()

    def _filter_movies(self, e):
        search_term = e.control.value.lower()
        filtered = [m for m in self.movies if search_term in m.title.lower()]
        self._render_grid(filtered)

    def _open_movie_dialog(self, e=None, movie: Movie = None): # 'e' can be None for direct calls
        def on_save(movie_data: Movie):
            if movie_data.id:
                success = self.movie_service.update_movie(movie_data)
                msg = "Película actualizada" if success else "Error al actualizar"
            else:
                new_id = self.movie_service.create_movie(movie_data)
                success = new_id is not None
                msg = "Película creada" if success else "Error al crear"
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(msg, color=ft.Colors.WHITE),
                bgcolor=self.theme.color_scheme.primary if success else self.theme.color_scheme.error
            )
            self.page.snack_bar.open = True
            
            if success:
                self._load_movies()
            
            self.page.update()

        dlg = MovieDialog(self.page, self.theme, self.movie_service, on_save, movie)
        self.page.open(dlg)

    def _build_movie_card(self, movie: Movie):
        return MovieCard(
            movie=movie,
            theme=self.theme,
            on_edit=lambda: self._open_movie_dialog(movie=movie),
            on_delete=lambda: self._show_delete_dialog(movie),
        )

    def _show_delete_dialog(self, movie: Movie):
        def delete_confirmed(e):
            self._delete_movie(movie, dlg)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Estás seguro de que quieres eliminar la película '{movie.title}'? Esta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton(
                    "Eliminar", 
                    on_click=delete_confirmed, 
                    style=ft.ButtonStyle(color=self.theme.color_scheme.error)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dlg)

    def _delete_movie(self, movie: Movie, dialog: ft.AlertDialog):
        self.page.close(dialog)
        success = self.movie_service.delete_movie(movie.id)
        
        msg = "Película eliminada con éxito" if success else "Error al eliminar la película"
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(msg, color=ft.Colors.WHITE),
            bgcolor=self.theme.color_scheme.primary if success else self.theme.color_scheme.error
        )
        self.page.snack_bar.open = True
        
        if success:
            self._load_movies()
        
        self.page.update()
