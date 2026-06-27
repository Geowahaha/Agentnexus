from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from decimal import Decimal

from app.auth.service import AuthService
from app.billing.service import BillingService
from app.core.config import settings
from app.core.checkpoint import get_checkpointer
from app.core.database import get_session
from app.core.llm import get_llm_factory
from app.repositories.agent_repository import AgentRepository
from app.repositories.expert_skill_repository import ExpertSkillRepository
from app.repositories.showcase_repository import ShowcaseRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.repositories.wallet_repository import WalletRepository
from app.repositories.user_repository import UserRepository
from app.repositories.creator_repository import CreatorRepository
from app.repositories.buyer_review_repository import BuyerReviewRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.review_inbox_repository import ReviewInboxRepository
from app.services.review_attachment_service import ReviewAttachmentService
from app.repositories.custom_tool_repository import CustomToolRepository
from app.repositories.bridge_repository import BridgeRepository
from app.repositories.smart_farm_repository import SmartFarmRepository
from app.repositories.mcp_server_repository import MCPServerRepository
from app.services.agent_registry import AgentRegistry
from app.services.mcp_service import MCPService
from app.services.portfolio_service import PortfolioService
from app.services.bridge_service import BridgeService
from app.services.tool_resolver import ToolResolver
from app.services.smart_farm_service import SmartFarmService
from app.services.workflow_service import WorkflowService


async def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(session)


async def get_auth_service(
    repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(repository)


async def get_wallet_repository(
    session: AsyncSession = Depends(get_session),
) -> WalletRepository:
    return WalletRepository(session)


async def get_agent_repository(
    session: AsyncSession = Depends(get_session),
) -> AgentRepository:
    return AgentRepository(session)


async def get_expert_skill_repository(
    session: AsyncSession = Depends(get_session),
) -> ExpertSkillRepository:
    return ExpertSkillRepository(session)


async def get_showcase_repository(
    session: AsyncSession = Depends(get_session),
) -> ShowcaseRepository:
    return ShowcaseRepository(session)


async def get_showcase_service(
    repository: ShowcaseRepository = Depends(get_showcase_repository),
):
    from app.services.showcase_service import ShowcaseService

    return ShowcaseService(repository)


async def get_portfolio_repository(
    session: AsyncSession = Depends(get_session),
) -> PortfolioRepository:
    return PortfolioRepository(session)


async def get_review_inbox_repository(
    session: AsyncSession = Depends(get_session),
) -> ReviewInboxRepository:
    return ReviewInboxRepository(session)


async def get_buyer_review_repository(
    session: AsyncSession = Depends(get_session),
) -> BuyerReviewRepository:
    return BuyerReviewRepository(session)


async def get_notification_repository(
    session: AsyncSession = Depends(get_session),
) -> NotificationRepository:
    return NotificationRepository(session)


def get_review_attachment_service() -> ReviewAttachmentService:
    return ReviewAttachmentService()


async def get_creator_repository(
    session: AsyncSession = Depends(get_session),
) -> CreatorRepository:
    return CreatorRepository(session)


async def get_custom_tool_repository(
    session: AsyncSession = Depends(get_session),
) -> CustomToolRepository:
    return CustomToolRepository(session)


async def get_mcp_server_repository(
    session: AsyncSession = Depends(get_session),
) -> MCPServerRepository:
    return MCPServerRepository(session)


async def get_mcp_service(
    repository: MCPServerRepository = Depends(get_mcp_server_repository),
) -> MCPService:
    return MCPService(repository)


async def get_bridge_repository(
    session: AsyncSession = Depends(get_session),
) -> BridgeRepository:
    return BridgeRepository(session)


async def get_bridge_service(
    repository: BridgeRepository = Depends(get_bridge_repository),
) -> BridgeService:
    return BridgeService(repository)


async def get_tool_resolver(
    custom_tool_repository: CustomToolRepository = Depends(get_custom_tool_repository),
    mcp_server_repository: MCPServerRepository = Depends(get_mcp_server_repository),
    mcp_service: MCPService = Depends(get_mcp_service),
    bridge_service: BridgeService = Depends(get_bridge_service),
) -> ToolResolver:
    return ToolResolver(
        custom_tool_repository,
        mcp_server_repository,
        mcp_service,
        bridge_service,
    )


async def get_agent_registry(
    repository: AgentRepository = Depends(get_agent_repository),
    tool_resolver: ToolResolver = Depends(get_tool_resolver),
) -> AgentRegistry:
    return AgentRegistry(repository, tool_resolver)


async def get_billing_service(
    wallet_repository: WalletRepository = Depends(get_wallet_repository),
    registry: AgentRegistry = Depends(get_agent_registry),
    expert_skills: ExpertSkillRepository = Depends(get_expert_skill_repository),
) -> BillingService:
    return BillingService(wallet_repository, registry, expert_skills)


async def get_workflow_service(
    registry: AgentRegistry = Depends(get_agent_registry),
    tool_resolver: ToolResolver = Depends(get_tool_resolver),
    billing: BillingService = Depends(get_billing_service),
    expert_skills: ExpertSkillRepository = Depends(get_expert_skill_repository),
    mcp_service: MCPService = Depends(get_mcp_service),
    bridge_service: BridgeService = Depends(get_bridge_service),
) -> WorkflowService:
    try:
        return WorkflowService(
            get_llm_factory(),
            registry,
            get_checkpointer(),
            tool_resolver,
            billing,
            expert_skills,
            mcp_service,
            bridge_service,
            signup_credits_usd=Decimal(str(settings.signup_credits_usd)),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


async def get_smart_farm_repository(
    session: AsyncSession = Depends(get_session),
) -> SmartFarmRepository:
    return SmartFarmRepository(session)


async def get_smart_farm_service(
    repository: SmartFarmRepository = Depends(get_smart_farm_repository),
) -> SmartFarmService:
    return SmartFarmService(repository)


async def get_portfolio_service(
    repository: PortfolioRepository = Depends(get_portfolio_repository),
    registry: AgentRegistry = Depends(get_agent_registry),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> PortfolioService:
    return PortfolioService(repository, registry, workflow_service)