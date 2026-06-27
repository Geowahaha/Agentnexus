from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.auth.google import GoogleAuthError, GoogleUserInfo, verify_google_id_token
from app.auth.models import Token, User, UserCreate, UserLogin
from app.core.config import settings
from app.repositories.user_repository import UserAlreadyExistsError, UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user_id: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
        payload = {"sub": user_id, "exp": expire}
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_access_token(token: str) -> str | None:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            user_id = payload.get("sub")
            return str(user_id) if user_id else None
        except JWTError:
            return None

    async def register(self, data: UserCreate) -> User:
        hashed_password = self.hash_password(data.password)
        return await self._repository.create(data, hashed_password)

    async def login(self, data: UserLogin) -> Token:
        row = await self._repository.get_orm_by_email(data.email)
        if row is None or not row.hashed_password:
            raise ValueError("Invalid email or password")
        if not self.verify_password(data.password, row.hashed_password):
            raise ValueError("Invalid email or password")
        if not row.is_active:
            raise ValueError("User account is inactive")

        user = self._repository._to_schema(row)
        return Token(access_token=self.create_access_token(user.id))

    async def login_with_google(self, id_token: str) -> tuple[Token, bool]:
        try:
            google_user = await verify_google_id_token(id_token)
        except GoogleAuthError as exc:
            raise ValueError(str(exc)) from exc

        user, is_new_user = await self._get_or_create_google_user(google_user)
        if not user.is_active:
            raise ValueError("User account is inactive")

        return Token(access_token=self.create_access_token(user.id), is_new_user=is_new_user), is_new_user

    async def _get_or_create_google_user(self, google_user: GoogleUserInfo) -> tuple[User, bool]:
        existing_by_google = await self._repository.get_by_google_id(google_user.google_id)
        if existing_by_google is not None:
            return existing_by_google, False

        row = await self._repository.get_orm_by_email(google_user.email)
        if row is not None:
            return await self._repository.link_google_account(str(row.id), google_user.google_id), False

        try:
            return await self._repository.create_google_user(
                email=google_user.email,
                full_name=google_user.full_name,
                google_id=google_user.google_id,
            ), True
        except UserAlreadyExistsError:
            row = await self._repository.get_orm_by_email(google_user.email)
            if row is None:
                raise
            return await self._repository.link_google_account(str(row.id), google_user.google_id), False

    async def get_user(self, user_id: str) -> User | None:
        return await self._repository.get_by_id(user_id)


