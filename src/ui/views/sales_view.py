import flet as ft
from typing import Callable, List, Dict, Any
from src.models.transaction import Transaction, Ticket, Seat, ConcessionItem
from src.services.sales_service import SalesService
from src.ui.components.seat_map import SeatMap
from src.ui.components.product_card import ProductCard
from src.utils.security import current_session

class SalesView(ft.Container):
    """
    Vista de pantalla completa para el proceso de ventas, con un layout de 
    contenido principal y un panel de resumen de orden.
    """
    def __init__(self, on_exit_sale_mode: Callable[[], None], theme, sales_service: SalesService):
        super().__init__()
        self.on_exit_sale_mode = on_exit_sale_mode
        self.theme = theme
        self.sales_service = sales_service
        
        self.transaction = Transaction()
        self.movies: List[Dict[str, Any]] = []
        self.current_ticket_prices: Dict[str, float] = {}
        self.selected_movie: Dict[str, Any] | None = None
        self.selected_showtime: Dict[str, Any] | None = None
        self.selected_ticket_type: str = "Adulto"
        
        self._build_ui_components()
        self.content_area = self._build_content_area()
        self.summary_panel = self._build_summary_panel()
        
        self.expand = True
        self.padding = 0
        self.content = ft.Row(
            controls=[self.content_area, self.summary_panel],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START, 
        )
        
    def did_mount(self):
        """Called after the control is added to the page."""
        self._update_summary_panel()
        self._load_movies()

    def _build_ui_components(self):
        """Initializes UI components that need to be referenced later."""
        self.order_items_list = ft.Column(spacing=10)
        self.subtotal_text = ft.Text("S/ 0.00")
        self.tax_text = ft.Text("S/ 0.00")
        self.total_text = ft.Text("S/ 0.00", weight=ft.FontWeight.BOLD, style=self.theme.text_theme.title_large)
        self.pay_button = ft.ElevatedButton("Pagar", icon=ft.Icons.PAYMENT, height=60, on_click=lambda e: self._show_payment_step(), style=ft.ButtonStyle(bgcolor=self.theme.color_scheme.primary, color=self.theme.color_scheme.on_primary, shape=ft.RoundedRectangleBorder(radius=10)))
        self.movie_grid = ft.GridView(expand=True, max_extent=200, child_aspect_ratio=0.7, spacing=20, run_spacing=20)
        self.concessions_grid = ft.GridView(expand=True, max_extent=180, child_aspect_ratio=1.0, spacing=20, run_spacing=20)
        self.loading_indicator = ft.ProgressRing(width=50, height=50)
        self.continue_button = ft.ElevatedButton("Continuar a Confitería", icon=ft.Icons.FASTFOOD, height=50, on_click=lambda e: self._show_confectionery_step())

    def _build_content_area(self) -> ft.Container:
        """Construye el área de contenido principal donde ocurrirán los pasos de la venta."""
        return ft.Container(
            content=ft.Stack([
                ft.Column([
                    ft.Text("Paso 1: Selección de Película", style=self.theme.text_theme.headline_medium),
                    ft.Divider(),
                    self.movie_grid,
                ], expand=True),
                self.loading_indicator,
            ], expand=True),
            expand=True, padding=30, bgcolor=self.theme.color_scheme.surface_variant,
        )

    def _build_summary_panel(self) -> ft.Container:
        """Construye el panel lateral para el resumen de la orden."""
        exit_button = ft.TextButton("Salir de Ventas", icon=ft.Icons.CLOSE, on_click=lambda e: self.on_exit_sale_mode(), style=ft.ButtonStyle(color=self.theme.color_scheme.on_surface))
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Text("Resumen de Orden", style=self.theme.text_theme.title_large), ft.Container(expand=True), exit_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Container(content=self.order_items_list, expand=True, padding=ft.padding.symmetric(vertical=10)),
                ft.Column([
                    ft.Divider(),
                    ft.Row([ft.Text("Subtotal"), self.subtotal_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("IGV (18%)"), self.tax_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    ft.Row([ft.Text("TOTAL", style=self.theme.text_theme.title_large, weight=ft.FontWeight.BOLD), self.total_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=10),
                    self.pay_button
                ], spacing=8)
            ], spacing=10),
            width=400, padding=20, bgcolor=self.theme.color_scheme.surface,
            border=ft.border.only(left=ft.BorderSide(1, self.theme.color_scheme.outline_variant))
        )
    
    def _load_movies(self):
        """Obtiene las películas del servicio y actualiza la UI."""
        self.loading_indicator.visible = True
        self.movie_grid.controls.clear()
        self.update()
        
        self.movies = self.sales_service.get_active_movies_with_showtimes()
        
        self.loading_indicator.visible = False
        if not self.movies:
            self.movie_grid.controls.append(ft.Text("No hay funciones disponibles para hoy."))
        else:
            for movie in self.movies:
                self.movie_grid.controls.append(self._build_movie_card(movie))
        self.update()
        
    def _build_movie_card(self, movie: Dict[str, Any]) -> ft.Control:
        return ft.Card(content=ft.Container(
            content=ft.Column([
                ft.Image(src=movie.get("poster_url", "https://via.placeholder.com/200x300.png?text=No+Image"), fit=ft.ImageFit.COVER, expand=True),
                ft.Container(content=ft.Text(movie["title"], weight=ft.FontWeight.BOLD, size=14, no_wrap=True), padding=10)
            ], spacing=0, alignment=ft.MainAxisAlignment.START),
            border_radius=ft.border_radius.all(10), clip_behavior=ft.ClipBehavior.HARD_EDGE, on_click=lambda e: self._on_movie_selected(movie),
        ))

    def _on_movie_selected(self, movie: Dict[str, Any]):
        self.selected_movie = movie
        self.content_area.content = ft.Column(
            controls=[
                ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self._show_movie_grid()),
                ft.Text(f"Horarios para {movie['title']}", style=self.theme.text_theme.headline_small),
                ft.Divider()
            ] + [ft.ElevatedButton(f"{st['show_time']} - Sala {st['room_name']} ({st['format']})", on_click=lambda e, st=st: self._show_seat_map(st)) for st in movie["showtimes"]],
            spacing=10
        )
        self.update()

    def _show_movie_grid(self):
        self.selected_movie = None
        self.content_area.content = ft.Column([
            ft.Text("Paso 1: Selección de Película", style=self.theme.text_theme.headline_medium),
            ft.Divider(),
            self.movie_grid
        ], expand=True)
        self.update()
    
    def _show_seat_map(self, showtime: Dict[str, Any]):
        self.selected_showtime = showtime
        self.content_area.content = ft.Stack([self.loading_indicator], expand=True)
        self.update()
        
        # Obtener precios dinámicos y mapa de asientos en paralelo
        self.current_ticket_prices = self.sales_service.get_ticket_prices_for_showtime(showtime["showtime_id"])
        seat_data = self.sales_service.get_seat_map(showtime["showtime_id"])
        
        if not seat_data.get("seats"):
            self.content_area.content = ft.Column([
                ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self._on_movie_selected(self.selected_movie)),
                ft.Text("Error", style=self.theme.text_theme.headline_small),
                ft.Text("No se pudo cargar la información de los asientos para esta función.")
            ])
        else:
            # Crear segmentos basados en los precios obtenidos
            price_segments = []
            for ticket_type, price in self.current_ticket_prices.items():
                # El ícono se puede mapear o dejar genérico
                icon = ft.icons.PERSON
                if ticket_type == "Niño":
                    icon = ft.icons.CHILD_CARE
                elif ticket_type == "3ra Edad":
                    icon = ft.icons.ELDERLY
                price_segments.append(ft.Segment(value=ticket_type, label=ft.Text(f"{ticket_type} (S/ {price:.2f})"), icon=ft.Icon(icon)))

            ticket_type_selector = ft.SegmentedButton(
                on_change=self._on_ticket_type_changed, selected={self.selected_ticket_type},
                segments=price_segments
            )
            seat_map_component = SeatMap(seat_data, self._on_seat_selected, self.theme)
            self.content_area.content = ft.Column([
                ft.Row([
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self._on_movie_selected(self.selected_movie)),
                    ft.Text(f"Paso 2: Selección de Asientos", style=self.theme.text_theme.headline_medium)
                ]),
                ft.Divider(),
                ft.Row([ft.Text("Seleccione el tipo de entrada:"), ticket_type_selector], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                seat_map_component,
                ft.Row([self.continue_button], alignment=ft.MainAxisAlignment.END)
            ], expand=True)
        self.update()

    def _on_ticket_type_changed(self, e: ft.ControlEvent):
        self.selected_ticket_type = e.data
        self.update()

    def _on_seat_selected(self, seat_info: Dict[str, Any], is_selected: bool):
        if is_selected:
            self.transaction.add_ticket(Ticket(
                movie_title=self.selected_movie["title"],
                showtime=self.selected_showtime["show_time"],
                showtime_id=self.selected_showtime["showtime_id"],
                seat=Seat(row=seat_info['seat_row'], number=seat_info['seat_col'], seat_id=seat_info['seat_id']),
                ticket_type=self.selected_ticket_type,
                price=self.current_ticket_prices.get(self.selected_ticket_type, 0.0)
            ))
        else:
            self.transaction.remove_ticket_by_seat(seat_info['seat_id'])
        self._update_summary_panel()

    def _show_confectionery_step(self):
        self.content_area.content = ft.Stack([self.loading_indicator], expand=True)
        self.update()

        products = self.sales_service.get_concession_products()
        self.concessions_grid.controls.clear()

        if not products:
            self.concessions_grid.controls.append(ft.Text("No hay productos de confitería disponibles."))
        else:
            for product in products:
                self.concessions_grid.controls.append(
                    ProductCard(product, self._on_concession_change, self.theme)
                )
        
        self.content_area.content = ft.Column([
            ft.Row([
                ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self._show_seat_map(self.selected_showtime)),
                ft.Text("Paso 3: Selección de Confitería", style=self.theme.text_theme.headline_medium),
            ]),
            ft.Divider(),
            self.concessions_grid
        ], expand=True)
        self.update()

    def _on_concession_change(self, product: Dict[str, Any], new_quantity: int):
        self.transaction.update_concession_quantity(product, new_quantity)
        self._update_summary_panel()

    def _show_payment_step(self):
        _, _, total = self.transaction.calculate_total()
        
        payment_buttons = ft.Row(
            [
                ft.ElevatedButton("Efectivo", icon=ft.Icons.MONEY, on_click=lambda e: self._process_sale("Efectivo"), height=60, expand=True),
                ft.ElevatedButton("Tarjeta", icon=ft.Icons.CREDIT_CARD, on_click=lambda e: self._process_sale("Tarjeta"), height=60, expand=True),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER
        )

        self.content_area.content = ft.Column([
            ft.Row([
                ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self._show_confectionery_step()),
                ft.Text("Paso 4: Pago Final", style=self.theme.text_theme.headline_medium),
            ]),
            ft.Divider(),
            ft.Container(height=20),
            ft.Text("Resumen Final del Pedido:", style=self.theme.text_theme.title_medium),
            ft.Container(
                content=self.order_items_list, # Re-use the same list view
                padding=20,
                border=ft.border.all(1, self.theme.color_scheme.outline_variant),
                border_radius=10
            ),
            ft.Container(height=20),
            ft.Row([
                ft.Text("TOTAL A PAGAR:", style=self.theme.text_theme.headline_small, weight=ft.FontWeight.BOLD),
                ft.Text(f"S/ {total:.2f}", style=self.theme.text_theme.headline_small, color=self.theme.color_scheme.primary, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=40),
            payment_buttons
        ])
        self.update()

    def _process_sale(self, payment_method: str):
        self.content_area.content = ft.Stack([self.loading_indicator], expand=True)
        self.loading_indicator.visible = True
        self.update()

        success = self.sales_service.save_transaction(self.transaction, current_session.user_id)
        
        self.loading_indicator.visible = False
        self.update()

        def close_dialog(e):
            self.page.close(dialog)
            if success:
                self.reset_sale()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Resultado de la Venta"),
            content=ft.Text("¡Venta completada exitosamente!" if success else "Error: No se pudo procesar la venta."),
            actions=[ft.TextButton("Aceptar", on_click=close_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dialog)

    def reset_sale(self):
        """Limpia y resetea la vista de ventas a su estado inicial."""
        self.transaction.clear()
        self.selected_movie = None
        self.selected_showtime = None
        self.selected_ticket_type = "Adulto"
        self.concessions_grid.controls.clear()
        
        self._show_movie_grid()
        self._update_summary_panel()

    def _update_summary_panel(self):
        """Refresca el panel de resumen basado en el estado actual de la transacción."""
        self.order_items_list.controls.clear()
        
        if self.transaction.is_empty():
            self.order_items_list.controls.append(ft.Text("El pedido está vacío", italic=True, color=self.theme.color_scheme.outline))
        else:
            ticket_summary = {}
            for ticket in self.transaction.tickets:
                key = (ticket.ticket_type, ticket.price)
                if key not in ticket_summary:
                    ticket_summary[key] = {"count": 0, "seats": []}
                ticket_summary[key]["count"] += 1
                ticket_summary[key]["seats"].append(f"{ticket.seat.row}{ticket.seat.number}")
            
            for (ticket_type, price), summary in ticket_summary.items():
                self.order_items_list.controls.append(ft.Row([
                    ft.Column([
                        ft.Text(f"{summary['count']}x {ticket_type}"),
                        ft.Text(f"Asientos: {', '.join(summary['seats'])}", size=12, color=self.theme.color_scheme.outline)
                    ]), ft.Text(f"S/ {summary['count'] * price:.2f}")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

            for item in self.transaction.concessions:
                 self.order_items_list.controls.append(ft.Row([
                    ft.Text(f"{item.quantity}x {item.name}"), ft.Text(f"S/ {item.total_price:.2f}")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

        base, taxes, total = self.transaction.calculate_total()
        
        self.subtotal_text.value = f"S/ {base:.2f}"
        self.tax_text.value = f"S/ {taxes:.2f}"
        self.total_text.value = f"S/ {total:.2f}"
        self.pay_button.disabled = self.transaction.is_empty()
        self.continue_button.disabled = not self.transaction.tickets
        
        self.update()