import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.bridge_device import BridgeAuditEventORM, BridgeDeviceORM, BridgePairingCodeORM


def hash_device_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_pairing_code() -> str:
    alphabet = string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


def generate_device_token() -> str:
    return secrets.token_urlsafe(32)


class BridgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_pairing_code(self, user_id: str, *, ttl_minutes: int = 30) -> tuple[str, datetime]:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=ttl_minutes)
        for _ in range(8):
            code = generate_pairing_code()
            existing = await self._session.execute(
                select(BridgePairingCodeORM.id).where(BridgePairingCodeORM.code == code)
            )
            if existing.scalar_one_or_none() is None:
                row = BridgePairingCodeORM(
                    id=uuid4(),
                    user_id=UUID(user_id),
                    code=code,
                    expires_at=expires_at,
                    created_at=now,
                )
                self._session.add(row)
                await self._session.commit()
                return code, expires_at
        raise RuntimeError("Could not allocate pairing code")

    async def create_device_for_user(
        self,
        *,
        user_id: str,
        device_name: str,
        allowed_roots: list[str] | None = None,
        capabilities: list[str] | None = None,
        solution_context: str | None = None,
    ) -> tuple[BridgeDeviceORM, str]:
        now = datetime.now(timezone.utc)
        device_token = generate_device_token()
        device = BridgeDeviceORM(
            id=uuid4(),
            user_id=UUID(user_id),
            device_name=device_name.strip() or "My device",
            token_hash=hash_device_token(device_token),
            capabilities=capabilities or ["read"],
            allowed_roots=allowed_roots or [],
            solution_context=solution_context,
            status="active",
            last_seen_at=now,
            created_at=now,
        )
        self._session.add(device)
        await self._session.commit()
        await self._session.refresh(device)
        return device, device_token

    async def pair_device(
        self,
        *,
        code: str,
        device_name: str,
        allowed_roots: list[str] | None = None,
        capabilities: list[str] | None = None,
        solution_context: str | None = None,
    ) -> tuple[BridgeDeviceORM, str]:
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            select(BridgePairingCodeORM).where(BridgePairingCodeORM.code == code)
        )
        pairing = result.scalar_one_or_none()
        if pairing is None:
            raise KeyError("Invalid pairing code")
        if pairing.used_at is not None:
            raise ValueError("Pairing code already used")
        if pairing.expires_at < now:
            raise ValueError("Pairing code expired")

        device_token = generate_device_token()
        device = BridgeDeviceORM(
            id=uuid4(),
            user_id=pairing.user_id,
            device_name=device_name.strip() or "My device",
            token_hash=hash_device_token(device_token),
            capabilities=capabilities or ["read"],
            allowed_roots=allowed_roots or [],
            solution_context=solution_context,
            status="active",
            last_seen_at=now,
            created_at=now,
        )
        pairing.used_at = now
        pairing.device_id = device.id
        self._session.add(device)
        await self._session.commit()
        await self._session.refresh(device)
        return device, device_token

    async def get_device_by_token(self, device_token: str) -> BridgeDeviceORM | None:
        token_hash = hash_device_token(device_token)
        result = await self._session.execute(
            select(BridgeDeviceORM).where(
                BridgeDeviceORM.token_hash == token_hash,
                BridgeDeviceORM.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def touch_device(self, device_id: UUID) -> None:
        now = datetime.now(timezone.utc)
        await self._session.execute(
            update(BridgeDeviceORM)
            .where(BridgeDeviceORM.id == device_id)
            .values(last_seen_at=now)
        )
        await self._session.commit()

    async def list_devices(self, user_id: str) -> list[BridgeDeviceORM]:
        result = await self._session.execute(
            select(BridgeDeviceORM)
            .where(BridgeDeviceORM.user_id == UUID(user_id), BridgeDeviceORM.status == "active")
            .order_by(BridgeDeviceORM.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_device_for_user(self, user_id: str, device_id: str) -> BridgeDeviceORM | None:
        result = await self._session.execute(
            select(BridgeDeviceORM).where(
                BridgeDeviceORM.id == UUID(device_id),
                BridgeDeviceORM.user_id == UUID(user_id),
                BridgeDeviceORM.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def revoke_device(self, user_id: str, device_id: str) -> bool:
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            update(BridgeDeviceORM)
            .where(
                BridgeDeviceORM.id == UUID(device_id),
                BridgeDeviceORM.user_id == UUID(user_id),
                BridgeDeviceORM.status == "active",
            )
            .values(status="revoked", revoked_at=now)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def log_audit(
        self,
        *,
        user_id: str,
        device_id: str | None,
        tool_name: str,
        args: dict,
        ok: bool,
        error_message: str | None = None,
    ) -> None:
        row = BridgeAuditEventORM(
            id=uuid4(),
            user_id=UUID(user_id),
            device_id=UUID(device_id) if device_id else None,
            tool_name=tool_name,
            args=args,
            ok=ok,
            error_message=error_message,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(row)
        await self._session.commit()