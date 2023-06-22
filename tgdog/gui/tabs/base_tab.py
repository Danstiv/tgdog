from sqlalchemy import select

from tgdog.db import db
from tgdog.gui.exceptions import (
    GUIError,
    ReconstructionError,
    StopUserRequestProcessing,
)
from tgdog.gui.keyboards import SimpleKeyboard
from tgdog.gui.texts import Text


class BaseTab:
    text_class = Text
    keyboard_class = SimpleKeyboard
    input_fields = []
    rerender_text = True

    def __init__(self, window):
        self.window = window
        self.message_text = None
        self.text = self.get_text()
        self.keyboard = self.get_keyboard()
        self.activated_button = None

    def get_text(self):
        return  self.text_class(self)

    async def get_text_data(self):
        return {}

    def get_keyboard(self):
        return self.keyboard_class(self)

    async def build(self, *args, **kwargs):
        self.row = self.table(*args, window=self.window.row, **kwargs)
        self.row.index_in_window = self.window.row.current_tab_index
        db.add(self.row)
        # In some places further window and tab identifiers will be needed.
        # Therefore, we need to insert the previously created window and tab to the database.
        await db.flush()
        await self.text.build()

    def rebind(self):
        db.add(self.row)
        self.text.rebind()
        self.keyboard.rebind()

    async def render(self):
        if self.rerender_text or not self.message_text:
            if self.row.input_processing_enabled and self.input_fields[self.row.current_input_field_name].text:
                self.text.set_input_field_text(self.input_fields[self.row.current_input_field_name].text)
            text = await self.text.render()
        else:
            text = self.message_text
        keyboard = await self.keyboard.render()
        return text, keyboard

    async def reconstruct(self, text, buttons):
        stmt = select(self.table).where(
            self.table.window_id == self.window.row.id,
            self.table.index_in_window == self.window.row.current_tab_index
        )
        self.row = (await db.execute(stmt)).scalar()
        if not self.row:
            raise ReconstructionError('Tab not found')
        self.message_text = text
        await self.text.reconstruct(text)
        await self.keyboard.reconstruct(buttons)

    def stop_user_request_processing(self, **kwargs):
        raise StopUserRequestProcessing(window=self.window, **kwargs)

    async def handle_button_activation(self):
        await self.keyboard.handle_button_activation()

    async def process_input(self, text):
        callback = getattr(
            self,
            self.input_fields[self.row.current_input_field_name].method_name.format(
                name=self.row.current_input_field_name
            )
        )
        await callback(text)

    def select_input_field(self, field_name):
        if field_name not in self.input_fields:
            raise NameError(f'Field "{field_name}" not found')
        self.row.current_input_field_name = field_name

    def enable_input_processing(self):
        if self.row.current_input_field_name is None:
            raise ValueError('Input field not selected')
        self.row.input_processing_enabled = True

    def disable_input_processing(self):
        self.row.input_processing_enabled = False

    def enable_window_message_resending(self, delete_previous_window_message=True):
        self.row.resend_window_message = True
        self.row.delete_previous_window_message_before_resending = (
            True if delete_previous_window_message else False
        )

    def disable_window_message_resending(self):
        self.row.resend_window_message = False

    def enable_user_input_message_deletion(self):
        self.row.delete_user_input_message = True

    def disable_user_input_message_deletion(self):
        self.row.delete_user_input_message = False

    async def save(self):
        await self.text.save()
        await self.keyboard.save()

    async def restore(self):
        stmt = select(self.table).where(
            self.table.window_id == self.window.row.id,
            self.table.index_in_window == self.window.row.current_tab_index
        )
        row = (await db.execute(stmt)).scalar()
        if not row:
            raise GUIError('Tab restore failed')
        self.row = row
        try:
            await self.text.restore()
            await self.keyboard.restore()
        except ReconstructionError:
            raise GUIError('Tab restore succeeded, but reconstruction failed')

    async def destroy(self):
        await db.delete(self.row)
        await self.text.destroy()
        await self.keyboard.destroy()
