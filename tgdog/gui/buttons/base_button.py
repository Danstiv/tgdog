import uuid

import pyrogram

from tgdog.db import db
from tgdog.gui.constants import CALLBACK_QUERY_SIGNATURE
from tgdog.gui.registry import ButtonMeta


class BaseButton(metaclass=ButtonMeta):

    def __init__(self, text=None, *args, row=None, **kwargs):
        self.text = text
        self.row = row if row else self.table(*args, **kwargs)

    def set_text(self, text):
        self.text = text

    async def handle_button_activation(self, row_index, column_index):
        raise NotImplementedError

    def rebind(self):
        db.add(self.row)

    async def db_render(self):
        if self.row.id is None:
            self.row.callback_data = (
                CALLBACK_QUERY_SIGNATURE  # 4 bytes
                + self.keyboard.tab.window.crc32  # 4 bytes
                + self.keyboard.tab.window.row.id.to_bytes(4, 'big')  # 4 bytes
                + self.crc32  # 4 bytes
                + uuid.uuid4().bytes  # 16 bytes
            )
            self.row.window = self.keyboard.tab.window.row
        db.add(self.row)

    async def render(self):
        await self.db_render()
        return pyrogram.types.InlineKeyboardButton(self.text, callback_data=self.row.callback_data)

    async def destroy(self):
        await db.delete(self.row)

    def get_column_value_or_default(self, name):
        value = getattr(self.row, name)
        if value is not None:
            return value
        return self.row.__table__.c[name].default.arg

