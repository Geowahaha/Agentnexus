"""Pack- and step-specific LLM prompts for expert skill pipelines."""

from __future__ import annotations

import re

_KEYWORDS_RE = re.compile(
    r"(?:keywords?|target\s+keywords?|kw)\s*[:=]\s*(.+)",
    re.IGNORECASE,
)

LINEART_CONTENT_PACKS = frozenset(
    {
        "ai-lineart-youtube-kemlife",
        "ai-lineart-facebook-reel-kemlife",
    }
)

CONTENT_CREATOR_PACKS = frozenset(
    {
        "image-post-creator",
        "short-post-creator",
    }
)

SMART_FARM_PACKS = frozenset(
    {
        "quality-check-smart-farm",
        "japanese-melon-dataset",
    }
)

_CONTENT_STEP_IDS = frozenset(
    {
        "topic_research",
        "hook_research",
        "script",
        "image_prompts",
        "angle_research",
        "caption_draft",
        "image_prompt",
        "research",
        "draft",
        "edit",
        "gather",
        "synthesize",
        "intake",
        "work",
        "review",
        "deliver",
    }
)


def _visibility_pipeline_step(step_id: str, step_outputs: dict[str, str]) -> bool:
    """SEO / AI visibility runs include an MCP scan step before analyze."""
    if step_id in ("analyze", "improve"):
        return bool(step_outputs.get("scan"))
    if step_id == "qa":
        return bool(step_outputs.get("scan") or step_outputs.get("analyze"))
    return False

_PIPELINE_RULES = (
    "Pipeline rules: You are one step in a paid marketplace run. "
    "Never ask the buyer to paste prior step output — it is provided below when available. "
    "On the first step, work from the buyer task only. "
    "Ship concrete deliverables in markdown — no placeholders."
)


def extract_task_keywords(task: str) -> str | None:
    match = _KEYWORDS_RE.search(task)
    if not match:
        return None
    return match.group(1).strip().rstrip(".,;)")


def build_llm_prompt(
    *,
    pack_slug: str,
    step_id: str,
    skill_context: str,
    target_url: str | None,
    task_description: str,
    step_outputs: dict[str, str],
    prior: str,
) -> tuple[str, str]:
    if pack_slug == "seo-expert-analysis":
        return _seo_expert_prompts(
            step_id=step_id,
            skill_context=skill_context,
            target_url=target_url,
            task_description=task_description,
            step_outputs=step_outputs,
            prior=prior,
        )
    if pack_slug == "fable5-coding-agent":
        return _fable5_local_prompts(
            step_id=step_id,
            skill_context=skill_context,
            target_url=target_url,
            task_description=task_description,
            step_outputs=step_outputs,
            prior=prior,
        )
    if pack_slug in SMART_FARM_PACKS:
        return _smart_farm_prompts(
            pack_slug=pack_slug,
            step_id=step_id,
            skill_context=skill_context,
            task_description=task_description,
            step_outputs=step_outputs,
            prior=prior,
        )
    if pack_slug == "fable5-coding-agent-premium":
        return _fable5_premium_prompts(
            step_id=step_id,
            skill_context=skill_context,
            target_url=target_url,
            task_description=task_description,
            step_outputs=step_outputs,
            prior=prior,
        )
    if pack_slug in (
        "ai-visibility-2026",
        "fix-bot-ai-agent-ready",
        "agent-ready-auto-fix",
    ) or _visibility_pipeline_step(
        step_id, step_outputs
    ):
        return _ai_visibility_prompts(
            pack_slug=pack_slug,
            step_id=step_id,
            skill_context=skill_context,
            target_url=target_url,
            task_description=task_description,
            step_outputs=step_outputs,
            prior=prior,
        )
    if (
        pack_slug in LINEART_CONTENT_PACKS
        or pack_slug in CONTENT_CREATOR_PACKS
        or step_id in _CONTENT_STEP_IDS
        or step_id == "qa"
        or pack_slug == "custom"
    ):
        return _content_task_prompts(
            pack_slug=pack_slug,
            step_id=step_id,
            skill_context=skill_context,
            target_url=target_url,
            task_description=task_description,
            step_outputs=step_outputs,
            prior=prior,
        )
    return _generic_task_prompts(
        step_id=step_id,
        skill_context=skill_context,
        task_description=task_description,
        prior=prior,
    )


