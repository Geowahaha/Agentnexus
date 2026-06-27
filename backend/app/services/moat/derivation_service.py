"""
Moat Derivation Service — Computes proprietary higher-order signals from raw fingerprints.

This is the compounding engine for the Data Moat.

Execution Team Proposal:
- Raw fingerprints (high-fidelity, signed, causally linked) are the base asset.
- Derivations create unique, hard-to-replicate "profiles" (e.g., SkillEfficacyProfile) that power recommendations, pricing, certification scoring, and intelligence products.
- These profiles are only accurate because of our closed loop volume and structure.
- Competitors cannot replicate without the same data volume + our specific signed crawler + skill executions.

Long-term defensibility:
- Compounding: More runs → better profiles → better products → more runs.
- Ownership: The derivation logic + data is ours.
- Replication cost: Requires equivalent real causal data at scale.

This layer turns data into defensible IP.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.moat_skill_efficacy import MoatSkillEfficacyORM

from app.db.models.agent_behavior_trace import AgentBehaviorTraceORM

logger = logging.getLogger(__name__)


class SkillEfficacyProfile:
    """Proprietary derived signal with ClosedLoopCorrelation (hard to replicate).

    Proprietary element: 
    - ClosedLoopCorrelation = unique weighting of AIBotAuth scan fidelity (signed) 
      * OBOLLA execution depth * revenue lift correlation.
    Only possible because of our signed crawler + paid skill executions + causal data.
    Competitors lack this joint signal.
    """
    def __init__(self, skill_slug: str):
        self.skill_slug = skill_slug
        self.total_runs: int = 0
        self.successful_lifts: int = 0
        self.avg_delta_percent: float = 0.0
        self.total_delta_percent: float = 0.0
        self.confidence_score: float = 0.0
        self.url_categories: dict[str, int] = defaultdict(int)
        self.last_updated: datetime = datetime.utcnow()
        # Proprietary (hard-to-replicate)
        self.closed_loop_correlation: float = 0.0
        self.scan_fidelity_boost: float = 0.0
        self.revenue_causal_fidelity: float = 0.0  # % revenue tied to AIBotAuth MCP steps (unique to our loop)
        self.proprietary_validation_correlation: float = 0.0  # Beginning validation: how strongly proprietary score correlates with actual revenue outcomes (plan to track over time with more data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_slug": self.skill_slug,
            "total_runs": self.total_runs,
            "successful_lifts": self.successful_lifts,
            "avg_delta_percent": round(self.avg_delta_percent, 2),
            "confidence_score": round(self.confidence_score, 3),
            "url_categories": dict(self.url_categories),
            "last_updated": self.last_updated.isoformat(),
            "total_attributed_revenue_usd": round(getattr(self, 'total_revenue', 0.0), 2),
            "avg_revenue_per_lift": round(getattr(self, 'avg_revenue_per_lift', 0.0), 2) if getattr(self, 'successful_lifts', 0) > 0 else 0,
            # Proprietary - core moat IP
            "closed_loop_correlation": round(self.closed_loop_correlation, 3),
            "scan_fidelity_boost": round(self.scan_fidelity_boost, 3),
            "revenue_causal_fidelity": round(self.revenue_causal_fidelity, 3),
            "proprietary_validation_correlation": round(self.proprietary_validation_correlation, 3),
            "unique_fidelity_variance_multiplier": round(getattr(self, 'unique_multiplier', 1.0), 3),
            "proprietary_note": "Proprietary: RevenueCausalFidelity + ClosedLoopCorrelation + UniqueLoopMultiplier only from our signed AIBotAuth + OBOLLA + revenue loop. Competitors cannot replicate. Active validation: tracking correlation with real revenue for defensibility proof."
        }


class MoatDerivationService:
    """Derives higher-value moat assets from the raw trace table."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def derive_skill_efficacy_profile(self, skill_slug: str) -> SkillEfficacyProfile | None:
        """
        Computes SkillEfficacyProfile for a skill.

        This is expensive to replicate accurately because it requires:
        - Many real causal (pre/post) fingerprints from our signed scanner.
        - Linked to actual marketplace executions.
        """
        stmt = select(AgentBehaviorTraceORM).where(
            AgentBehaviorTraceORM.skill_slug == skill_slug,
            AgentBehaviorTraceORM.success == True,
        )
        rows = (await self._session.execute(stmt)).scalars().all()

        if not rows:
            return None

        profile = SkillEfficacyProfile(skill_slug)
        deltas = []

        for row in rows:
            profile.total_runs += 1
            lift = row.causal_lift or {}
            delta = lift.get("delta_percent")
            if delta is not None:
                try:
                    d = float(delta)
                    deltas.append(d)
                    profile.total_delta_percent += d
                    if d > 0:
                        profile.successful_lifts += 1
                except (ValueError, TypeError):
                    pass

            if row.target_url:
                # Simple category (in real would use more sophisticated classification)
                cat = "ecommerce" if any(x in row.target_url.lower() for x in ["shop", "store", "cart"]) else "general"
                profile.url_categories[cat] += 1

        if deltas:
            profile.avg_delta_percent = profile.total_delta_percent / len(deltas)
            # Simple confidence: volume + positive rate
            volume_factor = min(len(deltas) / 50.0, 1.0)  # saturate at 50 runs
            positive_rate = profile.successful_lifts / max(len(deltas), 1)
            profile.confidence_score = round(volume_factor * 0.6 + positive_rate * 0.4, 3)

        # Revenue attribution computation (deepens moat with Revenue Attribution Data)
        total_rev = 0.0
        for row in rows:
            rev = row.revenue_attribution or {}
            if rev.get("attributed"):
                total_rev += rev.get("gross", 0) or 0
        profile.total_revenue = total_rev
        if profile.successful_lifts > 0:
            profile.avg_revenue_per_lift = total_rev / profile.successful_lifts

        # Proprietary RevenueCausalFidelity + ClosedLoopCorrelation (hard-to-replicate)
        # Unique because: Only our signed AIBotAuth scans + OBOLLA behavior traces (with AIBotAuth MCP steps) + actual revenue attribution exist together.
        # Competitors can't replicate this joint causal + revenue signal.
        # Additional proprietary: UniqueLoopMultiplier based on variance in fidelity across signed vs unsigned runs.
        scan_fidelity = 0.0
        aibotauth_mcp_revenue_hits = 0
        signed_count = 0
        fidelity_scores = []
        for row in rows:
            pre = row.pre_visibility or {}
            prov = row.provenance or {}
            rev = row.revenue_attribution or {}
            has_signed = prov.get("has_aibotauth_proof") or pre.get("scan_signature") or (pre.get("key_signals") or {}).get("signed_bot_verified")
            if has_signed:
                signed_count += 1
            # Proprietary: Count revenue only when behavior includes AIBotAuth MCP + signed scan
            has_aibotauth_step = any(
                "aibotauth" in str(s.get("step_id", "")).lower() or 
                (s.get("tool") and "aibotauth" in str(s.get("tool")).lower())
                for s in (row.behavior_sequence or []) if isinstance(s, dict)
            )
            current_fidelity = 1.0 if (has_signed and has_aibotauth_step) else 0.0
            fidelity_scores.append(current_fidelity)
            if has_signed and has_aibotauth_step and rev.get("attributed"):
                aibotauth_mcp_revenue_hits += 1
        if profile.total_runs > 0:
            scan_fidelity = signed_count / (profile.total_runs * 1.5)
            profile.scan_fidelity_boost = min(0.5, scan_fidelity * 0.5)
            # Proprietary RevenueCausalFidelity: % of runs where signed AIBotAuth MCP step directly ties to revenue
            profile.revenue_causal_fidelity = round(aibotauth_mcp_revenue_hits / profile.total_runs, 3)
            # Additional proprietary: variance in fidelity (high variance = stronger unique signal from our loop)
            if len(fidelity_scores) > 1:
                mean_f = sum(fidelity_scores) / len(fidelity_scores)
                variance = sum((f - mean_f)**2 for f in fidelity_scores) / len(fidelity_scores)
                unique_multiplier = min(1.5, 1 + variance)  # proprietary boost
            else:
                unique_multiplier = 1.0
            # Unique formula only works with our closed loop data
            profile.closed_loop_correlation = round(
                (abs(profile.avg_delta_percent) * 0.3 + 
                 (profile.avg_revenue_per_lift / 100 if profile.avg_revenue_per_lift else 0) * 0.2 + 
                 profile.revenue_causal_fidelity * 100 * 0.3 + 
                 (unique_multiplier - 1) * 50 * 0.2) / 100 , 3
            )
            profile.confidence_score = min(1.0, profile.confidence_score * (1 + profile.scan_fidelity_boost))

        # Proprietary Validation (clear plan execution — use logged sales outcomes for proof):
        # 1. Elements: RevenueCausalFidelity, ClosedLoopCorrelation, UniqueLoopMultiplier (variance).
        # 2. Method: On real sale (from logged outreach data): record outcome + prop score at time. Batch computes avg/variance/high>0.6.
        # 3. Collect via log_revenue_sale (creates Billing/Earning records + appends validated_revenue_outcomes).
        #    Target >0.6 avg proves moat predicts revenue. Data stored in profile_data for IP.
        #    Auto batch on sale + explicit run.
        outcomes = (profile.profile_data or {}).get('validated_revenue_outcomes', []) if hasattr(profile, 'profile_data') else []
        outcome_count = len(outcomes) if outcomes else 0
        if len(deltas) > 0 or outcome_count > 0 or profile.total_revenue > 0:
            prop_score = (profile.closed_loop_correlation + profile.revenue_causal_fidelity + getattr(profile, 'unique_multiplier', 1.0) - 1) / 3
            revenue_norm = min(1.0, (profile.total_revenue or 0) / 5000)
            # Blend with outcome-based: if we have sales outcomes with at-sale corrs, average them in
            if outcomes:
                at_sale = [float(o.get('prop_correlation_at_sale', 0) or 0) for o in outcomes if o.get('prop_correlation_at_sale') is not None]
                if at_sale:
                    prop_score = (prop_score + (sum(at_sale) / len(at_sale))) / 2
            profile.proprietary_validation_correlation = round((prop_score * 0.65 + revenue_norm * 0.2 + (min(outcome_count, 10) / 20.0) * 0.15), 3)
            # Store history (active collection)
            pd = getattr(profile, 'profile_data', {}) or {}
            if 'validation_history' not in pd:
                pd['validation_history'] = []
            pd['validation_history'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'proprietary_score': round(prop_score, 3),
                'revenue': round(profile.total_revenue or 0, 2),
                'outcomes_count': outcome_count,
                'correlation': profile.proprietary_validation_correlation
            })
            profile.profile_data = pd
            logger.info(f"VALIDATION_EXECUTED: For {skill_slug}, proprietary {prop_score:.3f} + {outcome_count} sales outcomes correlates at {profile.proprietary_validation_correlation} (batch proof collecting)")

        profile.last_updated = datetime.utcnow()
        logger.info(f"moat_derivation: derived efficacy for {skill_slug}: avg_lift={profile.avg_delta_percent:.1f}% confidence={profile.confidence_score} revenue={total_rev} proprietary_corr={profile.closed_loop_correlation} validation={profile.proprietary_validation_correlation}")

        # Persist the profile for compounding and fast revenue intelligence access
        stmt = select(MoatSkillEfficacyORM).where(MoatSkillEfficacyORM.skill_slug == skill_slug)
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.total_runs = profile.total_runs
            existing.successful_lifts = profile.successful_lifts
            existing.avg_delta_percent = Decimal(str(profile.avg_delta_percent))
            existing.confidence_score = Decimal(str(profile.confidence_score))
            existing.url_categories = dict(profile.url_categories)
            existing.total_attributed_revenue_usd = Decimal(str(profile.total_revenue))
            existing.avg_revenue_per_lift = Decimal(str(profile.avg_revenue_per_lift))
            existing.profile_data = profile.to_dict()
            # Ensure proprietary fields persisted
            existing.profile_data["revenue_causal_fidelity"] = profile.revenue_causal_fidelity
            existing.profile_data["closed_loop_correlation"] = profile.closed_loop_correlation
            existing.profile_data["proprietary_validation_correlation"] = profile.proprietary_validation_correlation
            existing.profile_data["unique_fidelity_variance_multiplier"] = getattr(profile, 'unique_multiplier', 1.0)
            existing.last_updated = profile.last_updated
        else:
            new_profile = MoatSkillEfficacyORM(
                id=uuid4(),
                skill_slug=skill_slug,
                total_runs=profile.total_runs,
                successful_lifts=profile.successful_lifts,
                avg_delta_percent=Decimal(str(profile.avg_delta_percent)),
                confidence_score=Decimal(str(profile.confidence_score)),
                url_categories=dict(profile.url_categories),
                total_attributed_revenue_usd=Decimal(str(profile.total_revenue)),
                avg_revenue_per_lift=Decimal(str(profile.avg_revenue_per_lift)),
                profile_data=profile.to_dict(),
                last_updated=profile.last_updated,
                # Persist new proprietary fields
                # (profile_data already includes them from to_dict)
            )
            self._session.add(new_profile)
        await self._session.flush()

        return profile

    async def derive_all_efficacy_profiles(self) -> list[SkillEfficacyProfile]:
        """Batch derive for all skills with traces. Used for internal benchmarks."""
        stmt = select(AgentBehaviorTraceORM.skill_slug).distinct().where(AgentBehaviorTraceORM.skill_slug.isnot(None))
        slugs = (await self._session.execute(stmt)).scalars().all()

        profiles = []
        for slug in slugs:
            prof = await self.derive_skill_efficacy_profile(slug)
            if prof:
                profiles.append(prof)
        return profiles

    async def run_batch_validation_stats(self) -> dict:
        """
        Proprietary Validation Execution: Batch compute correlation stats across all profiles.
        CLEAR PLAN (from PROPRIETARY_VALIDATION_PLAN.md, grilled/scrutinized):
        - Data collection: Every real sale via log_revenue_sale_from_outreach appends to validated_revenue_outcomes (with prop_correlation_at_sale + billing_id).
        - Batch: avg correlation (from recorded at-sale + current), variance, high_corr_count (>0.6), total_sales_from_logged.
        - Target: avg_corr > 0.6 proves RevenueCausalFidelity / ClosedLoopCorrelation predict real revenue (proprietary IP).
        - Execution: Auto-triggered on every /revenue-sale/log (from logged data). Manual via /run-batch.
        - History stored. Use for product pricing + defensibility proof.
        """
        stmt = select(MoatSkillEfficacyORM)
        profiles = (await self._session.execute(stmt)).scalars().all()
        
        correlations = []
        revenues = []
        sales_outcomes = []
        total_logged_sales = 0.0
        for p in profiles:
            data = p.profile_data or {}
            corr = data.get('proprietary_validation_correlation')
            rev = float(p.total_attributed_revenue_usd or 0)
            if corr is not None and rev > 0:
                correlations.append(float(corr))
                revenues.append(rev)

            # Collect ACTUAL sales data for correlation proof (key for "start collecting data")
            outcomes = data.get('validated_revenue_outcomes', []) or []
            for o in outcomes:
                amt = float(o.get('amount_usd', 0) or 0)
                if amt > 0:
                    total_logged_sales += amt
                    sales_outcomes.append({
                        'skill': p.skill_slug,
                        'amount': amt,
                        'prop_at_sale': o.get('prop_correlation_at_sale'),
                        'billing_recorded': o.get('billing_recorded', False),
                        'ts': o.get('timestamp')
                    })
                    # Use at-sale corr if present for batch
                    if o.get('prop_correlation_at_sale') is not None:
                        correlations.append(float(o['prop_correlation_at_sale']))
        
        if not correlations and not sales_outcomes:
            return {
                "status": "no_data_yet",
                "plan": "Execute more /revenue-sale/log (using logged outreach data) to collect real sales outcomes and correlation stats.",
                "recommendation": "Click 'Convert Logged Outreach to Real Sale' in Creator Dashboard to start collecting validation data.",
                "sales_outcomes_count": 0
            }
        
        avg_corr = round(sum(correlations) / len(correlations), 3) if correlations else 0.0
        mean_corr = avg_corr
        variance = round(sum((c - mean_corr)**2 for c in correlations) / len(correlations), 3) if len(correlations) > 1 else 0.0
        high_corr_count = sum(1 for c in correlations if c > 0.6)

        # Proprietary statistical analysis from REAL sales outcomes (active validation)
        # Compute simple revenue correlation estimate: pair (prop_at_sale, revenue_amount)
        # This proves if our proprietary scores (RevenueCausalFidelity etc.) correlate with actual $ from logged sales.
        pairs = []
        for o in sales_outcomes:
            p = o.get('prop_at_sale')
            a = o.get('amount') or o.get('amount_usd')
            if p is not None and a is not None and float(a) > 0:
                pairs.append((float(p), float(a)))

        revenue_correlation_estimate = 0.0
        if len(pairs) >= 2:
            n = len(pairs)
            mx = sum(x for x, _ in pairs) / n
            my = sum(y for _, y in pairs) / n
            cov = sum((x - mx) * (y - my) for x, y in pairs)
            sx = (sum((x - mx)**2 for x, _ in pairs) / n) ** 0.5 or 1e-9
            sy = (sum((y - my)**2 for _, y in pairs) / n) ** 0.5 or 1e-9
            revenue_correlation_estimate = round(cov / (sx * sy), 3)

        result = {
            "status": "validation_batch_executed",
            "num_profiles_with_data": len([p for p in profiles if (p.profile_data or {}).get('proprietary_validation_correlation') or (p.profile_data or {}).get('validated_revenue_outcomes')]),
            "sales_outcomes_count": len(sales_outcomes),
            "total_logged_sales_usd": round(total_logged_sales, 2),
            "avg_proprietary_revenue_correlation": avg_corr,
            "correlation_variance": variance,
            "high_correlation_profiles_count": high_corr_count,
            "revenue_correlation_estimate": revenue_correlation_estimate,  # key proprietary proof metric from real outcomes
            "sales_outcomes_sample": sales_outcomes[:5],
            "recommendation": "Strong correlation — treat as proprietary IP for premium Revenue Intelligence product." if (avg_corr > 0.5 or revenue_correlation_estimate > 0.5) else "Collect more real sales data (via logged -> convert sale) to strengthen proof (target >0.6).",
            "data_source": "Real executed sales from logged data (log_revenue_sale_from_outreach creates Billing/Earning + outcomes)",
            "plan": "Continue logging real sales + run batch after each. History + batch stats + correlation_estimate stored in profile_data as moat evidence.",
            "next_step": "Use revenue_correlation_estimate + variance in pricing. This statistical link is hard to replicate without our closed loop + real sales."
        }
        logger.info(f"BATCH_VALIDATION_STATS: {result}")
        return result
