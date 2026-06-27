# Agent Skills — AgentNexus / OBOLLA

Skills follow the [Agent Skills specification](https://agentskills.io/specification) ([anthropics/skills](https://github.com/anthropics/skills)).

## Layout

```
skills/                          # Cross-agent domain skills (Claude, Grok, API)
├── skill-creator/               # Official Anthropic skill-creator (create + eval loop)
├── isitagentready-one-stop/     # Protocol Level 5 / discovery
├── template-SKILL.md            # Minimal template
└── AGENT-SKILLS-SPEC.md         # Spec pointer

.grok/skills/                    # Grok project skills (workflow + loops)
├── obolla-workflow/             # Master framework (start here)
├── agent-ready-proof/
├── loop-verifier/
├── loop-triage/
└── loop-budget/
```

## Create a new skill

1. Read `skills/skill-creator/SKILL.md`
2. Scaffold from `skills/template-SKILL.md`
3. Validate:

```bash
python skills/skill-creator/scripts/quick_validate.py path/to/skill-name
```

4. For Grok project skills: place under `.grok/skills/<name>/` (name must match folder)
5. Run evals per skill-creator when output is verifiable

## Install external skills

```bash
npx skills add anthropics/skills
npx skills add thananon/9arm-skills
```

## OBOLLA entry point

Grok: `/obolla-workflow` → `.grok/skills/obolla-workflow/SKILL.md`