def _seo_expert_prompts(
    *,
    step_id: str,
    skill_context: str,
    target_url: str | None,
    task_description: str,
    step_outputs: dict[str, str],
    prior: str,
) -> tuple[str, str]:
    user_keywords = extract_task_keywords(task_description)
    site_intel = step_outputs.get("site_intel", "")
    scans = "\n\n".join(
        f"### {sid}\n{val}"
        for sid, val in step_outputs.items()
        if sid in ("tech_scan", "visibility_scan", "scan")
    )

    if step_id == "research":
        role = (
            "You are the Researcher Agent in a premium SEO Expert Analysis pipeline. "
            "Keywords are AUTO-EXTRACTED from the customer's website — use site_intel as "
            "the primary source. Only use user-provided keywords if explicitly given as override. "
            "Never claim backlink database metrics (DA, DR, referring domains).\n\n"
            f"{skill_context[:10000]}"
        )
        keyword_block = (
            f"User override (optional): {user_keywords}\n"
            if user_keywords
            else "User override: none — rely entirely on auto-extracted keywords.\n"
        )
        task = (
            f"Target URL: {target_url or task_description}\n"
            f"{keyword_block}\n"
            f"### Site Intelligence (crawled from live page)\n{site_intel or 'Unavailable — infer from scans'}\n\n"
            f"### Scanner data\n{scans or 'Limited scan data'}\n\n"
            "Deliver:\n"
            "1) Primary keywords (5–10) — cite which on-page evidence supports each\n"
            "2) Industry/vertical assessment from title, headings, and content\n"
            "3) 3–5 named competitors with domains (use web_context + industry knowledge)\n"
            "4) SERP landscape notes (who dominates, content types)\n"
            "5) Data gaps — what could not be verified"
        )
    elif step_id == "analyze":
        role = (
            "You are the Analyzer Agent. Deep-dive competitor content strategy and content gaps. "
            "Be specific and actionable — cite competitor pages by path pattern, not vague advice.\n\n"
            f"{skill_context[:8000]}"
        )
        task = (
            f"Target: {target_url}\n\n"
            f"Site intelligence:\n{site_intel}\n\nPrior research:\n{prior}\n\n"
            "Deliver:\n"
            "1) Competitor comparison table (structure, content types, trust signals)\n"
            "2) Content gap analysis with specific page/topic recommendations\n"
            "3) Competitive strengths/weaknesses for target site\n"
            "4) Winnable query opportunities (realistic, not guaranteed rankings)\n"
            "5) Content score /20 with justification"
        )
    elif step_id == "audit":
        role = (
            "You are the Auditor Agent. Comprehensive technical + on-page SEO audit using "
            "scan evidence and rubrics. Flag P0/P1/P2 with predicted impact ranges.\n\n"
            f"{skill_context[:8000]}"
        )
        task = (
            f"Target: {target_url}\n\n"
            f"Scans:\n{scans}\n\nPrior analysis:\n{prior}\n\n"
            "Deliver:\n"
            "1) Sub-scores: Technical /25, On-page /25 (show math)\n"
            "2) Crawlability & indexability findings\n"
            "3) On-page audit (title, meta, headings, URLs, internal links)\n"
            "4) Schema markup assessment + JSON-LD opportunities\n"
            "5) Core Web Vitals table with impact if fixed\n"
            "6) Issues list: [P0|P1|P2] — category — problem — predicted impact — fix — verify"
        )
    elif step_id == "optimize":
        role = (
            "You are the Optimizer Agent. Turn audit findings into an actionable plan with "
            "conservative impact forecasts. No ranking guarantees.\n\n"
            f"{skill_context[:6000]}"
        )
        task = (
            f"Target: {target_url}\n\nPrior work:\n{prior}\n\n"
            "Deliver:\n"
            "1) Quick Wins (this week) — numbered, effort S/M/L, predicted impact range\n"
            "2) Long-term improvements (1–3 months)\n"
            "3) Predicted outcomes table: fix → metric change → business impact range\n"
            "4) Paste-ready snippets where helpful (title/meta rewrites, schema blocks)\n"
            "5) Priority order with ROI reasoning"
        )
    elif step_id == "report":
        role = (
            "You are the Report Generator Agent. Produce a client-ready professional SEO report "
            "in polished markdown. Run QA checklist from marketplace-deliverables.md.\n\n"
            f"{skill_context[:6000]}"
        )
        task = (
            f"Target: {target_url}\n\nAll prior agent outputs:\n{prior}\n\n"
            "Deliver ONE cohesive report with:\n"
            "1) Executive summary + overall SEO score /100 + sub-scores\n"
            "2) Competitor analysis section\n"
            "3) Content gap section\n"
            "4) Technical SEO findings\n"
            "5) CWV assessment\n"
            "6) Action plan (Quick Wins + Long-term)\n"
            "7) Predicted outcomes\n"
            "8) QA verdict (READY / NEEDS_CORRECTION) with checklist PASS/FAIL\n"
            "Format for download — clear headings, tables, no placeholders."
        )
    else:
        role = f"You are an SEO specialist agent ({step_id}).\n\n{skill_context[:4000]}"
        task = f"Continue the SEO analysis for {target_url}:\n\n{prior}"

    return role, task


def _fable5_trace_rules() -> str:
    return (
        "Fable-5 trace rules: explore before edit; one logical change per file; "
        "concrete verify commands; no raw chain-of-thought; no invented APIs; "
        "no secrets or placeholder tokens in output."
    )


