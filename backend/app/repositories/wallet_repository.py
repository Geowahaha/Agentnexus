from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.models import BillingMeta, BillingTransaction, CreatorEarning, Wallet
from app.billing.platform_admin import (
    build_platform_test_billing_meta,
    is_platform_admin_user,
    platform_test_charge_description,
)
from app.billing.trial_credits import (
    build_billing_meta,
    demo_topup_description,
    signup_bonus_description,
    split_agent_charges,
    workflow_charge_description,
)
from app.db.models.billing_transaction import BillingTransactionORM, WorkflowChargeORM
from app.db.models.creator_earning import CreatorEarningORM
from app.db.models.stripe_checkout import StripeCheckoutSessionORM
from app.db.models.user import SYSTEM_USER_ID, UserORM
from app.db.models.wallet import WalletORM


class InsufficientBalanceError(ValueError):
    pass


DEMO_CREDIT_TYPES = frozenset({"signup_bonus", "demo_topup", "topup"})
PAID_CREDIT_TYPES = frozenset({"stripe_topup", "earnings_transfer"})


class WalletRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _wallet_to_schema(row: WalletORM) -> Wallet:
        return Wallet(
            user_id=str(row.user_id),
            balance_usd=Decimal(str(row.balance_usd)),
            earnings_balance_usd=Decimal(str(row.earnings_balance_usd)),
            updated_at=row.updated_at,
        )

    @staticmethod
    def _billing_meta_to_schema(meta: dict | None) -> BillingMeta | None:
        if not meta:
            return None
        return BillingMeta(
            funding=str(meta.get("funding") or "paid"),
            trial_amount_usd=Decimal(str(meta.get("trial_amount_usd") or 0)),
            paid_amount_usd=Decimal(str(meta.get("paid_amount_usd") or 0)),
            creator_payout_eligible=bool(meta.get("creator_payout_eligible")),
            platform_tested=bool(meta.get("platform_tested")),
            trial_notice=meta.get("trial_notice"),
            trial_notice_en=meta.get("trial_notice_en"),
            platform_notice=meta.get("platform_notice"),
            platform_notice_en=meta.get("platform_notice_en"),
        )

    @staticmethod
    def _transaction_to_schema(row: BillingTransactionORM) -> BillingTransaction:
        agent_items, billing_meta = split_agent_charges(list(row.agent_charges or []))
        return BillingTransaction(
            id=str(row.id),
            user_id=str(row.user_id),
            workflow_id=row.workflow_id,
            transaction_type=row.transaction_type,
            amount_usd=Decimal(str(row.amount_usd)),
            marketplace_cost_usd=Decimal(str(row.marketplace_cost_usd)),
            llm_cost_usd=Decimal(str(row.llm_cost_usd)),
            balance_after_usd=Decimal(str(row.balance_after_usd)),
            description=row.description,
            agent_charges=agent_items,
            billing_meta=WalletRepository._billing_meta_to_schema(billing_meta),
            created_at=row.created_at,
        )

    @staticmethod
    def _earning_to_schema(row: CreatorEarningORM) -> CreatorEarning:
        return CreatorEarning(
            id=str(row.id),
            creator_id=str(row.creator_id),
            buyer_id=str(row.buyer_id),
            agent_id=str(row.agent_id),
            product_type=row.product_type,
            workflow_id=row.workflow_id,
            gross_amount_usd=Decimal(str(row.gross_amount_usd)),
            platform_fee_usd=Decimal(str(row.platform_fee_usd)),
            net_amount_usd=Decimal(str(row.net_amount_usd)),
            created_at=row.created_at,
        )

    async def get_wallet(self, user_id: str) -> Wallet | None:
        result = await self._session.execute(
            select(WalletORM).where(WalletORM.user_id == UUID(user_id))
        )
        row = result.scalar_one_or_none()
        return self._wallet_to_schema(row) if row else None

    async def create_wallet(self, user_id: str, initial_balance: Decimal) -> Wallet:
        now = datetime.now(timezone.utc)
        row = WalletORM(
            id=uuid4(),
            user_id=UUID(user_id),
            balance_usd=initial_balance,
            earnings_balance_usd=Decimal("0"),
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        if initial_balance > 0:
            self._session.add(
                BillingTransactionORM(
                    id=uuid4(),
                    user_id=UUID(user_id),
                    workflow_id=None,
                    transaction_type="signup_bonus",
                    amount_usd=initial_balance,
                    marketplace_cost_usd=Decimal("0"),
                    llm_cost_usd=Decimal("0"),
                    balance_after_usd=initial_balance,
                    description=signup_bonus_description(initial_balance),
                    agent_charges=[],
                    created_at=now,
                )
            )
        await self._session.commit()
        await self._session.refresh(row)
        return self._wallet_to_schema(row)

    async def get_or_create_wallet(self, user_id: str, initial_balance: Decimal) -> Wallet:
        wallet = await self.get_wallet(user_id)
        if wallet is not None:
            return wallet
        return await self.create_wallet(user_id, initial_balance)

    async def add_credits(
        self,
        user_id: str,
        amount: Decimal,
        *,
        transaction_type: str,
        description: str,
    ) -> Wallet:
        wallet_row = await self._get_wallet_row_for_update(user_id)
        new_balance = Decimal(str(wallet_row.balance_usd)) + amount
        wallet_row.balance_usd = new_balance
        wallet_row.updated_at = datetime.now(timezone.utc)
        self._session.add(
            BillingTransactionORM(
                id=uuid4(),
                user_id=UUID(user_id),
                workflow_id=None,
                transaction_type=transaction_type,
                amount_usd=amount,
                marketplace_cost_usd=Decimal("0"),
                llm_cost_usd=Decimal("0"),
                balance_after_usd=new_balance,
                description=description,
                agent_charges=[],
                created_at=datetime.now(timezone.utc),
            )
        )
        await self._session.commit()
        await self._session.refresh(wallet_row)
        return self._wallet_to_schema(wallet_row)

    async def create_stripe_checkout_record(
        self,
        user_id: str,
        stripe_session_id: str,
        amount_usd: Decimal,
    ) -> StripeCheckoutSessionORM:
        row = StripeCheckoutSessionORM(
            id=uuid4(),
            user_id=UUID(user_id),
            stripe_session_id=stripe_session_id,
            amount_usd=amount_usd,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def get_stripe_checkout_by_session_id(self, stripe_session_id: str) -> StripeCheckoutSessionORM | None:
        result = await self._session.execute(
            select(StripeCheckoutSessionORM).where(
                StripeCheckoutSessionORM.stripe_session_id == stripe_session_id
            )
        )
        return result.scalar_one_or_none()

    async def fulfill_stripe_checkout(self, stripe_session_id: str) -> Wallet | None:
        result = await self._session.execute(
            select(StripeCheckoutSessionORM)
            .where(StripeCheckoutSessionORM.stripe_session_id == stripe_session_id)
            .with_for_update()
        )
        checkout = result.scalar_one_or_none()
        if checkout is None or checkout.status == "completed":
            return None

        user_id = str(checkout.user_id)
        amount = Decimal(str(checkout.amount_usd))
        wallet_row = await self._get_wallet_row_for_update(user_id)
        new_balance = Decimal(str(wallet_row.balance_usd)) + amount
        now = datetime.now(timezone.utc)
        wallet_row.balance_usd = new_balance
        wallet_row.updated_at = now
        checkout.status = "completed"
        checkout.completed_at = now

        self._session.add(
            BillingTransactionORM(
                id=uuid4(),
                user_id=checkout.user_id,
                workflow_id=None,
                transaction_type="stripe_topup",
                amount_usd=amount,
                marketplace_cost_usd=Decimal("0"),
                llm_cost_usd=Decimal("0"),
                balance_after_usd=new_balance,
                description=f"Stripe payment {stripe_session_id}",
                agent_charges=[],
                created_at=now,
            )
        )
        await self._session.commit()
        await self._session.refresh(wallet_row)
        return self._wallet_to_schema(wallet_row)

    async def is_workflow_charged(self, workflow_id: str) -> bool:
        result = await self._session.execute(
            select(WorkflowChargeORM.id).where(WorkflowChargeORM.workflow_id == workflow_id)
        )
        return result.scalar_one_or_none() is not None

    async def charge_workflow(
        self,
        *,
        user_id: str,
        workflow_id: str,
        marketplace_cost: Decimal,
        llm_cost: Decimal,
        agent_charges: list[dict],
        platform_fee_percent: Decimal,
    ) -> tuple[BillingTransaction, list[CreatorEarning]]:
        if await self.is_workflow_charged(workflow_id):
            raise ValueError(f"Workflow '{workflow_id}' already charged")

        total = marketplace_cost + llm_cost
        wallet_row = await self._get_wallet_row_for_update(user_id)
        current_balance = Decimal(str(wallet_row.balance_usd))
        if current_balance < total:
            raise InsufficientBalanceError(
                f"Insufficient balance. Need ${total:.4f}, have ${current_balance:.4f}"
            )

        platform_test = await self._is_platform_admin_user(user_id)
        demo_remaining, paid_remaining = await self._compute_funding_pools(user_id)
        trial_spend = min(demo_remaining, total)
        paid_spend = total - trial_spend
        if platform_test:
            paid_fraction = Decimal("0")
            creator_payout_eligible = False
            billing_meta = build_platform_test_billing_meta(
                trial_spend=trial_spend,
                paid_spend=paid_spend,
            )
            charge_description = platform_test_charge_description(workflow_id)
        else:
            if marketplace_cost > 0:
                paid_marketplace = max(Decimal("0"), marketplace_cost - demo_remaining)
                paid_marketplace = min(paid_marketplace, paid_remaining)
                paid_fraction = (paid_marketplace / marketplace_cost).quantize(Decimal("0.0001"))
            else:
                paid_fraction = Decimal("0")
            creator_payout_eligible = paid_fraction > 0
            billing_meta = build_billing_meta(
                trial_spend=trial_spend,
                paid_spend=paid_spend,
                creator_payout_eligible=creator_payout_eligible,
            )
            charge_description = workflow_charge_description(
                workflow_id,
                trial_spend=trial_spend,
                paid_spend=paid_spend,
            )

        new_balance = current_balance - total
        now = datetime.now(timezone.utc)
        wallet_row.balance_usd = new_balance
        wallet_row.updated_at = now

        stored_charges = [*agent_charges, billing_meta]

        tx = BillingTransactionORM(
            id=uuid4(),
            user_id=UUID(user_id),
            workflow_id=workflow_id,
            transaction_type="workflow_charge",
            amount_usd=-total,
            marketplace_cost_usd=marketplace_cost,
            llm_cost_usd=llm_cost,
            balance_after_usd=new_balance,
            description=charge_description,
            agent_charges=stored_charges,
            created_at=now,
        )
        charge = WorkflowChargeORM(
            id=uuid4(),
            workflow_id=workflow_id,
            user_id=UUID(user_id),
            marketplace_cost_usd=marketplace_cost,
            llm_cost_usd=llm_cost,
            total_cost_usd=total,
            created_at=now,
        )
        self._session.add(tx)
        self._session.add(charge)

        payouts = await self._distribute_creator_earnings(
            buyer_id=user_id,
            workflow_id=workflow_id,
            agent_charges=agent_charges,
            platform_fee_percent=platform_fee_percent,
            paid_fraction=paid_fraction,
            now=now,
        )
        await self._session.commit()
        await self._session.refresh(tx)
        return self._transaction_to_schema(tx), payouts

    async def _is_platform_admin_user(self, user_id: str) -> bool:
        result = await self._session.execute(
            select(UserORM.email, UserORM.role).where(UserORM.id == UUID(user_id))
        )
        row = result.first()
        if row is None:
            return False
        email, role = row
        return is_platform_admin_user(email=email, role=role)

    async def _compute_funding_pools(self, user_id: str) -> tuple[Decimal, Decimal]:
        """Return demo and paid credit pools remaining (FIFO spend: demo first)."""
        result = await self._session.execute(
            select(BillingTransactionORM)
            .where(BillingTransactionORM.user_id == UUID(user_id))
            .order_by(BillingTransactionORM.created_at.asc())
        )
        demo = Decimal("0")
        paid = Decimal("0")
        for row in result.scalars().all():
            amount = Decimal(str(row.amount_usd))
            ttype = row.transaction_type
            if ttype in DEMO_CREDIT_TYPES:
                demo += amount
            elif ttype in PAID_CREDIT_TYPES:
                paid += amount
            elif ttype == "workflow_charge":
                spend = -amount
                from_demo = min(demo, spend)
                demo -= from_demo
                spend -= from_demo
                if spend > 0:
                    paid -= min(paid, spend)
        return demo, paid

    async def _distribute_creator_earnings(
        self,
        *,
        buyer_id: str,
        workflow_id: str,
        agent_charges: list[dict],
        platform_fee_percent: Decimal,
        paid_fraction: Decimal,
        now: datetime,
    ) -> list[CreatorEarning]:
        payouts: list[CreatorEarning] = []
        if paid_fraction <= 0:
            return payouts

        fee_rate = platform_fee_percent / Decimal("100")
        buyer_uuid = UUID(buyer_id)

        for item in agent_charges:
            creator_id = item.get("owner_id")
            if not creator_id:
                continue
            creator_uuid = UUID(creator_id)
            if creator_uuid == buyer_uuid or creator_uuid == SYSTEM_USER_ID:
                continue

            gross = (
                Decimal(str(item.get("price_usd_per_run", 0))) * paid_fraction
            ).quantize(Decimal("0.0001"))
            if gross <= 0:
                continue

            platform_fee = (gross * fee_rate).quantize(Decimal("0.0001"))
            net = gross - platform_fee

            creator_wallet = await self._get_or_create_wallet_row_for_update(creator_id)
            creator_wallet.earnings_balance_usd = Decimal(str(creator_wallet.earnings_balance_usd)) + net
            creator_wallet.updated_at = now

            earning_row = CreatorEarningORM(
                id=uuid4(),
                creator_id=creator_uuid,
                buyer_id=buyer_uuid,
                agent_id=UUID(item["agent_id"]),
                product_type=str(item.get("product_type") or "agent"),
                workflow_id=workflow_id,
                gross_amount_usd=gross,
                platform_fee_usd=platform_fee,
                net_amount_usd=net,
                created_at=now,
            )
            self._session.add(earning_row)
            payouts.append(self._earning_to_schema(earning_row))

        return payouts

    async def transfer_earnings_to_balance(
        self,
        user_id: str,
        amount: Decimal | None = None,
    ) -> Wallet:
        wallet_row = await self._get_wallet_row_for_update(user_id)
        available = Decimal(str(wallet_row.earnings_balance_usd))
        if available <= 0:
            raise InsufficientBalanceError("No earnings available to transfer")

        transfer_amount = amount if amount is not None else available
        if transfer_amount > available:
            raise InsufficientBalanceError(
                f"Cannot transfer ${transfer_amount:.4f}; only ${available:.4f} in earnings"
            )

        now = datetime.now(timezone.utc)
        wallet_row.earnings_balance_usd = available - transfer_amount
        wallet_row.balance_usd = Decimal(str(wallet_row.balance_usd)) + transfer_amount
        wallet_row.updated_at = now

        self._session.add(
            BillingTransactionORM(
                id=uuid4(),
                user_id=UUID(user_id),
                workflow_id=None,
                transaction_type="earnings_transfer",
                amount_usd=transfer_amount,
                marketplace_cost_usd=Decimal("0"),
                llm_cost_usd=Decimal("0"),
                balance_after_usd=wallet_row.balance_usd,
                description=f"Transferred ${transfer_amount:.4f} from creator earnings",
                agent_charges=[],
                created_at=now,
            )
        )
        await self._session.commit()
        await self._session.refresh(wallet_row)
        return self._wallet_to_schema(wallet_row)

    async def list_creator_earnings(self, creator_id: str, *, limit: int = 50) -> list[CreatorEarning]:
        result = await self._session.execute(
            select(CreatorEarningORM)
            .where(CreatorEarningORM.creator_id == UUID(creator_id))
            .order_by(CreatorEarningORM.created_at.desc())
            .limit(limit)
        )
        return [self._earning_to_schema(row) for row in result.scalars().all()]

    async def total_creator_earnings(self, creator_id: str) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(CreatorEarningORM.net_amount_usd), 0)).where(
                CreatorEarningORM.creator_id == UUID(creator_id)
            )
        )
        return Decimal(str(result.scalar_one()))

    async def list_transactions(self, user_id: str, *, limit: int = 50) -> list[BillingTransaction]:
        result = await self._session.execute(
            select(BillingTransactionORM)
            .where(BillingTransactionORM.user_id == UUID(user_id))
            .order_by(BillingTransactionORM.created_at.desc())
            .limit(limit)
        )
        return [self._transaction_to_schema(row) for row in result.scalars().all()]

    async def _get_wallet_row_for_update(self, user_id: str) -> WalletORM:
        result = await self._session.execute(
            select(WalletORM).where(WalletORM.user_id == UUID(user_id)).with_for_update()
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"Wallet not found for user '{user_id}'")
        return row

    async def _get_or_create_wallet_row_for_update(self, user_id: str) -> WalletORM:
        result = await self._session.execute(
            select(WalletORM).where(WalletORM.user_id == UUID(user_id)).with_for_update()
        )
        row = result.scalar_one_or_none()
        if row is not None:
            return row

        now = datetime.now(timezone.utc)
        row = WalletORM(
            id=uuid4(),
            user_id=UUID(user_id),
            balance_usd=Decimal("0"),
            earnings_balance_usd=Decimal("0"),
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.flush()
        return row