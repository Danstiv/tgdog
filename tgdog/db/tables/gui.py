import pyrogram
from sqlalchemy import Boolean, Column, Integer, JSON, LargeBinary, String
from sqlalchemy.ext.mutable import MutableList

from tgdog.constants import DEFAULT_USER_ID
from tgdog.db.tables.base import Base
from tgdog.gui.mixins import (
    ButtonMixin,
    CheckBoxButtonMixin,
    SingleSelectButtonMixin,
    TabMixin,
    TableWithWindowMixin,
    TextMixin,
)


class Window(Base):
    __tablename__ = 'window'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False, default=DEFAULT_USER_ID)
    window_class_crc32 = Column(LargeBinary(4), nullable=False)
    message_id = Column(Integer, nullable=True)
    current_tab_index = Column(Integer)
    saved_tab_indexes = Column(MutableList.as_mutable(JSON), default=[])
    input_required = Column(Boolean, default=False)


class Tab(TabMixin, Base):
    __tablename__ = 'tab'


class TimeZoneSelectionTab(TabMixin, Base):
    __tablename__ = 'time_zone_selection_tab'
    selected_time_zone_offset = Column(Integer, nullable=False)


class NumberSelectionTab(TabMixin, Base):
    __tablename__ = 'number_selection_tab'
    min_value = Column(Integer)
    initial_value = Column(Integer, nullable=False)
    max_value = Column(Integer)
    selected_value = Column(Integer)


class Text(TextMixin, Base):
    __tablename__ = 'text'


class PyrogramButton(TableWithWindowMixin, Base):
    __tablename__ = 'pyrogram_button'
    id = Column(Integer, primary_key=True)
    text = Column(String)
    callback_data = Column(LargeBinary(64))
    url = Column(String)
    web_app_url = Column(String)
    login_url = Column(String)
    user_id = Column(Integer)
    switch_inline_query = Column(String)
    switch_inline_query_current_chat = Column(String)
    # callback_game: "Placeholder, currently holds no information."
    right_button = Column(Boolean, default=False)
    tab_index = Column(Integer)
    simple_attrs = [
        'text', 'callback_data',
        'url', 'login_url',
        'user_id', 'switch_inline_query',
        'switch_inline_query_current_chat'
    ]

    def set_data(self, button):
        for attr in self.simple_attrs:
            setattr(self, attr, getattr(button, attr))
        if button.web_app:
            self.web_app_url = button.web_app.url

    def get_button(self):
        data = {}
        for attr in self.simple_attrs:
            data[attr] = getattr(self, attr)
        if self.web_app_url:
            data['web_app'] = pyrogram.types.WebAppInfo(url=self.web_app_url)
        return pyrogram.types.InlineKeyboardButton(**data)


class SimpleButton(ButtonMixin, Base):
    __tablename__ = 'simple_button'
    arg = Column(String)


class CheckBoxButton(CheckBoxButtonMixin, Base):
    __tablename__ = 'check_box_button'
    arg = Column(String)


class SingleSelectButton(SingleSelectButtonMixin, Base):
    __tablename__ = 'single_select_button'
    arg = Column(String)
