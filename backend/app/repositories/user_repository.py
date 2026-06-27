from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserCreate
from app.db.models.user import UserORM


class UserAlreadyExistsError(ValueError):
    pass


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_schema(row: UserORM) -> User:
        return User(
            id=str(row.id),
            email=row.email,
            full_name=row.full_name,
            role=row.role,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def create(self, data: UserCreate, hashed_password: str) -> User:
        existing = await self.get_by_email(data.email)
        if existing is not None:
            raise UserAlreadyExistsError(f"Email '{data.email}' is already registered")

        now = datetime.now(timezone.utc)
        row = UserORM(
            id=uuid4(),
            email=data.email.lower(),
            hashed_password=hashed_password,
            auth_provider="local",
            full_name=data.full_name,
            role="user",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_schema(row)

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self._session.execute(select(UserORM).where(UserORM.id == UUID(user_id)))
        row = result.scalar_one_or_none()
        return self._to_schema(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserORM).where(UserORM.email == email.lower())
        )
        row = result.scalar_one_or_none()
        return self._to_schema(row) if row else None

    async def get_orm_by_email(self, email: str) -> UserORM | None:
        result = await self._session.execute(
            select(UserORM).where(UserORM.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_orm_by_id(self, user_id: str) -> UserORM | None:
        result = await self._session.execute(select(UserORM).where(UserORM.id == UUID(user_id)))
        return result.scalar_one_or_none()

    async def get_full_name_by_id(self, user_id: str) -> str | None:
        row = await self.get_orm_by_id(user_id)
        return row.full_name if row is not None else None

    async def get_by_google_id(self, google_id: str) -> User | None:
        result = await self._session.execute(select(UserORM).where(UserORM.google_id == google_id))
        row = result.scalar_one_or_none()
        return self._to_schema(row) if row else None

    async def get_orm_by_google_id(self, google_id: str) -> UserORM | None:
        result = await self._session.execute(select(UserORM).where(UserORM.google_id == google_id))
        return result.scalar_one_or_none()

    async def create_google_user(self, *, email: str, full_name: str, google_id: str) -> User:
        existing = await self.get_by_email(email)
        if existing is not None:
            raise UserAlreadyExistsError(f"Email '{email}' is already registered")

        now = datetime.now(timezone.utc)
        row = UserORM(
            id=uuid4(),
            email=email.lower(),
            hashed_password=None,
            google_id=google_id,
            auth_provider="google",
            full_name=full_name,
            role="user",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_schema(row)

    async def link_google_account(self, user_id: str, google_id: str) -> User:
        row = await self.get_orm_by_id(user_id)
        if row is None:
            raise ValueError("User not found")

        existing = await self.get_orm_by_google_id(google_id)
        if existing is not None and str(existing.id) != user_id:
            raise UserAlreadyExistsError("This Google account is linked to another user")

        row.google_id = google_id
        if row.auth_provider == "local":
            row.auth_provider = "local"
        row.updated_at = datetime.now(timezone.utc)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_schema(row)