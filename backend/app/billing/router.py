from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.billing.models import (
    BillingConfigResponse,
    CostEstimate,
    EarningsSummary,
    StripeCheckoutRequest,
    StripeCheckoutResponse,
    TopUpRequest,
    TransferEarningsRequest,
    Wallet,
)
from app.billing.service import BillingService
from app.billing.stripe_service import StripeNotConfiguredError, StripeService
from app.core.config import settings
from app.core.deps import get_billing_service
from app.models.state import WorkflowType
from pydantic import BaseModel

router = APIRouter()


class EstimateRequest(BaseModel):
    workflow_type: WorkflowType = "single_agent"
    agent_id: str | None = None
    agents: list[str] | None = None
    expert_skill_id: str | None = None


@router.get("/config", response_model=BillingConfigResponse)
async def get_billing_config(
    billing: BillingService = Depends(get_billing_service),
) -> BillingConfigResponse:
    return billing.get_config()


@router.get("/wallet", response_model=Wallet)
async def get_wallet(
    current_user: User = Depends(get_current_user),
    billing: BillingService = Depends(get_billing_service),
) -> Wallet:
    return await billing.get_wallet(
        current_user.id,
        initial_balance=Decimal(str(settings.signup_credits_usd)),
    )


@router.get("/transactions")
async def list_transactions(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    billing: BillingService = Depends(get_billing_service),
):
    return await billing.list_transactions(current_user.id, limit=limit)


@router.get("/earnings", response_model=EarningsSummary)
async def get_earnings(
    current_user: User = Depends(get_current_user),
    billing: BillingService = Depends(get_billing_service),
) -> EarningsSummary:
    return await billing.get_earnings_summary(current_user.id)


@router.post("/earnings/transfer", response_model=Wallet)
async def transfer_earnings(
    payload: TransferEarningsRequest,
    current_user: User = Depends(get_current_user),
    billing: BillingService = Depends(get_billing_service),
) -> Wallet:
    try:
        return await billing.transfer_earnings(current_user.id, payload.amount_usd)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/estimate", response_model=CostEstimate)
async def estimate_cost(
    payload: EstimateRequest,
    current_user: User = Depends(get_current_user),
    billing: BillingService = Depends(get_billing_service),
) -> CostEstimate:
    return await billing.estimate_cost(
        current_user.id,
        workflow_type=payload.workflow_type,
        agent_id=payload.agent_id,
        agent_ids=payload.agents,
        expert_skill_id=payload.expert_skill_id,
        initial_balance=Decimal(str(settings.signup_credits_usd)),
    )


@router.post("/topup", response_model=Wallet)
async def top_up(
    payload: TopUpRequest,
    current_user: User = Depends(get_current_user),
    billing: BillingService = Depends(get_billing_service),
) -> Wallet:
    if not (settings.debug or not StripeService.is_configured()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Demo top-up is disabled. Use Stripe checkout instead.",
        )
    max_amount = Decimal(str(settings.billing_topup_max_usd))
    if current_user.role != "admin" and payload.amount_usd > max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum top-up amount is ${max_amount:.2f}",
        )
    return await billing.top_up(current_user.id, payload.amount_usd)


@router.post("/stripe/checkout", response_model=StripeCheckoutResponse)
async def create_stripe_checkout(
    payload: StripeCheckoutRequest,
    current_user: User = Depends(get_current_user),
    billing: BillingService = Depends(get_billing_service),
) -> StripeCheckoutResponse:
    max_amount = Decimal(str(settings.billing_topup_max_usd))
    if current_user.role != "admin" and payload.amount_usd > max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum top-up amount is ${max_amount:.2f}",
        )
    try:
        return await billing.create_stripe_checkout(
            current_user.id,
            payload.amount_usd,
            customer_email=current_user.email,
        )
    except StripeNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post("/stripe/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    billing: BillingService = Depends(get_billing_service),
):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    try:
        stripe_service = StripeService()
        event = stripe_service.construct_webhook_event(payload, signature)
    except StripeNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await billing.handle_stripe_checkout_completed(session["id"])

    return {"received": True}