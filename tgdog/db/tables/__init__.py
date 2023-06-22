from sqlalchemy import Column, Integer

from tgdog.db.tables.base import Base
from tgdog.db.tables.gui import (
    CheckBoxButton,
    NumberSelectionTab,
    PyrogramButton,
    SimpleButton,
    SingleSelectButton,
    Tab,
    Text,
    TimeZoneSelectionTab,
    Window,
)


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
