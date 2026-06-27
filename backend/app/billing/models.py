from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class AgentCharge(BaseModel):
    agent_id: str
    agent_name: str
    owner_id: str
    price_usd_per_run: Decimal
    product_type: str = "agent"


class Wallet(BaseModel):
    user_id: str
    balance_usd: Decimal
    earnings_balance_usd: Decimal
    updated_at: datetime


class CostEstimate(BaseModel):
    marketplace_cost_usd: Decimal
    estimated_llm_cost_usd: Decimal = Field(default=Decimal("0"))
    estimated_total_usd: Decimal
    agent_charges: list[AgentCharge]
    current_balance_usd: Decimal
    sufficient_balance: bool


class BillingMeta(BaseModel):
    funding: str
    trial_amount_usd: Decimal = Decimal("0")
    paid_amount_usd: Decimal = Decimal("0")
    creator_payout_eligible: bool = False
    platform_tested: bool = False
    trial_notice: str | None = None
    trial_notice_en: str | None = None
    platform_notice: str | None = None
    platform_notice_en: str | None = None


class BillingTransaction(BaseModel):
    id: str
    user_id: str
    workflow_id: str | None
    transaction_type: str
    amount_usd: Decimal
    marketplace_cost_usd: Decimal
    llm_cost_usd: Decimal
    balance_after_usd: Decimal
    description: str
    agent_charges: list[dict]
    billing_meta: BillingMeta | None = None
    created_at: datetime


class TopUpRequest(BaseModel):
    amount_usd: Decimal = Field(..., gt=0, le=1000)


class StripeCheckoutRequest(BaseModel):
    amount_usd: Decimal = Field(..., gt=0, le=1000)


class StripeCheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class BillingConfigResponse(BaseModel):
    stripe_enabled: bool
    demo_topup_enabled: bool
    platform_fee_percent: float
    signup_credits_usd: float


class CreatorEarning(BaseModel):
    id: str
    creator_id: str
    buyer_id: str
    agent_id: str
    product_type: str = "agent"
    workflow_id: str
    gross_amount_usd: Decimal
    platform_fee_usd: Decimal
    net_amount_usd: Decimal
    created_at: datetime


class EarningsSummary(BaseModel):
    earnings_balance_usd: Decimal
    total_earned_usd: Decimal
    platform_fee_percent: float
    recent_earnings: list[CreatorEarning]


class TransferEarningsRequest(BaseModel):
    amount_usd: Decimal | None = Field(default=None, gt=0)


class WorkflowBilling(BaseModel):
    workflow_id: str
    marketplace_cost_usd: Decimal
    llm_cost_usd: Decimal
    total_charged_usd: Decimal
    balance_after_usd: Decimal | None = None
    charged: bool = False
    creator_payouts: list[CreatorEarning] = Field(default_factory=list)
    delivery_quality: str | None = None
    marketplace_fee_multiplier: float | None = None
    marketplace_waived_usd: Decimal | None = None
    trial_amount_usd: Decimal | None = None
    paid_amount_usd: Decimal | None = None
    creator_payout_eligible: bool | None = None
    trial_notice: str | None = None
    platform_tested: bool | None = None
    platform_notice: str | None = None