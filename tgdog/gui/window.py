import pyrogram
from sqlalchemy import select

from tgdog.constants import ANONYMOUS_USER_ID, DEFAULT_USER_ID
from tgdog.db import db
from tgdog.gui.callback_query import current_callback_query
from tgdog.gui.exceptions import (
    GUIError,
    NoWindowError,
    PermissionError,
)
from tgdog.gui.registry import WindowMeta
from tgdog.gui import tables
from tgdog.users import current_user


class Window(metaclass=WindowMeta):
    send_message_kwargs = None
    edit_message_kwargs = None
    message_kwargs = None
    resend_window_message_after_input_processing = True

    def __init__(self, controller, chat_id, user_id=None):
        self.controller = controller
        self.chat_id = chat_id
        self.user_id = user_id
        self.processing_input = False

    def find_tab_index_by_class(self, tab_class):
        try:
            return self.tabs.index(tab_class)
        except ValueError:
            raise GUIError('Requested tab not found')

    def find_tab_index_by_class_name(self, class_name):
        for i, tab in enumerate(self.tabs):
            if tab.__name__ == class_name:
                return i
        raise GUIError('Requested tab not found')

    async def build(self, *args, tab=None, **kwargs):
        self.row = tables.Window(chat_id=self.chat_id, user_id=self.user_id)
        self.row.window_class_crc32 = self.crc32
        tab_index = 0 if not tab else self.find_tab_index_by_class(tab)
        self.current_tab = self.tabs[tab_index](self)
        self.row.current_tab_index = tab_index
        db.add(self.row)
        await self.current_tab.build(*args, **kwargs)

    def rebind(self):
        db.add(self.row)
        self.current_tab.rebind()

    async def render(
        self,
        send_message_kwargs=None,
        edit_message_kwargs=None,
        message_kwargs=None,
    ):
        send_message_kwargs = send_message_kwargs or self.send_message_kwargs or {}
        edit_message_kwargs = edit_message_kwargs or self.edit_message_kwargs or {}
        message_kwargs = message_kwargs or self.message_kwargs or {}
        text, keyboard = await self.current_tab.render()
        if self.current_tab.row.input_processing_enabled:
            self.row.input_required = True
        else:
            self.row.input_required = False
        if self.current_tab.row.resend_window_message:
            resend_window_message = True
            delete_previous_window_message_before_resending = self.current_tab.row.delete_previous_window_message_before_resending
        else:
            resend_window_message = self.processing_input and self.resend_window_message_after_input_processing
            delete_previous_window_message_before_resending = True
        if resend_window_message and self.row.message_id:
            if delete_previous_window_message_before_resending:
                try:
                    await self.controller.app.delete_messages(self.row.chat_id, self.row.message_id)
                except pyrogram.errors.MessageDeleteForbidden:
                    pass
            self.row.message_id = None
        if not self.row.message_id:
            message = await self.controller.send_message(
                text,
                self.row.chat_id,
                reply_markup=keyboard,
                blocking=True,
                **message_kwargs | send_message_kwargs,
            )
            if message is None:  # Network failure, bot is banned by user, etc...
                await self.destroy()
                return
            self.row.message_id = message.id
        else:
            try:
                await self.controller.app.edit_message_text(
                    self.row.chat_id,
                    self.row.message_id,
                    text,
                    reply_markup=keyboard,
                    **message_kwargs | edit_message_kwargs,
                )
            except pyrogram.errors.MessageNotModified:
                pass

    @classmethod
    async def reconstruct(cls, controller, chat_id, window_id, message=None, row=None):
        if not row:
            stmt = select(tables.Window).where(
                tables.Window.id==window_id,
                tables.Window.chat_id==chat_id,
            )
            row = (await db.execute(stmt)).scalar()
        if row is None:
            raise NoWindowError
        # If we process a callback query, we will always have the current user.
        current_user_id = current_user.user_id if current_user.is_set else ANONYMOUS_USER_ID
        if row.user_id == ANONYMOUS_USER_ID and current_callback_query.is_set:
            # Now we know that the current user id definitely contains the id of some user.
            try:
                info = await controller.app.get_chat_member(chat_id, current_user_id)
                if info.privileges.is_anonymous:
                    # It's actually anonymous.
                    current_user_id = ANONYMOUS_USER_ID
            except pyrogram.errors.exceptions.bad_request_400.UserNotParticipant:
                # Raising this exception implicitly makes it clear that the user is anonymous.
                current_user_id = ANONYMOUS_USER_ID
        if row.user_id != DEFAULT_USER_ID and row.user_id != current_user_id:
            raise PermissionError
        if message is None:
            message = await controller.app.get_messages(chat_id, row.message_id)
            # "A message can be empty in case it was deleted or you tried to retrieve a message that doesn’t exist yet."
            if message.empty:
                await db.delete(row)
                raise NoWindowError('Message not found')
        if message.id != row.message_id:
            raise NoWindowError('Message id does not match the id in the database')
        buttons = []
        if isinstance(message.reply_markup, pyrogram.types.InlineKeyboardMarkup):
            buttons = message.reply_markup.inline_keyboard
        window = cls(controller, row.chat_id, row.user_id)
        window.row = row
        window.current_tab = window.tabs[row.current_tab_index](window)
        await window.current_tab.reconstruct(message.text, buttons)
        return window

    async def destroy(self):
        await self.current_tab.destroy()
        for saved_tab_index in self.row.saved_tab_indexes:
            self.row.current_tab_index = saved_tab_index
            self.current_tab = self.tabs[saved_tab_index](self)
            await self.current_tab.restore()
            await self.current_tab.destroy()

        await db.delete(self.row)

    async def handle_button_activation(self):
        await self.current_tab.handle_button_activation()

    async def process_input(self, message):
        # When processing input, the tab can be switched,
        # so we save the information to delete the user's message now.
        user_message_deletion_required = self.current_tab.row.delete_user_input_message
        try:
            await self.current_tab.process_input(message.text)
        finally:
            if user_message_deletion_required:
                try:
                    await message.delete()
                except pyrogram.errors.MessageDeleteForbidden:
                    pass

    async def switch_tab(self, new_tab, *args, save_current_tab=False, **kwargs):
        if isinstance(new_tab, str):
            new_tab_index = self.find_tab_index_by_class_name(new_tab)
            new_tab_class = self.tabs[new_tab_index]
        else:
            new_tab_index = self.find_tab_index_by_class(new_tab)
            new_tab_class = new_tab
        if new_tab_index == self.row.current_tab_index:
            raise ValueError('This tab is already active')
        if not save_current_tab:
            await self.current_tab.destroy()
        else:
            await self.current_tab.save()
            self.row.saved_tab_indexes.append(self.row.current_tab_index)
        self.row.current_tab_index = new_tab_index
        self.current_tab = new_tab_class(self)
        if new_tab_index in self.row.saved_tab_indexes:
            await self.current_tab.restore()
            self.row.saved_tab_indexes.remove(new_tab_index)
        else:
            await self.current_tab.build(*args, **kwargs)
        return self.current_tab
