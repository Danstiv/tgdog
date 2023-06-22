import pyrogram

from tgdog.db import tables
from tgdog.gui.buttons.check_box_button import CheckBoxButton


class SingleSelectButton(CheckBoxButton):
    table = tables.SingleSelectButton

    async def handle_button_activation(self, row_index, column_index):
        if self.row.is_checked:
            return
        for button in self.keyboard.buttons_iter():
            if isinstance(button, self.__class__) and button.row.selection_group == self.row.selection_group and button.row.is_checked:
                button.row.is_checked = False
                break
        self.row.is_checked = True
        await self.callback(self.row.arg)
