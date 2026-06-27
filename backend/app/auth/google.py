from dataclasses import dataclass

import httpx

from app.core.config import settings


class GoogleAuthError(ValueError):
    pass


@dataclass(frozen=True)
class GoogleUserInfo:
    google_id: str
    email: str
    full_name: str
    email_verified: bool


async def verify_google_id_token(id_token: str) -> GoogleUserInfo:
    client_id = settings.google_oauth_client_id
    if not client_id:
        raise GoogleAuthError("Google sign-in is not configured")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
        )

    if response.status_code != 200:
        raise GoogleAuthError("Invalid Google token")

    payload = response.json()
    if payload.get("aud") != client_id:
        raise GoogleAuthError("Google token audience mismatch")

    email_verified = str(payload.get("email_verified", "")).lower() == "true"
    if not email_verified:
        raise GoogleAuthError("Google email is not verified")

    google_id = payload.get("sub")
    email = payload.get("email")
    if not google_id or not email:
        raise GoogleAuthError("Google token is missing required fields")

    full_name = payload.get("name") or email.split("@", 1)[0]
    return GoogleUserInfo(
        google_id=str(google_id),
        email=str(email).lower(),
        full_name=str(full_name)[:120],
        email_verified=email_verified,
    )