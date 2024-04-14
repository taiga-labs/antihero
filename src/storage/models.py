from sqlalchemy import String, BIGINT, Integer, ForeignKey, Boolean
from sqlalchemy.orm import (
    mapped_column,
    Mapped,
    relationship,
    DeclarativeBase,
    declared_attr,
)


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"


class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    address: Mapped[str] = mapped_column(String, nullable=True, unique=True)
    seqno: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    language: Mapped[str] = mapped_column(String, nullable=False, server_default="en")
    win: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class Nft(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_nft: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    address: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    activated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="f")
    rare: Mapped[int] = mapped_column(Integer, nullable=False)
    duel: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="f")
    arena: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="f")
    withdraw: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="f")

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    user: Mapped[User] = relationship(User, lazy="joined")


class Player(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nft_id: Mapped[int] = mapped_column(Integer, ForeignKey("nfts.id"), nullable=False)
    nft: Mapped[User] = relationship(Nft, lazy="joined")
    score: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    notified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="f")


class Game(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    player_l_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=False
    )
    player_l: Mapped[User] = relationship(
        Player, foreign_keys="[Game.player_l_id]", lazy="joined"
    )
    player_r_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=False
    )
    player_r: Mapped[User] = relationship(
        Player, foreign_keys="[Game.player_r_id]", lazy="joined"
    )
    closed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="f")
    start_time: Mapped[int] = mapped_column(Integer, nullable=False)


class Withdrawal(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nft_address: Mapped[str] = mapped_column(String, nullable=False)
    dst_address: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="t")
