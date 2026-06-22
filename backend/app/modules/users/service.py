from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserUpdate


class UserAlreadyExistsError(Exception):
    pass


class UsernameAlreadyExistsError(UserAlreadyExistsError):
    pass


class EmailAlreadyExistsError(UserAlreadyExistsError):
    pass


class UserNotFoundError(Exception):
    pass


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.repository.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        return self.repository.get_by_email(email.lower())

    def get_user_by_username(self, username: str) -> User | None:
        return self.repository.get_by_username(username.strip())

    def list_users(self, offset: int = 0, limit: int = 100) -> list[User]:
        return self.repository.list_users(offset=offset, limit=limit)

    def create_user(self, data: UserCreate, hashed_password: str) -> User:
        existing_by_email = self.repository.get_by_email(data.email.lower())
        if existing_by_email is not None:
            raise EmailAlreadyExistsError(f"Email '{data.email}' is already in use.")

        existing_by_username = self.repository.get_by_username(data.username.strip())
        if existing_by_username is not None:
            raise UsernameAlreadyExistsError(
                f"Username '{data.username}' is already in use."
            )

        return self.repository.create(
            username=data.username.strip(),
            email=data.email.lower(),
            hashed_password=hashed_password,
            is_active=True,
            role=data.role,
        )

    def update_current_user(self, user_id: int, data: UserUpdate) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError("User not found")

        username = data.username.strip() if data.username is not None else None
        email = data.email.lower() if data.email is not None else None

        if username is not None and username != user.username:
            existing_by_username = self.repository.get_by_username(username)
            if existing_by_username is not None and existing_by_username.id != user.id:
                raise UsernameAlreadyExistsError(
                    f"Username '{data.username}' is already in use."
                )

        if email is not None and email != user.email:
            existing_by_email = self.repository.get_by_email(email)
            if existing_by_email is not None and existing_by_email.id != user.id:
                raise EmailAlreadyExistsError(
                    f"Email '{data.email}' is already in use."
                )

        return self.repository.update(
            user,
            username=username,
            email=email,
        )

    def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError("User not found")

        username = data.username.strip() if data.username is not None else None
        email = data.email.lower() if data.email is not None else None

        if username is not None and username != user.username:
            existing_by_username = self.repository.get_by_username(username)
            if existing_by_username is not None and existing_by_username.id != user.id:
                raise UsernameAlreadyExistsError(
                    f"Username '{data.username}' is already in use."
                )

        if email is not None and email != user.email:
            existing_by_email = self.repository.get_by_email(email)
            if existing_by_email is not None and existing_by_email.id != user.id:
                raise EmailAlreadyExistsError(
                    f"Email '{data.email}' is already in use."
                )

        return self.repository.update(
            user,
            username=username,
            email=email,
            is_active=data.is_active,
            role=data.role,
        )
