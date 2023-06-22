import pyrogram

from tgdog.db import tables
from tgdog.gui.buttons.mixins import ButtonWithCallback


class CheckBoxButton(ButtonWithCallback):
    table = tables.CheckBoxButton

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'row' not in kwargs:  # Creation
            self.row.text = self.text
        else:  # Reconstruction
            self.text = self.row.text

    async def render(self):
        await self.db_render()
        if self.row.is_checked:
            prefix = self.get_column_value_or_default('is_checked_prefix')
        else:
            prefix = self.get_column_value_or_default('is_unchecked_prefix')
        return pyrogram.types.InlineKeyboardButton(prefix + self.text, callback_data=self.row.callback_data)

    async def handle_button_activation(self, row_index, column_index):
        self.row.is_checked = not self.row.is_checked
        await self.callback(self.row.is_checked, self.row.arg)
