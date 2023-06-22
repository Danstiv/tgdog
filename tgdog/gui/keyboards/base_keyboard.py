import pyrogram
from sqlalchemy import select

from tgdog.db import db
from tgdog.gui import tables
from tgdog.gui.buttons import BaseButton
from tgdog.gui.callback_query import current_callback_query
from tgdog.gui.exceptions import ReconstructionError
from tgdog.gui.registry import button_registry


class BaseKeyboard:

    def __init__(self, tab):
        self.tab = tab
        self.buttons = []

    def add_row(self, *buttons):
        if not buttons:
            raise ValueError('The row must not be empty')
        self.buttons.append(list(buttons))

    def add_button(self, button):
        if not self.buttons:
            self.buttons.append([])
        self.buttons[-1].append(button)

    async def remove_buttons_by_name(self, name):
        buttons = self.buttons
        self.buttons = []
        for row in buttons:
            new_row = []
            for button in row:
                if button.row.name != name:
                    new_row.append(button)
                    continue
                await button.destroy()
            if new_row:
                self.buttons.append(new_row)

    async def clear(self):
        [await button.destroy() for row in self.buttons for button in row]
        self.buttons = []

    def buttons_iter(self):
        for row in self.buttons:
            yield from row

    def find_buttons_by_name(self, name):
        buttons = []
        for button in self.buttons_iter():
            if button.row.name == name:
                buttons.append(button)
        return buttons

    def rebind(self):
        [button.rebind() for row in self.buttons for button in row]

    async def render(self):
        keyboard = []
        for row in self.buttons:
            keyboard.append([])
            for button in row:
                if isinstance(button, pyrogram.types.InlineKeyboardButton):
                    keyboard[-1].append(button)
                    continue
                if not isinstance(button, BaseButton):
                    raise ValueError(f'Button {button} is not a subclass of BaseButton')
                button.keyboard = self
                keyboard[-1].append(await button.render())
        return None if not keyboard else pyrogram.types.InlineKeyboardMarkup(keyboard)

    async def reconstruct(self, buttons):
        # Perhaps there is a more elegant way to do this.
        button_classes_data_map = {}
        db_buttons_count = 0
        callback_data_position_map = {}
        for row_index, row in enumerate(buttons):
            self.buttons.append([])
            for column_index, button in enumerate(row):
                if not button.callback_data:
                    self.buttons[-1].append(button)
                    continue
                button_class = button_registry.get(button.callback_data[12:16], None)
                if not button_class:
                    raise ReconstructionError('Button class not found')
                if button_class not in button_classes_data_map:
                    button_classes_data_map[button_class] = []
                button_classes_data_map[button_class].append(button.callback_data)
                db_buttons_count += 1
                self.buttons[-1].append(button.text)
                callback_data_position_map[button.callback_data] = (row_index, column_index)
        buttons_data = []
        for button_class, buttons_callback_data in button_classes_data_map.items():
            stmt = select(button_class.table).where(
                button_class.table.callback_data.in_(buttons_callback_data)
            )
            temp = (await db.execute(stmt)).scalars()
            buttons_data.extend([{'class': button_class, 'row': b} for b in temp])
        if len(buttons_data) != db_buttons_count:
            raise ReconstructionError(f'{len(buttons_data)} buttons out of {db_buttons_count} were fetched')
        for button_data in buttons_data:
            row_index, column_index = callback_data_position_map[button_data['row'].callback_data]
            text = self.buttons[row_index][column_index]
            button = button_data['class'](text, row=button_data['row'])
            button.keyboard = self
            self.buttons[row_index][column_index] = button

    async def handle_button_activation(self):
        for row_index, row in enumerate(self.buttons):
            for column_index, button in enumerate(row):
                if button.row.callback_data == current_callback_query.data:
                    self.tab.activated_button = button
                    try:
                        await button.handle_button_activation(row_index, column_index)
                    finally:
                        self.tab.activated_button = None
                    return

    async def save(self):
        for row in self.buttons:
            for i, button in enumerate(row):
                if isinstance(button, pyrogram.types.InlineKeyboardButton):
                    db_row = tables.PyrogramButton()
                    db_row.set_data(button)
                else:
                    db_row = tables.PyrogramButton(text=button.text, callback_data=button.row.callback_data)
                if i == len(row)-1:
                    db_row.right_button = True
                db_row.tab_index = self.tab.window.row.current_tab_index
                db_row.window_id = self.tab.window.row.id
                db.add(db_row)

    async def restore(self):
        stmt = select(tables.PyrogramButton).where(
            tables.PyrogramButton.window_id == self.tab.window.row.id,
            tables.PyrogramButton.tab_index == self.tab.row.index_in_window
        )
        db_buttons = (await db.execute(stmt)).scalars()
        buttons = []
        new_row = []
        for db_button in db_buttons:
            button = db_button.get_button()
            new_row.append(button)
            if db_button.right_button:
                buttons.append(new_row)
                new_row = []
            await db.delete(db_button)
        await self.reconstruct(buttons)

    async def destroy(self):
        for row in self.buttons:
            for button in row:
                await button.destroy()
