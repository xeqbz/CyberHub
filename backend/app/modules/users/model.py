from enum import Enum

from sqlalchemy import Boolean, Integer, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseModel


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    ORGANIZER = "ORGANIZER"


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, name="user_role"),
        default=UserRole.USER,
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        default=1000,
        nullable=False,
    )
    wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    losses: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    draws: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