def _fable5_local_prompts(
    *,
    step_id: str,
    skill_context: str,
    target_url: str | None,
    task_description: str,
    step_outputs: dict[str, str],
    prior: str,
) -> tuple[str, str]:
    task_label = task_description.strip() or (target_url or "")
    trace_rules = _fable5_trace_rules()
    engine = "qwen3.6-27b-fable5 LoRA (local Ollama)"

    if step_id == "plan":
        role = (
            f"You are the Planner Agent in a local Fable-5 LoRA pipeline ({engine}). "
            "Behave like agents in Fable-5 traces: Glob/Read/Grep exploration first, "
            "then an executable edit plan. Follow marketplace-deliverables.md.\n\n"
            f"{trace_rules}\n\n"
            f"{skill_context[:10000]}"
        )
        task = (
            f"Coding task:\n{task_label}\n\n"
            "Deliver:\n"
            "1) Goal restatement + success criteria\n"
            "2) Assumptions (stack, repo layout, env limits)\n"
            "3) Exploration notes — which files you would Read/Grep and why\n"
            "4) Numbered step plan — each step names target files + verify command\n"
            "5) Risks + mitigations\n"
            "6) Out of scope"
        )
    elif step_id == "implement":
        role = (
            f"You are the Implementer Agent ({engine}). Execute the approved plan. "
            "Ship copy-paste-ready code: full files or unified diffs — never use `...`. "
            "Match existing style. Follow tool-use-patterns.md.\n\n"
            f"{trace_rules}\n\n"
            f"{skill_context[:8000]}"
        )
        plan_text = step_outputs.get("plan", prior)
        task = (
            f"Task:\n{task_label}\n\nApproved plan:\n{plan_text}\n\n"
            "Deliver:\n"
            "1) Changes summary (files touched)\n"
            "2) Code blocks — complete, copy-paste ready\n"
            "3) Bash commands — install, run, test (from repo root when possible)\n"
            "4) Env vars / migrations / breaking-change notes"
        )
    elif step_id == "review":
        role = (
            f"You are the Code Reviewer Agent ({engine}). Critique correctness, security, "
            "edge cases, test coverage, and plan adherence. Cite file paths when possible.\n\n"
            f"{trace_rules}\n\n"
            f"{skill_context[:6000]}"
        )
        task = (
            f"Task:\n{task_label}\n\nPlan + implementation:\n{prior}\n\n"
            "Deliver:\n"
            "1) Review score /10 with short rationale\n"
            "2) Issues table — P0/P1/P2, file reference, problem, fix\n"
            "3) Security & edge-case checklist\n"
            "4) Suggested patches for every P0/P1 (code blocks)"
        )
    elif step_id == "qa":
        role = (
            f"You are the QA Gate ({engine}) before delivery. "
            "Run marketplace-deliverables.md checklist strictly. "
            "Verdict must be READY or NEEDS_CORRECTION.\n\n"
            f"{skill_context[:6000]}"
        )
        task = (
            f"QA this Fable-5 local LoRA run:\n\n{prior}\n\n"
            "Deliver:\n"
            "1) QA checklist — PASS/FAIL/N/A per item\n"
            "2) Verdict — READY or NEEDS_CORRECTION\n"
            "3) Correction list — exact fixes only if NEEDS_CORRECTION"
        )
    else:
        role = f"You are a Fable-5 local LoRA agent ({step_id}).\n\n{skill_context[:4000]}"
        task = f"Continue the coding task:\n{task_label}\n\n{prior}"

    return role, task


