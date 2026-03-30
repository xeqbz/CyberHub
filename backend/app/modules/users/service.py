from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate


class UserAlreadyExistsError(Exception):
    pass


class UsernameAlreadyExistsError(UserAlreadyExistsError):
    pass


class EmailAlreadyExistsError(UserAlreadyExistsError):
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
            raise UsernameAlreadyExistsError(f"Username '{data.username}' is already in use.")
        
        return self.repository.create(
            username=data.username.strip(),
            email=data.email.lower(),
            hashed_password=hashed_password,
            is_active=True,
        )