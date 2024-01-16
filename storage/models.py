import time
from typing import Any

from sqlalchemy import String, Integer, ForeignKey, Boolean, JSON, func
from sqlalchemy.orm import mapped_column, Mapped, relationship, DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"


class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    address: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    verif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="f")
    count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0") # TODO server default int 0
    win: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0") # TODO server default int 0
    bonus: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0") # TODO server default int 0


class Nft(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_nft: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    address: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    rare: Mapped[str] = mapped_column(String, nullable=False)
    duel: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="f")
    arena: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="f")

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    user: Mapped[User] = relationship(User, lazy="joined")