def _fable5_premium_prompts(
    *,
    step_id: str,
    skill_context: str,
    target_url: str | None,
    task_description: str,
    step_outputs: dict[str, str],
    prior: str,
) -> tuple[str, str]:
    task_label = task_description.strip() or (target_url or "")
    trace_rules = _fable5_trace_rules()

    if step_id == "plan":
        role = (
            "You are the Planner Agent in Fable-5 Coding Agent Pro (GPT-4.1). "
            "Deliver a senior-engineer quality plan inspired by Fable-5 trace patterns. "
            "Infer likely repo layout from stack hints; name concrete paths; every step "
            "must end with a verify command. Follow marketplace-deliverables.md.\n\n"
            f"{trace_rules}\n\n"
            f"{skill_context[:10000]}"
        )
        task = (
            f"Coding task:\n{task_label}\n\n"
            "Deliver (Pro depth):\n"
            "1) Goal + measurable success criteria\n"
            "2) Stack assumptions and constraints\n"
            "3) Exploration map — Glob/Read/Grep targets with rationale\n"
            "4) Numbered plan — file paths, functions, verify command per step\n"
            "5) Test strategy — what to add or run\n"
            "6) Risks, rollback, out of scope"
        )
    elif step_id == "implement":
        role = (
            "You are the Implementer Agent (GPT-4.1 Pro). Execute the plan completely. "
            "Output production-grade artifacts: FULL file contents or unified diffs with "
            "context lines — never `...`. Include test files for new logic. "
            "This is a paid $5 run — quality must impress.\n\n"
            f"{trace_rules}\n\n"
            f"{skill_context[:8000]}"
        )
        plan_text = step_outputs.get("plan", prior)
        task = (
            f"Task:\n{task_label}\n\nApproved plan:\n{plan_text}\n\n"
            "Deliver:\n"
            "1) Changes summary\n"
            "2) Complete code blocks (implementation + tests)\n"
            "3) Bash — install, run, test, lint (copy-paste from repo root)\n"
            "4) Migration/env/breaking-change notes\n"
            "If ambiguous, state assumption and still ship complete code."
        )
    elif step_id == "review":
        role = (
            "You are the Code Reviewer (Grok 3 Mini) — independent senior reviewer. "
            "Be strict: correctness, security, edge cases, tests, plan adherence. "
            "You did not write the implementation; challenge every weak spot.\n\n"
            f"{trace_rules}\n\n"
            f"{skill_context[:6000]}"
        )
        task = (
            f"Task:\n{task_label}\n\nPlan + implementation:\n{prior}\n\n"
            "Deliver:\n"
            "1) Review score /10 — justify against Pro quality bar\n"
            "2) Issues — P0/P1/P2 with file:line references\n"
            "3) Security & edge-case audit\n"
            "4) Complete patch blocks for every P0/P1"
        )
    elif step_id == "qa":
        role = (
            "You are the QA Gate (Grok 3 Mini) for a $5 Pro delivery. "
            "Reject partial diffs, invented paths, missing tests, or secrets. "
            "Verdict READY only if a buyer could paste and run today.\n\n"
            f"{skill_context[:6000]}"
        )
        task = (
            f"QA this Pro coding run:\n\n{prior}\n\n"
            "Deliver:\n"
            "1) QA checklist — PASS/FAIL/N/A (tests, types, lint, docs, secrets, completeness)\n"
            "2) Verdict — READY or NEEDS_CORRECTION\n"
            "3) Exact corrections if NEEDS_CORRECTION"
        )
    else:
        role = f"You are a Fable-5 Pro agent ({step_id}).\n\n{skill_context[:4000]}"
        task = f"Continue the coding task:\n{task_label}\n\n{prior}"

    return role, task


def _prior_block(prior: str) -> str:
    cleaned = prior.strip()
    if not cleaned:
        return "Prior pipeline steps: (none — this is the first LLM step; use buyer task only.)"
    return f"Prior pipeline steps:\n\n{cleaned}"


def _task_requests_thai(task_label: str) -> bool:
    text = task_label.strip()
    if not text:
        return False
    if re.search(r"[\u0E00-\u0E7F]", text):
        return True
    lowered = text.lower()
    return any(token in lowered for token in ("thai", "ภาษาไทย", "lang=th", "ภาษา: ไทย"))


def _image_post_copy_mode(task_label: str) -> str:
    lowered = task_label.lower()
    if any(
        token in lowered
        for token in (
            "แคปชั่น",
            "caption style",
            "classic caption",
            "โฆษณา",
            "cta",
            "ขาย",
        )
    ):
        return "caption"
    if _task_requests_thai(task_label):
        return "story_episode"
    return "caption"


_THAI_HUMAN_COPY_RULES = (
    "Thai copy rules (mandatory when language is Thai):\n"
    "- Default format: **เรื่องเล่า 1 ตอน** — micro-story grounded in the image, not ad caption.\n"
    "- Write like a Thai creator covering AI news / global trends — conversational, short paragraphs.\n"
    "- Tie copy to the visual: mention objects, mood, layout from the planned image.\n"
    "- NEVER stiff translated Thai: no 'ในวันนี้เราจะมาพูดถึง', stacked 'อย่างไรก็ตาม/ดังนั้น', "
    "or English slogans pasted into Thai.\n"
    "- Close with a natural question or punchline — not 'บันทึกโพสต์' unless buyer asked to sell.\n"
    "- See playbook references/thai-copy-style.md."
)


