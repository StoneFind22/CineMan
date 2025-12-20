import flet as ft
from src.services.inventory_service import InventoryService
from src.ui.theme import AppTheme
from src.ui.components.dialogs import show_info_dialog

class StockAdjustmentDialog(ft.AlertDialog):
    """
    Diálogo para realizar ajustes manuales de stock (Pérdidas, Ajustes de Auditoría, Ingresos rápidos).
    """
    def __init__(self, page: ft.Page, inventory_service: InventoryService, theme: AppTheme, item_data: dict, on_save: callable):
        super().__init__()
        self.page = page
        self.inventory_service = inventory_service
        self.theme = theme
        self.item_data = item_data
        self.on_save = on_save

        # Campos
        self.qty_field = ft.TextField(
            label="Cantidad", 
            keyboard_type=ft.KeyboardType.NUMBER, 
            suffix_text=item_data['unit'],
            autofocus=True,
            value="1"
        )
        self.type_dropdown = ft.Dropdown(
            label="Tipo de Movimiento",
            options=[
                ft.dropdown.Option("RESTOCK", text="Reabastecimiento (+)"),
                ft.dropdown.Option("LOSS", text="Pérdida / Merma (-)"),
                ft.dropdown.Option("ADJUSTMENT", text="Ajuste de Auditoría (+/-)"),
            ],
            value="RESTOCK"
        )
        self.notes_field = ft.TextField(label="Motivo / Notas", multiline=True, min_lines=2)

        self.modal = True
        self.title = ft.Text(f"Ajustar Stock: {item_data['name']}")
        self.content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(f"Stock Actual: {item_data['current_stock']:.2f} {item_data['unit']}", weight=ft.FontWeight.BOLD),
                    self.type_dropdown,
                    self.qty_field,
                    self.notes_field
                ],
                tight=True,
                spacing=15
            ),
            width=400
        )
        self.actions = [
            ft.TextButton("Cancelar", on_click=self.close_dialog),
            ft.ElevatedButton("Aplicar Ajuste", on_click=self.save_adjustment)
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def close_dialog(self, e):
        self.page.close(self)

    def save_adjustment(self, e):
        try:
            qty = float(self.qty_field.value)
            movement_type = self.type_dropdown.value
            
            # Lógica de signos
            final_qty = qty
            if movement_type == "LOSS":
                final_qty = -abs(qty) # Asegurar negativo
            elif movement_type == "RESTOCK":
                final_qty = abs(qty) # Asegurar positivo
            elif movement_type == "ADJUSTMENT":
                final_qty = qty

            if final_qty == 0:
                self.qty_field.error_text = "La cantidad no puede ser 0"
                self.qty_field.update()
                return

            # TODO: Usar usuario real de la sesión
            user_id = 1 

            success = self.inventory_service.add_stock_movement(
                item_id=self.item_data['id'],
                quantity=final_qty,
                movement_type=movement_type,
                user_id=user_id,
                notes=self.notes_field.value or "Ajuste manual desde Inventario"
            )

            if success:
                show_info_dialog(self.page, "Ajuste Realizado", "El stock ha sido actualizado correctamente.")
                self.on_save()
                self.page.close(self)
            else:
                show_info_dialog(self.page, "Error", "No se pudo actualizar el stock en la base de datos.")

        except ValueError:
            self.qty_field.error_text = "Valor numérico inválido"
            self.qty_field.update()

    def show(self):
        self.page.open(self)
