from fastapi import APIRouter

from app.api.routes import health, workflows
from app.api.v1 import (
    agent_ready,
    obolla_mcp,
    agents,
    bridge,
    buyer_reviews,
    community,
    creators,
    custom_tools,
    expert_skills,
    marketplace,
    mcp_servers,
    moat,
    notifications,
    portfolio,
    review_inbox,
    showcases,
    smart_farm,
    speech,
    tools,
)
from app.auth.router import router as auth_router
from app.billing.router import router as billing_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(billing_router, prefix="/billing", tags=["billing"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(portfolio.router, prefix="/agents", tags=["portfolio"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(marketplace.router, prefix="/marketplace", tags=["marketplace"])
api_router.include_router(community.router, prefix="/community", tags=["community"])
api_router.include_router(expert_skills.router, prefix="/expert-skills", tags=["expert-skills"])
api_router.include_router(agent_ready.router, prefix="/agent-ready", tags=["agent-ready"])
api_router.include_router(obolla_mcp.router, tags=["obolla-mcp"])
api_router.include_router(creators.router, prefix="/creators", tags=["creators"])
api_router.include_router(review_inbox.router, prefix="/creators/me/reviews", tags=["review-inbox"])
api_router.include_router(buyer_reviews.router, prefix="/reviews", tags=["buyer-reviews"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(showcases.router, prefix="/showcases", tags=["showcases"])
api_router.include_router(custom_tools.router, prefix="/custom-tools", tags=["custom-tools"])
api_router.include_router(mcp_servers.router, prefix="/mcp-servers", tags=["mcp-servers"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(bridge.router, prefix="/bridge", tags=["bridge"])
api_router.include_router(speech.router, prefix="/speech", tags=["speech"])
api_router.include_router(smart_farm.router, prefix="/smart-farm", tags=["smart-farm"])
api_router.include_router(moat.router, prefix="/moat", tags=["moat-intelligence"])