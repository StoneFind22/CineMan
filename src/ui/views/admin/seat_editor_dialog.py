import flet as ft
import logging
from src.models.models import Theater, Seat, SeatType, SeatStatus
from src.services.theater_service import TheaterService
from src.ui.theme import AppTheme

logger = logging.getLogger(__name__)

class SeatEditorDialog(ft.AlertDialog):
    """Diálogo modal para la edición visual del layout de asientos de una sala."""
    def __init__(self, page: ft.Page, theme: AppTheme, theater: Theater, theater_service: TheaterService, on_save):
        self.page = page
        self.theme = theme
        self.theater = theater
        self.theater_service = theater_service
        self.on_save = on_save
        
        self.seats_to_render: list[Seat] = []
        self.seat_types: list[SeatType] = []
        self.current_tool = "select"
        self.max_x = 0
        self.max_y = 0

        # Control para dar feedback de texto al usuario.
        self.status_bar = ft.Text(value="Selecciona una herramienta para empezar.", size=12, color=theme.color_scheme.outline)

        super().__init__(
            modal=True,
            title=ft.Text(f"Editor de Layout: {theater.name}"),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close),
                ft.ElevatedButton("Guardar Layout", on_click=self._save_layout)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        
        self._load_initial_data()
        self.content = self._build_editor_content()

    def _load_initial_data(self):
        """Carga los asientos y tipos de asiento existentes para inicializar el editor."""
        self.seats_to_render = self.theater_service.get_theater_seats(self.theater.id)
        self.seat_types = self.theater_service.get_all_seat_types()
        
        if self.seats_to_render:
            self.max_x = max((s.x_position for s in self.seats_to_render), default=0)
            self.max_y = max((s.y_position for s in self.seats_to_render), default=0)
        else: 
            self.max_x = 15
            self.max_y = 10
            
    def _build_editor_content(self):
        """Construye el layout principal del editor: barra de herramientas y parrilla de asientos."""
        self.seat_grid = self._build_seat_grid()
        self.toolbar = self._build_toolbar()
        
        grid_container = ft.Container(
            content=self.seat_grid,
            width=800,
            height=450, # Altura ajustada para dar espacio a la leyenda.
            border=ft.border.all(1, self.theme.color_scheme.outline),
            border_radius=10,
            padding=20,
            alignment=ft.alignment.center,
        )

        # Columna principal que contiene la parrilla, la leyenda y la barra de estado.
        main_editor_column = ft.Column([
            grid_container,
            ft.Divider(height=10),
            self._build_legend(),
            self.status_bar
        ], spacing=10)

        return ft.Row(
            controls=[self.toolbar, main_editor_column],
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=20
        )

    def _build_legend(self):
        """Construye la leyenda de colores para los tipos de asiento."""
        
        def legend_item(color, label):
            return ft.Row([ft.Container(width=20, height=20, bgcolor=color, border_radius=4), ft.Text(label, size=12)])

        items = []
        for st in self.seat_types:
            color = self.theme.color_scheme.primary
            if "VIP" in st.name: color = ft.Colors.AMBER
            elif "Discapacitados" in st.name: color = ft.Colors.LIGHT_BLUE_500
            items.append(legend_item(color, st.name))
        
        items.append(legend_item("rgba(0,0,0,0.4)", "Bloqueado"))
        items.append(legend_item(ft.Colors.GREY_300, "Pasillo"))
        
        return ft.Row(items, spacing=15, alignment=ft.MainAxisAlignment.CENTER)


    def _build_toolbar(self):
        """Construye la barra de herramientas con botones estáticos y dinámicos."""
        tool_controls = [ft.Text("Herramientas", weight=ft.FontWeight.BOLD)]
        
        static_tools = [
            ("select", ft.Icons.TOUCH_APP, "Seleccionar"),
            ("broken", ft.Icons.BLOCK, "Bloquear/Desbloquear"),
            ("delete", ft.Icons.DELETE_FOREVER, "Convertir en Pasillo"),
        ]
        tool_controls.extend([self._build_tool_button(t[0], t[1], t[2]) for t in static_tools])
        
        tool_controls.append(ft.Divider(height=10))
        
        # Las herramientas de tipo de asiento se crean dinámicamente desde la BD.
        for seat_type in self.seat_types:
            icon = ft.Icons.EVENT_SEAT
            if "VIP" in seat_type.name: icon = ft.Icons.DIAMOND
            if "Discapacitados" in seat_type.name: icon = ft.Icons.ACCESSIBLE
            tool_controls.append(self._build_tool_button(f"type_{seat_type.id}", icon, seat_type.name))
            
        return ft.Container(
            content=ft.Column(tool_controls, spacing=10, alignment=ft.MainAxisAlignment.START),
            width=200,
            padding=10,
            bgcolor=self.theme.color_scheme.surface_variant,
            border_radius=10
        )

    def _build_tool_button(self, tool_id, icon, label):
        """Crea un botón individual para la barra de herramientas."""
        is_selected = self.current_tool == tool_id
        return ft.Container(
            content=ft.Row([ft.Icon(icon, size=20), ft.Text(label, size=12)], spacing=8),
            padding=10,
            bgcolor=self.theme.color_scheme.primary_container if is_selected else ft.Colors.TRANSPARENT,
            border_radius=8,
            ink=True,
            on_click=lambda e, tid=tool_id: self._select_tool(tid)
        )

    def _select_tool(self, tool_id):
        """Maneja la selección de una nueva herramienta y actualiza el feedback."""
        self.current_tool = tool_id
        tool_name = tool_id
        if tool_id.startswith("type_"):
            type_id = int(tool_id.split('_')[1])
            tool_name = next((st.name for st in self.seat_types if st.id == type_id), "desconocido")
        
        self.status_bar.value = f"Herramienta seleccionada: {tool_name.capitalize()}"
        # Re-render para mostrar visualmente la herramienta seleccionada.
        self.toolbar.content.controls = self._build_toolbar().content.controls
        self.page.update()

    def _build_seat_grid(self):
        """Construye la parrilla de asientos basada en los datos actuales."""
        seat_map = {(s.x_position, s.y_position): s for s in self.seats_to_render}
        rows = []
        for y in range(self.max_y + 1):
            row_controls = []
            for x in range(self.max_x + 1):
                seat = seat_map.get((x, y))
                row_controls.append(self._build_seat_control(x, y, seat))
            rows.append(ft.Row(row_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=5))
        return ft.Column(rows, alignment=ft.MainAxisAlignment.CENTER, spacing=5, scroll=ft.ScrollMode.AUTO)

    def _build_seat_control(self, x, y, seat: Seat | None):
        """Crea un control individual y visual para un asiento en la parrilla."""
        color = ft.Colors.GREY_300 # Color por defecto para pasillos.
        icon = None
        tooltip_text = f"Pasillo ({x},{y})"
        seat_type_map = {st.id: st for st in self.seat_types}

        if seat:
            seat_type = seat_type_map.get(seat.seat_type_id)
            seat_type_name = seat_type.name if seat_type else "Desconocido"
            # Tooltip mejorado con más información.
            tooltip_text = f"Asiento {seat.row_label}{seat.number} ({seat_type_name}) - {seat.status}"
            
            # Asigna color basado en el estado y tipo de asiento.
            if seat.status != SeatStatus.ACTIVE.value:
                color = "rgba(0,0,0,0.4)" # Negro semi-transparente para bloqueados.
                icon = ft.Icons.BLOCK
            elif seat_type:
                if "VIP" in seat_type.name: color = ft.Colors.AMBER
                elif "Discapacitados" in seat_type.name: color = ft.Colors.LIGHT_BLUE_500
                else: color = self.theme.color_scheme.primary
            else:
                 color = self.theme.color_scheme.primary
        
        return ft.Container(
            content=ft.Icon(icon, size=16, color=ft.Colors.WHITE) if icon else None,
            width=30, height=30, bgcolor=color, border_radius=4,
            on_click=lambda e: self._on_seat_click(x, y),
            tooltip=tooltip_text
        )

    def _on_seat_click(self, x, y):
        """Maneja la lógica de edición al hacer clic en un asiento y da feedback."""
        seat = next((s for s in self.seats_to_render if s.x_position == x and s.y_position == y), None)
        self.status_bar.value = "" # Limpia la barra de estado.

        if self.current_tool == "select":
            self.status_bar.value = f"Información: {seat.row_label}{seat.number} ({seat.status})" if seat else f"Posición vacía ({x},{y})."
        
        elif self.current_tool == "delete":
            if seat:
                self.seats_to_render.remove(seat)
                self.status_bar.value = f"Asiento en ({x},{y}) eliminado. Se convertirá en pasillo."
            else:
                self.status_bar.value = "Acción no aplicable: ya es un pasillo."
        
        elif self.current_tool == "broken":
            if seat:
                is_currently_broken = seat.status == SeatStatus.BROKEN.value
                seat.status = SeatStatus.ACTIVE.value if is_currently_broken else SeatStatus.BROKEN.value
                self.status_bar.value = f"Asiento {seat.row_label}{seat.number} ahora está {'ACTIVO' if is_currently_broken else 'BLOQUEADO'}."
            else:
                self.status_bar.value = "Acción no aplicable: no se puede bloquear un pasillo."

        elif self.current_tool.startswith("type_"):
            type_id = int(self.current_tool.split('_')[1])
            seat_type = next((st for st in self.seat_types if st.id == type_id), None)
            
            if not seat_type:
                self.status_bar.value = "Error: Tipo de asiento no encontrado."
                self.page.update()
                return

            row_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            row_label = row_labels[y] if y < len(row_labels) else f"F{y+1}"

            if seat:
                seat.seat_type_id = type_id
                seat.status = SeatStatus.ACTIVE.value # Activa el asiento al cambiarle el tipo.
                self.status_bar.value = f"Asiento {seat.row_label}{seat.number} cambiado a tipo '{seat_type.name}'."
            else:
                # Crea un nuevo objeto de asiento si el espacio estaba vacío.
                new_seat = Seat(
                    id=None, theater_id=self.theater.id,
                    row_label=row_label, number=x + 1,
                    seat_type_id=type_id, status=SeatStatus.ACTIVE.value,
                    x_position=x, y_position=y,
                    seat_type_name="", price_modifier=0
                )
                self.seats_to_render.append(new_seat)
                self.status_bar.value = f"Nuevo asiento '{seat_type.name}' creado en ({x},{y})."
        
        self.seat_grid.controls = self._build_seat_grid().controls
        self.page.update()

    def _save_layout(self, e):
        """Guarda todo el layout (creaciones, actualizaciones, borrados) en la BD."""
        try:
            self.theater_service.update_seat_layout(self.theater.id, self.seats_to_render)
            self.on_save()
            self.close(e)
        except Exception as ex:
            logger.error(f"Error al guardar layout: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error al guardar: {ex}"), bgcolor=ft.Colors.RED)
            self.page.snack_bar.open = True
            self.page.update()

    def close(self, e):
        """Cierra el diálogo actual."""
        self.page.close(self)
