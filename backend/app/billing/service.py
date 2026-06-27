from decimal import Decimal

from app.agents.definitions import resolve_crew
from app.graphs.utils import assess_expert_skill_delivery
from app.billing.models import (
    AgentCharge,
    BillingConfigResponse,
    CostEstimate,
    CreatorEarning,
    EarningsSummary,
    StripeCheckoutResponse,
    Wallet,
    WorkflowBilling,
)
from app.billing.stripe_service import StripeNotConfiguredError, StripeService
from app.billing.trial_credits import demo_topup_description
from app.core.config import settings
from app.models.state import WorkflowType
from app.repositories.expert_skill_repository import ExpertSkillRepository
from app.repositories.wallet_repository import InsufficientBalanceError, WalletRepository
from app.services.agent_registry import AgentRegistry


class BillingService:
    def __init__(
        self,
        wallet_repository: WalletRepository,
        agent_registry: AgentRegistry,
        expert_skill_repository: ExpertSkillRepository,
    ) -> None:
        self._wallets = wallet_repository
        self._registry = agent_registry
        self._expert_skills = expert_skill_repository

    @staticmethod
    def get_config() -> BillingConfigResponse:
        return BillingConfigResponse(
            stripe_enabled=StripeService.is_configured(),
            demo_topup_enabled=settings.debug or not StripeService.is_configured(),
            platform_fee_percent=settings.platform_fee_percent,
            signup_credits_usd=settings.signup_credits_usd,
        )

    async def get_wallet(self, user_id: str, *, initial_balance: Decimal) -> Wallet:
        return await self._wallets.get_or_create_wallet(user_id, initial_balance)

    async def top_up(self, user_id: str, amount: Decimal) -> Wallet:
        return await self._wallets.add_credits(
            user_id,
            amount,
            transaction_type="topup",
            description=demo_topup_description(amount),
        )

    async def create_stripe_checkout(
        self,
        user_id: str,
        amount: Decimal,
        *,
        customer_email: str | None = None,
    ) -> StripeCheckoutResponse:
        stripe_service = StripeService()
        session = stripe_service.create_checkout_session(
            user_id=user_id,
            amount_usd=amount,
            customer_email=customer_email,
        )
        await self._wallets.create_stripe_checkout_record(user_id, session.id, amount)
        return StripeCheckoutResponse(checkout_url=session.url, session_id=session.id)

    async def handle_stripe_checkout_completed(self, stripe_session_id: str) -> Wallet | None:
        return await self._wallets.fulfill_stripe_checkout(stripe_session_id)

    async def list_transactions(self, user_id: str, *, limit: int = 50):
        return await self._wallets.list_transactions(user_id, limit=limit)

    async def get_earnings_summary(self, user_id: str) -> EarningsSummary:
        wallet = await self.get_wallet(user_id, initial_balance=Decimal(str(settings.signup_credits_usd)))
        recent = await self._wallets.list_creator_earnings(user_id, limit=20)
        total = await self._wallets.total_creator_earnings(user_id)
        return EarningsSummary(
            earnings_balance_usd=wallet.earnings_balance_usd,
            total_earned_usd=total,
            platform_fee_percent=settings.platform_fee_percent,
            recent_earnings=recent,
        )

    async def transfer_earnings(self, user_id: str, amount: Decimal | None = None) -> Wallet:
        return await self._wallets.transfer_earnings_to_balance(user_id, amount)

    FABLE5_LOCAL_SKILL_ID = "33333333-3333-4333-8333-333333333303"
    FABLE5_PREMIUM_SKILL_ID = "33333333-3333-4333-8333-333333333304"
    IMAGE_POST_SKILL_ID = "33333333-3333-4333-8333-333333333307"

    @staticmethod
    def _estimate_llm_cost(
        workflow_type: WorkflowType,
        *,
        expert_skill_id: str | None = None,
    ) -> Decimal:
        if workflow_type == "expert_skill":
            if expert_skill_id == BillingService.FABLE5_LOCAL_SKILL_ID:
                return Decimal("0.00")
            if expert_skill_id == BillingService.FABLE5_PREMIUM_SKILL_ID:
                return Decimal("0.18")
            if expert_skill_id == BillingService.IMAGE_POST_SKILL_ID:
                return Decimal("0.17")
            return Decimal("0.12")
        if workflow_type == "multi_agent":
            return Decimal("0.08")
        return Decimal("0.03")

    async def _expert_skill_marketplace_price(
        self,
        skill,
        *,
        workflow_state: dict | None = None,
    ) -> Decimal:
        if skill.pack_slug != "custom":
            return Decimal(str(skill.price_usd_per_run))
        from app.expert_skills.model_tiers import effective_marketplace_price_usd

        tier_runtime = None
        if workflow_state:
            tier_runtime = (workflow_state.get("intermediate_results") or {}).get("model_tier_runtime")
        return effective_marketplace_price_usd(
            listed_price_usd=skill.price_usd_per_run,
            crew_config=skill.crew_config,
            tier_runtime=tier_runtime,
        )

    async def resolve_agent_charges(
        self,
        *,
        workflow_type: WorkflowType,
        agent_id: str | None,
        agent_ids: list[str] | None,
        expert_skill_id: str | None = None,
        workflow_state: dict | None = None,
    ) -> list[AgentCharge]:
        if workflow_type == "expert_skill":
            if not expert_skill_id:
                return []
            skill = await self._expert_skills.get_by_id(expert_skill_id)
            if skill is None:
                return []
            run_price = await self._expert_skill_marketplace_price(
                skill,
                workflow_state=workflow_state,
            )
            return [
                AgentCharge(
                    agent_id=skill.id,
                    agent_name=skill.name,
                    owner_id=skill.owner_id,
                    price_usd_per_run=run_price,
                    product_type="expert_skill",
                )
            ]
        if workflow_type == "single_agent":
            if not agent_id:
                return []
            agent = await self._registry.get_agent(agent_id)
            return [
                AgentCharge(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    owner_id=agent.owner_id,
                    price_usd_per_run=Decimal(str(agent.price_usd_per_run)),
                )
            ]

        if workflow_type == "multi_agent":
            crew = await resolve_crew(agent_ids, self._registry)
            charges: list[AgentCharge] = []
            for agent_def in crew:
                agent = await self._registry.get_agent(agent_def.agent_id)
                charges.append(
                    AgentCharge(
                        agent_id=agent.id,
                        agent_name=agent.name,
                        owner_id=agent.owner_id,
                        price_usd_per_run=Decimal(str(agent.price_usd_per_run)),
                    )
                )
            return charges

        return []

    async def estimate_cost(
        self,
        user_id: str,
        *,
        workflow_type: WorkflowType,
        agent_id: str | None,
        agent_ids: list[str] | None,
        expert_skill_id: str | None = None,
        initial_balance: Decimal,
    ) -> CostEstimate:
        wallet = await self.get_wallet(user_id, initial_balance=initial_balance)
        charges = await self.resolve_agent_charges(
            workflow_type=workflow_type,
            agent_id=agent_id,
            agent_ids=agent_ids,
            expert_skill_id=expert_skill_id,
        )
        marketplace_cost = sum((charge.price_usd_per_run for charge in charges), Decimal("0"))
        llm_estimate = self._estimate_llm_cost(workflow_type, expert_skill_id=expert_skill_id)
        return CostEstimate(
            marketplace_cost_usd=marketplace_cost,
            estimated_llm_cost_usd=llm_estimate,
            estimated_total_usd=marketplace_cost + llm_estimate,
            agent_charges=charges,
            current_balance_usd=wallet.balance_usd,
            sufficient_balance=wallet.balance_usd >= marketplace_cost,
        )

    async def ensure_sufficient_balance(
        self,
        user_id: str,
        *,
        workflow_type: WorkflowType,
        agent_id: str | None,
        agent_ids: list[str] | None,
        expert_skill_id: str | None = None,
        initial_balance: Decimal,
    ) -> CostEstimate:
        estimate = await self.estimate_cost(
            user_id,
            workflow_type=workflow_type,
            agent_id=agent_id,
            agent_ids=agent_ids,
            expert_skill_id=expert_skill_id,
            initial_balance=initial_balance,
        )
        if not estimate.sufficient_balance:
            raise InsufficientBalanceError(
                "Insufficient balance for agent fees. "
                f"Need at least ${estimate.marketplace_cost_usd:.4f}, "
                f"have ${estimate.current_balance_usd:.4f}. "
                "LLM usage is billed additionally when the workflow completes."
            )
        return estimate

    async def _expert_skill_delivery_meta(self, state: dict) -> dict:
        if state.get("workflow_type") != "expert_skill":
            return {}
        intermediate = state.get("intermediate_results") or {}
        if intermediate.get("delivery_quality"):
            return {
                "delivery_quality": intermediate.get("delivery_quality"),
                "marketplace_fee_multiplier": intermediate.get("marketplace_fee_multiplier"),
            }
        crew_steps = None
        expert_skill_id = (state.get("task_context") or {}).get("expert_skill_id")
        if expert_skill_id:
            skill = await self._expert_skills.get_by_id(expert_skill_id)
            if skill is not None:
                crew_steps = (skill.crew_config or {}).get("steps")
        assessment = assess_expert_skill_delivery(state, crew_steps=crew_steps)
        return {
            "delivery_quality": assessment["delivery_quality"],
            "marketplace_fee_multiplier": float(assessment["marketplace_fee_multiplier"]),
        }

    async def settle_workflow(self, state: dict, *, initial_balance: Decimal) -> WorkflowBilling | None:
        workflow_id = state.get("workflow_id")
        user_id = state.get("user_id")
        status = state.get("status")
        if not workflow_id or not user_id:
            return None

        if status == "waiting_human":
            return WorkflowBilling(
                workflow_id=workflow_id,
                marketplace_cost_usd=Decimal("0"),
                llm_cost_usd=Decimal("0"),
                total_charged_usd=Decimal("0"),
                charged=False,
            )

        if status not in {"completed", "failed"}:
            return None

        if await self._wallets.is_workflow_charged(workflow_id):
            delivery_meta = await self._expert_skill_delivery_meta(state)
            return WorkflowBilling(
                workflow_id=workflow_id,
                marketplace_cost_usd=Decimal("0"),
                llm_cost_usd=Decimal("0"),
                total_charged_usd=Decimal("0"),
                charged=True,
                delivery_quality=delivery_meta.get("delivery_quality"),
                marketplace_fee_multiplier=delivery_meta.get("marketplace_fee_multiplier"),
            )

        await self.get_wallet(user_id, initial_balance=initial_balance)
        task_context = state.get("task_context") or {}
        charges = await self.resolve_agent_charges(
            workflow_type=state.get("workflow_type", "single_agent"),
            agent_id=state.get("agent_id"),
            agent_ids=task_context.get("agents"),
            expert_skill_id=task_context.get("expert_skill_id"),
            workflow_state=state,
        )
        full_marketplace_cost = sum((charge.price_usd_per_run for charge in charges), Decimal("0"))
        llm_cost = Decimal(str(state.get("total_cost_usd") or 0))
        platform_fee = Decimal(str(settings.platform_fee_percent))

        delivery_quality: str | None = None
        fee_multiplier = Decimal("1")
        marketplace_waived = Decimal("0")
        if state.get("workflow_type") == "expert_skill":
            intermediate = state.get("intermediate_results") or {}
            if intermediate.get("marketplace_fee_multiplier") is not None:
                fee_multiplier = Decimal(str(intermediate["marketplace_fee_multiplier"]))
                delivery_quality = intermediate.get("delivery_quality")
            else:
                crew_steps = None
                expert_skill_id = (state.get("task_context") or {}).get("expert_skill_id")
                if expert_skill_id:
                    skill = await self._expert_skills.get_by_id(expert_skill_id)
                    if skill is not None:
                        crew_steps = (skill.crew_config or {}).get("steps")
                assessment = assess_expert_skill_delivery(state, crew_steps=crew_steps)
                fee_multiplier = Decimal(str(assessment["marketplace_fee_multiplier"]))
                delivery_quality = assessment["delivery_quality"]

        marketplace_cost = (full_marketplace_cost * fee_multiplier).quantize(Decimal("0.0001"))
        marketplace_waived = (full_marketplace_cost - marketplace_cost).quantize(Decimal("0.0001"))

        scaled_charges = [
            {
                **charge.model_dump(mode="json"),
                "price_usd_per_run": str(
                    (charge.price_usd_per_run * fee_multiplier).quantize(Decimal("0.0001"))
                ),
            }
            for charge in charges
        ]

        try:
            tx, payouts = await self._wallets.charge_workflow(
                user_id=user_id,
                workflow_id=workflow_id,
                marketplace_cost=marketplace_cost,
                llm_cost=llm_cost,
                agent_charges=scaled_charges,
                platform_fee_percent=platform_fee,
            )
        except InsufficientBalanceError:
            raise

        billing_meta = tx.billing_meta
        return WorkflowBilling(
            workflow_id=workflow_id,
            marketplace_cost_usd=marketplace_cost,
            llm_cost_usd=llm_cost,
            total_charged_usd=marketplace_cost + llm_cost,
            balance_after_usd=tx.balance_after_usd,
            charged=True,
            creator_payouts=payouts,
            delivery_quality=delivery_quality,
            marketplace_fee_multiplier=float(fee_multiplier),
            marketplace_waived_usd=marketplace_waived if marketplace_waived > 0 else None,
            trial_amount_usd=billing_meta.trial_amount_usd if billing_meta else None,
            paid_amount_usd=billing_meta.paid_amount_usd if billing_meta else None,
            creator_payout_eligible=billing_meta.creator_payout_eligible if billing_meta else None,
            trial_notice=billing_meta.trial_notice if billing_meta else None,
            platform_tested=billing_meta.platform_tested if billing_meta else None,
            platform_notice=billing_meta.platform_notice if billing_meta else None,
        )