from sqlalchemy import select

from tgdog.db import db
from tgdog.gui.exceptions import ReconstructionError


class BaseText:

    def __init__(self, tab):
        self.tab = tab
        self.one_time_header = True

    async def build(self, *args, **kwargs):
        self.row = self.table(
            *args,
            window_id=self.tab.window.row.id,
            tab_index=self.tab.row.index_in_window,
            tab_id=self.tab.row.id,
            **kwargs
        )
        db.add(self.row)

    def rebind(self):
        db.add(self.row)

    def set_header(self, header, one_time=True):
        self.row.header = header
        self.one_time_header = one_time

    def set_body(self, body):
        self.row.body = body

    def prepend_to_body(self, text):
        self.row.body = text + self.row.body

    def append_to_body(self, text):
        self.row.body = self.row.body + text

    def set_input_field_text(self, text):
        self.row.input_field_text = text

    async def render(self):
        text = ''
        if self.row.header:
            text += f'{self.row.header}\n{"-"*60}\n'
            if self.one_time_header:
                self.row.header = None
        body = []
        if self.row.body:
            body.append(self.row.body)
        if self.row.input_field_text:
            body.append(self.row.input_field_text)
        body = '\n'.join(body)
        if not body:
            body = '.'
        text += body
        if text_data := await self.tab.get_text_data():
            return text.format(**text_data)
        return text

    async def reconstruct(self, text):
        # The initial text does not seem to be needed here, but let it be just in case
        stmt = select(self.table).where(
            self.table.window_id == self.tab.window.row.id,
            self.table.tab_index == self.tab.row.index_in_window,
            self.table.tab_id == self.tab.row.id,
        )
        self.row = (await db.execute(stmt)).scalar()
        if not self.row:
            raise ReconstructionError('Text not found')

    async def save(self):
        pass

    async def restore(self):
        await self.reconstruct(None)

    async def destroy(self):
        await db.delete(self.row)
