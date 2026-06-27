import asyncio
import os
os.environ['ALLOW_INSECURE_DEV_JWT'] = '1'

from app.core.database import async_session_maker
from app.services.moat_service import record_logged_outreach, log_revenue_sale_from_outreach, get_logged_sales_pipeline
from sqlalchemy import select
from app.db.models.expert_skill import ExpertSkillORM
from app.db.models.creator_earning import CreatorEarningORM

async def main():
    print("=== LIVE TEST: Logged Outreach → Sale Flow (Post-Deploy) ===\n")
    
    async with async_session_maker() as session:
        # Get a real skill from prod
        stmt = select(ExpertSkillORM.slug).limit(1)
        skill = (await session.execute(stmt)).scalar_one_or_none()
        
        if not skill:
            print("No skills found!")
            return
            
        print(f"Using skill: {skill}")
        amount = 39.0
        
        # Step 1: Log the outreach
        print("\n[1] Logging outreach data...")
        logged = await record_logged_outreach(
            session=session,
            skill_slug=skill,
            amount_usd=amount,
            note="LIVE_TEST_FLOW - verify deployed fee fix"
        )
        logged_id = logged.get("logged_item", {}).get("id")
        print(f"    Logged ID: {logged_id}")
        
        # Step 2: Convert to actual sale (this calls the fixed log_revenue_sale_from_outreach)
        print("\n[2] Converting to sale (creates Billing + Earning)...")
        sale = await log_revenue_sale_from_outreach(
            session=session,
            skill_slug=skill,
            amount_usd=amount,
            source="live_test_flow_verification",
            logged_id=logged_id
        )
        
        print(f"    billing_id: {sale.get('billing_id')}")
        print(f"    earning_id: {sale.get('earning_id')}")
        print(f"    billing_recorded: {sale.get('billing_recorded')}")
        
        # Step 3: Fetch the actual earning record to see the fee
        if sale.get("earning_id"):
            earn_stmt = select(CreatorEarningORM).where(CreatorEarningORM.id == sale.get("earning_id"))
            earning = (await session.execute(earn_stmt)).scalar_one_or_none()
            
            if earning:
                print("\n[3] CreatorEarning Record (the key backend output):")
                print(f"    gross_amount_usd : {earning.gross_amount_usd}")
                print(f"    platform_fee_usd : {earning.platform_fee_usd}")
                print(f"    net_amount_usd   : {earning.net_amount_usd}")
                
                expected_fee = round(amount * 0.20, 4)  # Now should be 20%
                print(f"\n    Expected fee (20% config): {expected_fee}")
                print(f"    Actual fee applied       : {earning.platform_fee_usd}")
                
                if abs(earning.platform_fee_usd - expected_fee) < 0.01:
                    print("\n    ✅ SUCCESS: Using configured fee (20%), not hardcoded 30%")
                else:
                    print("\n    ❌ Still using old fee?")
        
        # Step 4: Check pipeline status
        pipe = await get_logged_sales_pipeline(session=session, skill_slug=skill)
        executed = len(pipe.get("executed", []))
        print(f"\n[4] Pipeline: {executed} executed sales for this skill (including this test)")

if __name__ == "__main__":
    asyncio.run(main())