def _image_post_prompts(
    *,
    step_id: str,
    task_label: str,
    prior_text: str,
    step_outputs: dict[str, str],
    playbook: str,
) -> tuple[str, str]:
    copy_mode = _image_post_copy_mode(task_label)
    thai_run = _task_requests_thai(task_label)
    thai_rules = f"\n\n{_THAI_HUMAN_COPY_RULES}" if thai_run else ""

    if step_id == "angle_research":
        role = (
            "You are the Angle & Hook Research agent for a social **image post** kit. "
            f"{_PIPELINE_RULES}\n\n{playbook}{thai_rules}"
        )
        story_note = (
            "Plan angles as **เรื่องเล่า 1 ตอน** episodes (AI news / trend update) with a visual scene each."
            if copy_mode == "story_episode"
            else "Plan classic scroll-stop caption angles."
        )
        task = (
            f"Buyer task:\n{task_label}\n\n{prior_text}\n\n"
            f"Copy mode: {copy_mode}\n\n"
            "Deliver:\n"
            "1) Restated goal, audience, platform (Instagram/Facebook/LinkedIn)\n"
            f"2) 3–5 angles — each with episode title (if story), opening hook, and visual scene for the image\n"
            "3) Recommended angle with rationale — must be easy to illustrate in one hero image\n"
            f"4) Language: {'Thai (human, conversational)' if thai_run else 'match buyer request'}\n"
            f"5) {story_note}"
        )
    elif step_id == "caption_draft":
        angles = step_outputs.get("angle_research") or prior_text
        role = (
            "You are the Copy Draft agent for a social image post. "
            "You write publish-ready Thai that sounds human — never translated or corporate. "
            f"{_PIPELINE_RULES}\n\n{playbook}{thai_rules}"
        )
        if copy_mode == "story_episode":
            deliver = (
                "Deliver markdown:\n"
                "**โหมด:** เรื่องเล่า 1 ตอน\n"
                "**ชื่อตอน:** (short, catchy Thai title)\n"
                "**เปิดเรื่อง:** 1–2 sentences tied to what the image will show\n"
                "**เนื้อเรื่อง:** 2–4 short paragraphs — AI/trend/news angle, conversational Thai\n"
                "**ปิดท้าย:** one natural question to spark comments (not hard-sell CTA)\n"
                "**Alt text:** natural Thai describing the planned visual\n"
                "**แฮชแท็ก:** 5–12 relevant tags"
            )
        else:
            deliver = (
                "Deliver:\n"
                "1) Caption — hook, body, soft CTA (still natural Thai if Thai run)\n"
                "2) Alt text for accessibility\n"
                "3) 5–15 hashtags (platform-appropriate)\n"
                "4) Note target platform and tone"
            )
        task = (
            f"Buyer task:\n{task_label}\n\n"
            f"Angle research:\n{angles}\n\n"
            f"Copy mode: {copy_mode}\n\n"
            f"{deliver}"
        )
    elif step_id == "image_prompt":
        caption = step_outputs.get("caption_draft") or prior_text
        angles = step_outputs.get("angle_research") or ""
        role = (
            "You are the Image Prompt agent for a static social post. "
            "The image must match the story opening — same objects, mood, and scene. "
            "Ship complete prompts — no placeholders. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n"
            f"Angles:\n{angles}\n\n"
            f"Copy draft (story/caption):\n{caption}\n\n"
            "Deliver:\n"
            "1) Aspect ratio (1:1 or 4:5 — infer from platform)\n"
            "2) **Full image prompt:** scene that matches the story opening and recommended angle\n"
            "3) Style block + mood aligned with AI news / trend / lifestyle topic if relevant\n"
            "4) Text-on-image overlay: usually None for story posts — say explicitly if none\n"
            "5) Optional carousel only if buyer asked"
        )
    elif step_id == "qa":
        role = (
            "You are the Publish QA gate for an image post delivery. "
            "A generated image URL must exist in the image_generate step — prompt-only is not READY. "
            "For Thai: FAIL if copy sounds translated, corporate, or disconnected from the image. "
            f"{_PIPELINE_RULES}\n\n{playbook}{thai_rules}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n"
            f"Full pipeline output:\n{prior_text}\n\n"
            "Deliver:\n"
            "1) QA checklist — PASS/FAIL/N/A per marketplace-deliverables.md "
            "(include Thai naturalness + image-copy alignment for Thai runs)\n"
            "2) Confirm generated image URL is present and downloadable\n"
            "3) If Thai is stiff/translated, verdict NEEDS_CORRECTION with rewritten opening paragraph\n"
            "4) Verdict — READY or NEEDS_CORRECTION\n"
            "5) Exact P0 fixes if NEEDS_CORRECTION"
        )
    else:
        return _generic_task_prompts(
            step_id=step_id,
            skill_context=playbook,
            task_description=task_label,
            prior=prior_text,
        )
    return role, task


