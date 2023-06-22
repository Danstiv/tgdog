import pyrogram
from pyrogram import filters
from sqlalchemy import desc, or_, select

from tgdog.constants import ANONYMOUS_USER_ID, DEFAULT_USER_ID
from tgdog.db import db, tables
from tgdog.enums import Category
from tgdog.group_manager import group_manager
from tgdog.gui.callback_query import current_callback_query
from tgdog.gui.constants import CALLBACK_QUERY_SIGNATURE
from tgdog.gui.exceptions import (
    NoWindowError,
    PermissionError,
    ReconstructionError,
    StopUserRequestProcessing,
)
from tgdog.gui.input_fields import InputField
from tgdog.gui.registry import window_registry
from tgdog.gui.tabs import Tab
from tgdog.gui.window import Window
from tgdog.handler_decorators import on_callback_query, on_message
from tgdog.users import current_user


class TGBotGUIMixin:

    @on_callback_query(category=Category.INITIALIZE, group=group_manager.PROCESS_CALLBACK_QUERY)
    async def set_callback_query_context(self, callback_query):
        current_callback_query.set_context_var_value(callback_query)

    @on_callback_query(group=group_manager.PROCESS_CALLBACK_QUERY)
    async def handle_callback_query(self, callback_query):
        if callback_query.data[:4] != CALLBACK_QUERY_SIGNATURE:
            callback_query.continue_propagation()
        try:
            window_cls = window_registry.get(callback_query.data[4:8], None)
            if not window_cls:
                raise NoWindowError
            window_id = int.from_bytes(callback_query.data[8:12], 'big')
            try:
                window = await window_cls.reconstruct(
                    self,
                    chat_id=callback_query.message.chat.id,
                    window_id=window_id,
                    message=callback_query.message
                )
                await window.handle_button_activation()
            except StopUserRequestProcessing as e:
                window = e.window
                if e.alert is not None:
                    await callback_query.answer(e.alert, show_alert=True)
            await window.render()
            await callback_query.answer()
        except PermissionError:
            await callback_query.answer('Извините, вы не можете активировать эту кнопку.', show_alert=True)
        except ReconstructionError:
            await callback_query.answer('Извините, эта клавиатура устарела и больше не обслуживается. Пожалуйста, попробуйте воспользоваться клавиатурой из более позднего сообщения.', show_alert=True)
        except Exception:
            await callback_query.answer('Извините, что-то пошло не так.\nПожалуйста, попробуйте позже.', show_alert=True)
            raise
        callback_query.stop_propagation()

    @on_callback_query(category=Category.FINALIZE, group=group_manager.RESET_CALLBACK_QUERY_CONTEXT)
    async def callback_query_reset_handler(self, callback_query):
        current_callback_query.reset_context_var()

    @on_message(filters.text, group=group_manager.PROCESS_INPUT)
    async def process_input(self, message):
        current_user_id = current_user.user_id if current_user.is_set else ANONYMOUS_USER_ID
        stmt = select(tables.Window).where(
            tables.Window.chat_id == message.chat.id,
            or_(tables.Window.user_id == DEFAULT_USER_ID, tables.Window.user_id == current_user_id),
            tables.Window.input_required == True
        ).order_by(
            desc(tables.Window.id)
        )
        window = (await db.execute(stmt)).scalar()
        if not window:
            message.continue_propagation()
        window_class = window_registry[window.window_class_crc32]
        try:
            try:
                window = await window_class.reconstruct(self, message.chat.id, window.id, row=window)
            except ReconstructionError:
                message.continue_propagation()
            window.processing_input = True
            await window.process_input(message)
        except StopUserRequestProcessing as e:
            window = e.window
        await window.render()
        message.stop_propagation()
