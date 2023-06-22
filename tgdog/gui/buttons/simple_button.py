from tgdog.db import tables
from tgdog.gui.buttons.mixins import ButtonWithCallback


class SimpleButton(ButtonWithCallback):
    table = tables.SimpleButton

    async def handle_button_activation(self, row_index, column_index):
        await self.callback(self.row.arg)
