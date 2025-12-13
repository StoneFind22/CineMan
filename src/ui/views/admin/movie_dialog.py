import flet as ft
from src.models.models import Movie, MovieStatus
from src.ui.theme import AppTheme
from src.services.movie_service import MovieService

class MovieDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page, theme: AppTheme, movie_service: MovieService, on_save, movie: Movie = None):
        self.page = page
        self.theme = theme
        self.movie_service = movie_service
        self.on_save = on_save
        self.movie = movie or Movie()
        self.is_edit = movie is not None

        # Fetch all existing tags for the autocomplete
        self.all_tags = self.movie_service.get_all_tags()
        
        super().__init__(
            modal=True,
            title=ft.Text("Editar Película" if self.is_edit else "Nueva Película"),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close),
                ft.ElevatedButton("Guardar", on_click=self._save)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.content = self._build_form()

    def _build_form(self):
        self.title_field = ft.TextField(label="Título", value=self.movie.title, expand=True)
        self.original_title_field = ft.TextField(label="Título Original", value=self.movie.original_title, expand=True)
        
        self.duration_field = ft.TextField(label="Duración (min)", value=str(self.movie.duration_minutes), width=150, keyboard_type=ft.KeyboardType.NUMBER)
        self.rating_field = ft.Dropdown(
            label="Clasificación", value=self.movie.rating,
            options=[ft.dropdown.Option(r) for r in ["AA", "A", "B", "B15", "C", "D"]], width=150
        )
        
        self.genre_field = ft.TextField(label="Género", value=self.movie.genre, expand=True)
        self.status_dropdown = ft.Dropdown(
            label="Estado", value=self.movie.status,
            options=[ft.dropdown.Option(s.value) for s in MovieStatus], width=150
        )
        
        self.synopsis_field = ft.TextField(label="Sinopsis", value=self.movie.synopsis, multiline=True, min_lines=3, max_lines=5)
        self.poster_url_field = ft.TextField(label="URL Poster", value=self.movie.poster_url, prefix_icon=ft.Icons.IMAGE)
        self.trailer_url_field = ft.TextField(label="URL Trailer", value=self.movie.trailer_url, prefix_icon=ft.Icons.VIDEO_LIBRARY)
        
        self.selected_tags_row = ft.Row(wrap=True, spacing=5)
        self._update_tag_chips(self.movie.tags)

        self.tag_input = ft.TextField(
            label="Añadir etiqueta",
            expand=True,
            on_submit=self._add_tag_from_input,
            on_change=self._filter_suggestions
        )
        
        self.suggestions_list = ft.ListView(expand=False, spacing=0, visible=False, height=150)
        self.tags_container = ft.Column(
            controls=[
                self.tag_input,
                self.suggestions_list
            ]
        )

        tags_ui = ft.Column(
            controls=[
                ft.Text("Etiquetas", weight=ft.FontWeight.BOLD),
                self.selected_tags_row,
                self.tags_container
            ]
        )

        return ft.Container(
            width=600,
            content=ft.Column(
                controls=[
                    ft.Row([self.title_field, self.original_title_field]),
                    ft.Row([self.duration_field, self.rating_field, self.status_dropdown]),
                    self.genre_field,
                    self.synopsis_field,
                    self.poster_url_field,
                    self.trailer_url_field,
                    ft.Divider(),
                    tags_ui
                ],
                spacing=15,
                scroll=ft.ScrollMode.ADAPTIVE,
                height=500 # Set a fixed height to make the column scrollable
            )
        )

    def _add_tag_from_input(self, e: ft.ControlEvent):
        """Adds a tag when the user presses Enter in the text field."""
        self._add_tag_chip(e.control.value)
        e.control.value = ""
        self.suggestions_list.controls.clear()
        self.suggestions_list.visible = False
        self.page.update()

    def _add_tag_from_suggestion_click(self, e: ft.ControlEvent):
        """Adds a tag when the user clicks a suggestion tile."""
        self._add_tag_chip(e.control.data)
        self.tag_input.value = ""
        self.suggestions_list.controls.clear()
        self.suggestions_list.visible = False
        self.page.update()

    def _add_tag_chip(self, tag_name: str, update: bool = True):
        """Adds a tag to the UI if it's not empty or already added."""
        tag_name = tag_name.strip()
        if not tag_name:
            return

        current_tags = [chip.data for chip in self.selected_tags_row.controls]
        if tag_name.lower() in [t.lower() for t in current_tags]:
            return

        chip = ft.Chip(
            label=ft.Text(tag_name),
            on_delete=self._remove_tag_chip,
            data=tag_name,
        )
        self.selected_tags_row.controls.append(chip)
        if update:
            self.selected_tags_row.update()

    def _remove_tag_chip(self, e: ft.ControlEvent):
        """Removes a tag chip from the UI."""
        self.selected_tags_row.controls.remove(e.control)
        self.selected_tags_row.update()

    def _update_tag_chips(self, tags: list[str]):
        """Populates the chip row from a list of tag names without updating the control."""
        self.selected_tags_row.controls.clear()
        for tag_name in tags:
            self._add_tag_chip(tag_name, update=False)
    
    def _filter_suggestions(self, e: ft.ControlEvent):
        """Filters existing tags and populates a custom suggestion list."""
        value = e.control.value.lower()
        if not value:
            self.suggestions_list.visible = False
        else:
            suggestions = [
                tag for tag in self.all_tags if value in tag.lower()
            ]
            self.suggestions_list.controls = [
                ft.ListTile(
                    title=ft.Text(s), 
                    data=s, 
                    on_click=self._add_tag_from_suggestion_click,
                    height=40
                ) for s in suggestions
            ]
            self.suggestions_list.visible = bool(suggestions)
        self.page.update()

    def _save(self, e):
        if not self.title_field.value:
            self.title_field.error_text = "Requerido"
            self.title_field.update()
            return

        try:
            duration = int(self.duration_field.value)
        except (ValueError, TypeError):
            self.duration_field.error_text = "Debe ser número"
            self.duration_field.update()
            return

        self.movie.title = self.title_field.value
        self.movie.original_title = self.original_title_field.value
        self.movie.duration_minutes = duration
        self.movie.rating = self.rating_field.value
        self.movie.genre = self.genre_field.value
        self.movie.status = self.status_dropdown.value
        self.movie.synopsis = self.synopsis_field.value
        self.movie.poster_url = self.poster_url_field.value
        self.movie.trailer_url = self.trailer_url_field.value
        
        self.movie.tags = [chip.data for chip in self.selected_tags_row.controls]

        self.on_save(self.movie)
        self.close(None)

    def close(self, e):
        self.page.close(self)
