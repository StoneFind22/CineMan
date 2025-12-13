import flet as ft
from typing import Callable, Dict, Any

class ProductCard(ft.Card):
    """
    Una tarjeta interactiva para un producto de confitería, que maneja
    su propia cantidad y notifica los cambios.
    """
    def __init__(
        self,
        product: Dict[str, Any],
        on_quantity_change: Callable[[Dict[str, Any], int], None],
        theme,
    ):
        super().__init__()
        self.product = product
        self.on_quantity_change = on_quantity_change
        self.theme = theme
        self.quantity = 0

        self.quantity_text = ft.Text(str(self.quantity), size=16, weight=ft.FontWeight.BOLD)
        
        self.content = self._build_content()

    def _build_content(self) -> ft.Container:
        """Construye el contenido de la tarjeta del producto."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Image(
                        src=self.product.get("image_url", "https://via.placeholder.com/150x150.png?text=No+Image"),
                        height=80,
                        fit=ft.ImageFit.COVER,
                        border_radius=ft.border_radius.only(top_left=10, top_right=10)
                    ),
                    ft.Container(
                        content=ft.Text(self.product["name"], weight=ft.FontWeight.BOLD, size=14, text_align=ft.TextAlign.CENTER, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        height=50,
                        alignment=ft.alignment.center
                    ),
                    ft.Text(f"S/ {self.product['price']:.2f}", size=14),
                    ft.Row(
                        [
                            ft.IconButton(icon=ft.Icons.REMOVE, on_click=self._decrease_quantity, bgcolor=self.theme.color_scheme.surface_variant),
                            self.quantity_text,
                            ft.IconButton(icon=ft.Icons.ADD, on_click=self._increase_quantity, bgcolor=self.theme.color_scheme.surface_variant),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            border_radius=ft.border_radius.all(10),
        )

    def _decrease_quantity(self, e):
        """Disminuye la cantidad del producto."""
        if self.quantity > 0:
            self.quantity -= 1
            self.quantity_text.value = str(self.quantity)
            self.on_quantity_change(self.product, self.quantity)

    def _increase_quantity(self, e):
        """Aumenta la cantidad del producto."""
        # En un sistema real, se verificaría el stock (self.product['stock'])
        self.quantity += 1
        self.quantity_text.value = str(self.quantity)
        self.on_quantity_change(self.product, self.quantity)
