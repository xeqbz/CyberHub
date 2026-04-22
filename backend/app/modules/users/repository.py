from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.users.model import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.scalar(stmt)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self.db.scalar(stmt)

    def list_users(self, offset: int = 0, limit: int = 100) -> list[User]:
        stmt = select(User).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(
        self,
        *,
        username: str,
        email: str,
        hashed_password: str,
        is_active: bool = True,
    ) -> User:
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=is_active,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(
        self,
        user: User,
        *,
        username: str | None = None,
        email: str | None = None,
    ) -> User:
        if username is not None:
            user.username = username

        if email is not None:
            user.email = email

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user