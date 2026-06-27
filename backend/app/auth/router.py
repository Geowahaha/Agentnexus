from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.models import GoogleAuthRequest, Token, User, UserCreate, UserLogin
from app.auth.service import AuthService
from decimal import Decimal

from app.core.config import settings
from app.core.deps import get_auth_service, get_billing_service
from app.billing.service import BillingService
from app.repositories.user_repository import UserAlreadyExistsError

router = APIRouter()


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
    billing: BillingService = Depends(get_billing_service),
) -> User:
    try:
        user = await auth_service.register(payload)
        await billing.get_wallet(user.id, initial_balance=Decimal(str(settings.signup_credits_usd)))
        return user
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login", response_model=Token)
async def login(
    payload: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    try:
        return await auth_service.login(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/google", response_model=Token)
async def google_auth(
    payload: GoogleAuthRequest,
    auth_service: AuthService = Depends(get_auth_service),
    billing: BillingService = Depends(get_billing_service),
) -> Token:
    try:
        token, is_new_user = await auth_service.login_with_google(payload.id_token)
        if is_new_user:
            user_id = auth_service.decode_access_token(token.access_token)
            if user_id:
                await billing.get_wallet(user_id, initial_balance=Decimal(str(settings.signup_credits_usd)))
        return token
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user