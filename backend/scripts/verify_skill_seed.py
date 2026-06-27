"""Verify AI Visibility Audit 2026 seed after migration 017."""

import asyncio

from sqlalchemy import text

from app.core.database import async_session_maker

SKILL_ID = "33333333-3333-4333-8333-333333333301"


async def main() -> None:
    async with async_session_maker() as session:
        skill = await session.execute(
            text(
                "SELECT price_usd_per_run, description, capabilities "
                "FROM expert_skills WHERE id = :id"
            ),
            {"id": SKILL_ID},
        )
        price, description, capabilities = skill.one()
        print(f"price: {price}")
        print(f"description: {description[:100]}...")
        print(f"capabilities: {capabilities}")

        showcases = await session.execute(
            text(
                "SELECT title, metric_value, before_after "
                "FROM skill_showcases WHERE expert_skill_id = :id ORDER BY sort_order"
            ),
            {"id": SKILL_ID},
        )
        for title, metric, before_after in showcases:
            ba = before_after or {}
            print(f"- {title} | {metric} | before: {ba.get('score_before')}")


if __name__ == "__main__":
    asyncio.run(main())