def _short_post_prompts(
    *,
    step_id: str,
    task_label: str,
    prior_text: str,
    step_outputs: dict[str, str],
    playbook: str,
) -> tuple[str, str]:
    if step_id == "research":
        role = (
            "You are the Angle & Platform Research agent for **short text posts**. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n{prior_text}\n\n"
            "Deliver:\n"
            "1) Restated goal, audience, platform (X/Threads/LinkedIn/Facebook)\n"
            "2) 3 angle options with hook rationale\n"
            "3) Char limit and tone constraints for the platform\n"
            "4) Language (Thai/English) matching buyer request"
        )
    elif step_id == "draft":
        research = step_outputs.get("research") or prior_text
        role = (
            "You are the Draft Variants agent for short social posts. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n"
            f"Research:\n{research}\n\n"
            "Deliver:\n"
            "1) Variant A, B, C — each with a different opening hook\n"
            "2) Character count for each variant (respect platform limit)\n"
            "3) Label variants clearly in markdown"
        )
    elif step_id == "edit":
        drafts = step_outputs.get("draft") or prior_text
        role = (
            "You are the Polish agent for short social posts. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n"
            f"Draft variants:\n{drafts}\n\n"
            "Deliver:\n"
            "1) **Primary** polished post (best variant merged/edited)\n"
            "2) **Backup** polished post\n"
            "3) Thread split (numbered 1/N) if buyer requested a thread\n"
            "4) Final character counts for every deliverable"
        )
    elif step_id == "qa":
        role = (
            "You are the Publish QA gate for a short text post delivery. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n"
            f"Full pipeline output:\n{prior_text}\n\n"
            "Deliver:\n"
            "1) QA checklist — PASS/FAIL/N/A per marketplace-deliverables.md\n"
            "2) Verdict — READY or NEEDS_CORRECTION\n"
            "3) Exact P0 fixes if NEEDS_CORRECTION"
        )
    else:
        return _generic_task_prompts(
            step_id=step_id,
            skill_context=playbook,
            task_description=task_label,
            prior=prior_text,
        )
    return role, task


