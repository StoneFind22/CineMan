import flet as ft


LIGHT_PALETTE = {
    "primary": "#3f51b5",
    "primary_container": "#c5cae9",
    "on_primary": "#ffffff",
    "background": "#fdfcff",
    "surface": "#fdfcff",
    "on_surface": "#1b1b1f",
    "outline": "#757579",
    "error": "#b3261e"
}

DARK_PALETTE = {
    "primary": "#b0c4ff",
    "primary_container": "#283a9e",
    "on_primary": "#0e2083",
    "background": "#1b1b1f",
    "surface": "#1b1b1f",
    "on_surface": "#e3e2e6",
    "outline": "#8f8f93",
    "error": "#f2b8b5"
}

def create_themed_text_style(color: str, size: float, weight: ft.FontWeight):
    """Helper para crear un TextStyle consistente."""
    return ft.TextStyle(size=size, weight=weight, color=color)

class AppTheme:
    """
    Define un tema de aplicación completo, incluyendo ColorScheme y TextTheme.
    """
    def __init__(self, palette: dict):
        self.palette = palette
        self.color_scheme = self._create_color_scheme()
        self.text_theme = self._create_text_theme()

    def _create_color_scheme(self):
        return ft.ColorScheme(
            primary=self.palette["primary"],
            primary_container=self.palette["primary_container"],
            on_primary=self.palette["on_primary"],
            background=self.palette["background"],
            surface=self.palette["surface"],
            on_surface=self.palette["on_surface"],
            outline=self.palette["outline"],
            error=self.palette["error"],
        )

    def _create_text_theme(self):
        return ft.TextTheme(

            display_large=create_themed_text_style(self.palette["on_surface"], 57, ft.FontWeight.W_400),
            display_medium=create_themed_text_style(self.palette["on_surface"], 45, ft.FontWeight.W_400),
            display_small=create_themed_text_style(self.palette["on_surface"], 36, ft.FontWeight.W_400),
            
            headline_large=create_themed_text_style(self.palette["on_surface"], 32, ft.FontWeight.BOLD),
            headline_medium=create_themed_text_style(self.palette["on_surface"], 28, ft.FontWeight.BOLD),
            headline_small=create_themed_text_style(self.palette["on_surface"], 24, ft.FontWeight.BOLD),
            
            title_large=create_themed_text_style(self.palette["on_surface"], 22, ft.FontWeight.W_500),
            title_medium=create_themed_text_style(self.palette["on_surface"], 16, ft.FontWeight.W_500),
            title_small=create_themed_text_style(self.palette["on_surface"], 14, ft.FontWeight.W_500),

            label_large=create_themed_text_style(self.palette["primary"], 14, ft.FontWeight.W_500),
            label_medium=create_themed_text_style(self.palette["primary"], 12, ft.FontWeight.W_500),
            label_small=create_themed_text_style(self.palette["primary"], 11, ft.FontWeight.W_500),
            
            body_large=create_themed_text_style(self.palette["on_surface"], 16, ft.FontWeight.NORMAL),
            body_medium=create_themed_text_style(self.palette["on_surface"], 14, ft.FontWeight.NORMAL),
            body_small=create_themed_text_style(self.palette["on_surface"], 12, ft.FontWeight.NORMAL),
        )


light_theme = AppTheme(LIGHT_PALETTE)
dark_theme = AppTheme(DARK_PALETTE)