import re
from datetime import date, datetime, time
from typing import Annotated

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Integer,
    MetaData,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.settings import settings

DB_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}


engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)

metadata = MetaData(naming_convention=DB_NAMING_CONVENTION)


int_pk = Annotated[int, mapped_column(Integer, primary_key=True, autoincrement=True)]


class Base(DeclarativeBase):
    metadata = metadata

    type_annotation_map = {
        dict: JSON,
        int: BigInteger,
        str: Text,
        bool: Boolean,
        datetime: DateTime,
        date: Date,
        time: Time,
    }

    def dict(self) -> dict:
        """Returns object as dict"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TableNameMixin:
    @declared_attr
    def __tablename__(cls) -> str:
        return camel_to_snake(cls.__name__)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


def camel_to_snake(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