def _smart_farm_prompts(
    *,
    pack_slug: str,
    step_id: str,
    skill_context: str,
    task_description: str,
    step_outputs: dict[str, str],
    prior: str,
) -> tuple[str, str]:
    task_label = task_description.strip()
    prior_text = _prior_block(prior)
    telemetry = step_outputs.get("telemetry") or ""
    playbook = skill_context[:12000]
    crop_schema_hint = (
        "Use the Japanese melon greenhouse schema: temp, humidity, UV, light, EC, pH, "
        "soil moisture, Brix — mapped to growth stages."
    )

    if step_id == "intake":
        role = (
            "You are the Smart Farm Intake agent. Sensor data is loaded from OBOLLA DB — "
            "do NOT ask the buyer to paste readings. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n"
            f"{telemetry}\n\n{prior_text}\n\n"
            "Deliver:\n"
            "1) Restated goal + crop/greenhouse context\n"
            "2) Which sensor channels are present vs missing vs schema\n"
            "3) Data quality flags (gaps, outliers, sampling frequency)\n"
            "4) What downstream QA/dataset steps must verify"
        )
    elif step_id == "work":
        role = (
            "You are the Smart Farm Analysis agent. Work from DB telemetry only. "
            f"{crop_schema_hint}\n{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n{telemetry}\n\n{prior_text}\n\n"
            "Deliver:\n"
            "1) Channel-by-channel assessment vs expected ranges for the crop\n"
            "2) Harvest-cycle alignment notes (growth_stage, harvest_cycle_day if present)\n"
            "3) Actionable adjustments for smart-farm automation thresholds"
        )
    elif step_id in ("review", "deliver"):
        is_dataset = pack_slug == "japanese-melon-dataset"
        dataset_export = step_outputs.get("dataset_export") or ""
        role = (
            "You are the Smart Farm Deliverable agent — finalize for marketplace handoff. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        if is_dataset:
            extra = (
                "4) Dataset pack section — use ONLY the download URL from dataset_export below. "
                "Format as markdown link: [Download dataset pack](URL). "
                "NEVER invent URLs. marketplace.obolla.com does NOT exist — forbidden. "
                "Only https://obolla.com/api/v1/smart-farm/datasets/{uuid}/download is valid. "
                "Include SHA-256 from dataset_export if present. "
                "If row count is 0, verdict is NEEDS_DATA (schema template only) and explain ingest steps."
            )
            task = (
                f"Buyer task:\n{task_label}\n\n{telemetry}\n\n"
                f"Dataset export (authoritative — copy URLs exactly):\n{dataset_export}\n\n"
                f"{prior_text}\n\nDeliver polished markdown for the buyer.\n{extra}"
            )
        else:
            extra = "4) QA verdict: READY or NEEDS_CORRECTION with P0/P1 fixes"
            task = (
                f"Buyer task:\n{task_label}\n\n{telemetry}\n\n{prior_text}\n\n"
                f"Deliver polished markdown for the buyer.\n{extra}"
            )
    elif step_id == "qa":
        role = (
            "You are the Smart Farm QA Gate. Validate readings against crop schema and playbook. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n{telemetry}\n\n{prior_text}\n\n"
            "Deliver:\n"
            "1) QA checklist per sensor channel — PASS/FAIL/N/A\n"
            "2) Verdict READY or NEEDS_CORRECTION\n"
            "3) P0 fixes before trusting automation or selling dataset"
        )
    else:
        return _generic_task_prompts(
            step_id=step_id,
            skill_context=skill_context,
            task_description=task_description,
            prior=prior,
        )
    return role, task


def _content_task_prompts(
    *,
    pack_slug: str,
    step_id: str,
    skill_context: str,
    target_url: str | None,
    task_description: str,
    step_outputs: dict[str, str],
    prior: str,
) -> tuple[str, str]:
    task_label = task_description.strip() or (target_url or "")
    prior_text = _prior_block(prior)
    is_reel = pack_slug == "ai-lineart-facebook-reel-kemlife"
    aspect = "9:16 vertical Reels" if is_reel else "16:9 YouTube"
    playbook = skill_context[:12000]

    if pack_slug == "image-post-creator":
        return _image_post_prompts(
            step_id=step_id,
            task_label=task_label,
            prior_text=prior_text,
            step_outputs=step_outputs,
            playbook=playbook,
        )

    if pack_slug == "short-post-creator":
        return _short_post_prompts(
            step_id=step_id,
            task_label=task_label,
            prior_text=prior_text,
            step_outputs=step_outputs,
            playbook=playbook,
        )

    if step_id in ("topic_research", "hook_research"):
        role = (
            "You are the Topic & Hook Research agent for a faceless MS Paint line-art video kit. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n{prior_text}\n\n"
            "Deliver:\n"
            "1) 3–5 video/Reel concepts with working titles\n"
            "2) Why each title earns the click or scroll-stop\n"
            "3) Suggested length and hook words for thumbnail/on-screen text\n"
            "4) Language (Thai/English) matching buyer presets if present"
        )
    elif step_id == "script":
        hooks = step_outputs.get("topic_research") or step_outputs.get("hook_research") or ""
        role = (
            "You are the Script + Timestamps agent for a faceless MS Paint line-art pipeline. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n"
            f"Topic/hook research:\n{hooks or prior_text}\n\n"
            "Deliver:\n"
            f"1) Full voiceover script ({'30–90s Reels' if is_reel else '8–13 min YouTube'} unless buyer specified)\n"
            f"2) Dense timestamps — {'every 1–3s' if is_reel else 'every 3–7s'} (one timestamp = one image)\n"
            "3) Mark hook, re-hooks, and outro\n"
            "Use markdown with a timestamp column"
        )
    elif step_id == "image_prompts":
        script_text = step_outputs.get("script") or prior_text
        role = (
            "You are the Shot Prompt Pack agent. MS Paint style only — intentionally ugly, never pretty. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n"
            f"Approved script + timestamps:\n{script_text}\n\n"
            "Deliver a markdown table:\n"
            "| Timestamp | Narrator line | On-screen text (if Reel) | Full image prompt | Filename |\n"
            f"- Every timestamp gets one row\n"
            f"- All prompts {aspect} with MS Paint style block prepended\n"
            "- Filenames like 0-00, 0-03"
        )
    elif step_id in ("research", "gather", "intake", "analyze"):
        role = (
            "You are the Research / Intake agent in a creator content pipeline. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n{prior_text}\n\n"
            "Deliver:\n"
            "1) Restated goal + audience\n"
            "2) Key angles, constraints, and format\n"
            "3) Outline of what downstream draft/edit steps should produce"
        )
    elif step_id == "draft" or step_id == "work":
        role = (
            "You are the Draft / Work agent in a creator content pipeline. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n{prior_text}\n\n"
            "Deliver the primary working draft described in the playbook — complete markdown, ready to edit."
        )
    elif step_id in ("edit", "review", "synthesize", "deliver"):
        role = (
            f"You are the {step_id.title()} agent in a creator content pipeline. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n{prior_text}\n\n"
            "Polish and finalize the deliverable for marketplace handoff. "
            "Fix gaps from prior steps; do not ask for more input."
        )
    elif step_id == "qa":
        role = (
            "You are the QA Gate before marketplace delivery. "
            "Run the playbook deliverables checklist. Verdict must be READY or NEEDS_CORRECTION. "
            f"{_PIPELINE_RULES}\n\n{playbook}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n"
            f"Full pipeline output to QA:\n{prior_text}\n\n"
            "Deliver:\n"
            "1) QA checklist — PASS/FAIL/N/A per item from the playbook\n"
            "2) Verdict — READY or NEEDS_CORRECTION\n"
            "3) Exact P0 fixes if NEEDS_CORRECTION"
        )
    else:
        return _generic_task_prompts(
            step_id=step_id,
            skill_context=skill_context,
            task_description=task_description,
            prior=prior,
        )

    return role, task


def _generic_task_prompts(
    *,
    step_id: str,
    skill_context: str,
    task_description: str,
    prior: str,
) -> tuple[str, str]:
    task_label = task_description.strip()
    prior_text = _prior_block(prior)
    if step_id == "qa":
        role = (
            "You are the QA Gate before marketplace delivery. "
            f"{_PIPELINE_RULES}\n\n{skill_context[:8000]}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n"
            f"Pipeline output:\n{prior_text}\n\n"
            "Deliver QA checklist (PASS/FAIL/N/A), verdict READY or NEEDS_CORRECTION, and fixes."
        )
    else:
        role = (
            f"You are the pipeline agent for step '{step_id}'. "
            f"{_PIPELINE_RULES}\n\n{skill_context[:8000]}"
        )
        task = (
            f"Buyer task:\n{task_label}\n\n{prior_text}\n\n"
            f"Produce this step's deliverables as described in the playbook for '{step_id}'."
        )
    return role, task


def _ai_visibility_prompts(
    *,
    pack_slug: str,
    step_id: str,
    skill_context: str,
    target_url: str | None,
    task_description: str,
    step_outputs: dict[str, str],
    prior: str,
) -> tuple[str, str]:
    free_scan = pack_slug == "fix-bot-ai-agent-ready"
    auto_fix = pack_slug == "agent-ready-auto-fix"
    if auto_fix:
        tier = "paid Agent-Ready Auto Fix Pro"
    elif free_scan:
        tier = "free Fix Bot AI"
    else:
        tier = "paid AI Visibility"
    rubric = (
        "isitagentready.com categories (Discoverability, Content, Bot Access, Protocol, Commerce)"
        if free_scan
        else "5-layer visibility model"
    )
    if step_id == "analyze":
        role = (
            f"You are an agent-readiness auditor for a {tier} marketplace run. Use the playbook "
            f"and deterministic scan scores. Map findings to {rubric}, prioritize easy wins "
            "(robots.txt + llms.txt + Content-Signal). Follow marketplace-deliverables.md.\n\n"
            f"{skill_context}"
        )
        task = (
            f"Target URL: {target_url or task_description}\n\n"
            f"Scan results:\n{step_outputs.get('scan', 'No scan')}\n\n"
            "Deliver:\n"
            f"1) Scorecard (overall + {'isitagentready categories' if free_scan else '5 layers'})\n"
            "2) Issues list: [P0|P1|P2] title — category — problem — impact — verify\n"
            "3) Bot status table (Before from scan data)\n"
            "4) List of deployable files needed\n"
        )
        if free_scan:
            task += (
                "5) Note: buyer can verify at https://isitagentready.com/\n"
                "Reference successcasting.com case study when relevant.\n"
            )
        task += "If scan was blocked (401/403/522), say so upfront — do not invent scores."
    elif step_id == "improve":
        role = (
            f"You are a fix-pack generator for a {tier} run. Ship complete paste-ready "
            "file contents: robots.txt (explicit AI bots + Content-Signal), llms.txt (Markdown "
            "links only), agents.txt, ai.txt, JSON-LD, Cloudflare _headers / next.config snippets. "
            "No placeholders, no secrets.\n\n"
            f"{skill_context[:8000]}"
        )
        extra = (
            "Include protocol stubs (api-catalog, OAuth, auth.md, MCP card, agent-skills, WebMCP) "
            "and commerce layer (UCP, ACP, openapi MPP, x402 /api/v1) when scan shows gaps or "
            "commerce signals. Follow successcasting-100-playbook.md. Add stack deploy guide "
            "(Next.js / Cloudflare / WordPress / static) and re-verify commands."
            if auto_fix
            else ""
        )
        task = (
            f"Target: {target_url}\n\n"
            f"Prior work:\n{prior}\n\n"
            "Generate every deployable file with full content and paste location. "
            "Include Before → After bot status projection for fixes you ship. "
            "Add 3–5 easy wins (isitagentready-style) the buyer can deploy this week."
            f"{(' ' + extra) if extra else ''}"
        )
    else:
        role = (
            "You are the final QA gate before delivery. Run the marketplace-deliverables.md "
            "checklist. Mark each item PASS/FAIL/N/A. Challenge invented scores, missing "
            "Markdown links in llms.txt, robots/WAF mismatches, fake JSON-LD/MCP, and any secrets. "
            "If FAIL items exist, list exact corrections."
        )
        task = (
            f"QA this expert skill run:\n\n{prior}\n\n"
            "Output: QA checklist (PASS/FAIL/N/A per item), delivery verdict "
            "(READY or NEEDS_CORRECTION), and any corrected snippets. "
            "If proof_badge / Agent-Ready Proof Badge is present, verify the public proof URL "
            "and embed snippet are included verbatim — do not invent alternate proof links."
        )
        if free_scan or auto_fix:
            task += "\nInclude: 'Verify at https://isitagentready.com/' in the delivery footer."
        if auto_fix:
            task += (
                "\nInclude deploy guide section and note successcasting.com as 100% reference."
            )
    return role, task