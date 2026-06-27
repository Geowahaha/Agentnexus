# AgentNexus / OBOLLA — Agent Instructions

## กรอบการทำงานหลัก (Grok)

**ใช้ skill นี้ทุกครั้งที่ทำงานใน repo นี้:**

`.grok/skills/obolla-workflow/SKILL.md` — รวมแนว 9arm-skills + loop-engineering + กฎ OBOLLA

```text
/obolla-workflow
```

## สร้าง skill ใหม่ (Anthropic standard)

- Spec: [agentskills.io](https://agentskills.io/specification) · repo: [anthropics/skills](https://github.com/anthropics/skills)
- Creator: `skills/skill-creator/SKILL.md` (ติดตั้งใน repo แล้ว)
- Validate: `python skills/skill-creator/scripts/quick_validate.py <skill-dir>`
- Index: `skills/README.md`

## แนวทางทำงานร่วมกับ AI agent

**เป้าหมาย: ทำให้สำเร็จ — ไม่หยุดที่ “คุณไปรันเอง”**

1. **รันคำสั่งเองก่อน** — agent ต้องลอง deploy / health / API ด้วย shell จริง ไม่ส่งแค่คำแนะนำ
2. **Workaround ก่อนยอมแพ้** — ถ้า auth / token / env ขัด ให้หาทางอื่น (เช่น OAuth แทน scoped token, ย้าย `.env` ชั่วคราว, ใช้ `account_id` ใน wrangler) แล้วลองต่อ
3. **แยกชั้น production** — Edge (`obolla.com`) = Cloudflare Worker; API/DB = VPS `43.128.75.149` เท่านั้น
4. **ปิดงานด้วยหลักฐาน** — หลัง deploy ต้องเช็ก `https://obolla.com/health` → `backend_reachable: true` และยืนยัน asset/bundle ขึ้นจริงเมื่อเกี่ยวกับ frontend
5. **บันทึกทางแก้ถาวร** — workaround ที่ใช้ได้ซ้ำ → สคริปต์ใน `scripts/` (เช่น `deploy-obolla.ps1`)

### OBOLLA edge deploy (token / OAuth)

`CLOUDFLARE_API_TOKEN` ใน `.env` มักเป็น token แคบ (DNS/Tunnel) — **Wrangler จะเลือก token นี้ก่อน OAuth** แล้ว deploy Worker ล้มเหลว (auth 10000)

ใช้สคริปต์นี้แทน `wrangler deploy` ตรงๆ:

```powershell
pwsh -NoProfile -File scripts/deploy-obolla.ps1
# หรือ
npm run deploy:obolla
```

สคริปต์จะ: build frontend → ตรวจสิทธิ์ Workers ของ token → ถ้าไม่พอ ย้าย `.env` ชั่วคราวแล้ว deploy ด้วย OAuth → restore `.env` → smoke `/health`

ครั้งแรกหรือ OAuth หมดอายุ: `npx wrangler login` (ต้อง unset `CLOUDFLARE_API_TOKEN` ใน session ก่อน login)

### ภาษาไทย (skill content)

- UI ใช้ `strings.ts` — ชื่อ/คำอธิบาย **สินค้าจาก creator** มาจาก API (`?lang=th`)
- เปิดหน้า skill ครั้งแรกภาษาไทย → backend แปลอัตโนมัติ (Gemini) แล้วเก็บใน `expert_skills.i18n`
- **OBOLLA จัด copy ไทยให้เอง** (`thai_copy.py`) — โทนมุมกาแฟ ตรงความสามารถจริง; creator ไม่ต้องแปลเอง
- Skill ใหม่/แก้ชื่อ → regenerate `i18n.th` อัตโนมัติตอน create/update
- Migration: `040_obolla_thai_skill_copy` — seed copy ทุก skill บน marketplace

## Production 24/7 rule (บังคับ)

**อะไรที่ขัด / ทำให้ใช้งานทุก feature ไม่ได้ 24/7 — ห้ามปล่อยไว้ — ต้องแก้หรือย้ายไป VPS**

- Production API + DB + tunnel รันบน VPS `43.128.75.149` เท่านั้น
- Edge (`obolla.com`) อยู่บน Cloudflare Workers
- อย่าใช้เครื่อง Windows dev เป็น production backend
- รายละเอียดเต็ม: [.production/PRODUCTION-RULES.md](.production/PRODUCTION-RULES.md)

## Deploy production

```powershell
# Edge (obolla.com Worker + SPA)
pwsh -NoProfile -File scripts/deploy-obolla.ps1

# Backend API + DB (VPS)
pwsh -NoProfile -File scripts/deploy-vps-production.ps1
```

## Health check

`https://obolla.com/health` ต้องได้ `backend_reachable: true` เสมอ

## IsItAgentReady Level 5 / 100% workflow

ใช้ skill ใน repo นี้เมื่ออัปเกรดหรือ rescan agent-readiness:

`skills/isitagentready-one-stop/SKILL.md`

เป้าหมายคือ Level 5 / 100% สำหรับ `https://obolla.com` และเว็บอื่นที่นำ workflow นี้ไปใช้ต่อ โดยต้อง deploy จริงแล้ว rescan live origin ไม่หยุดแค่สร้างไฟล์

กฎ DNSSEC:

- ถ้า DNS-AID fail เพราะ DNSSEC pending ให้ reset Cloudflare DNSSEC ได้แค่ครั้งเดียว
- ต้อง enable กลับไว้เสมอ
- หลัง enable กลับแล้วให้หยุด reset และรอ Cloudflare/parent registry publish DS
- ห้ามปล่อย DNSSEC เป็น `disabled`

helper:

```powershell
node skills/isitagentready-one-stop/scripts/reset-cloudflare-dnssec-once.mjs --zone-id <zone-id> --env-file <cf-env-file>
```

## Loop engineering (working rules)

We follow [loop-engineering](https://github.com/cobusgreyling/loop-engineering): **design loops that prompt agents**, not one-shot prompts.

| File | Purpose |
|------|---------|
| `LOOP.md` | Active loops, cadence, human gates |
| `STATE.md` | Durable memory + obolla.com proof baseline |
| `loop-run-log.md` | Append-only evidence per run |
| `loop-budget.md` | Token caps + kill switch |
| `docs/safety.md` | Denylist, verifier rules |

**Phases:** L1 report-only → L2 assisted fix + verifier → L3 unattended (scoped tokens).

**Agent-Ready proof (current — L1):** Test `https://obolla.com` tools first; record what verify / analyze / fix-pack / MCP can prove. **Do not change score formulas** until proof criteria in `STATE.md` are met. Skill: `.grok/skills/agent-ready-proof`. Checker: `.grok/skills/loop-verifier`.

```powershell
npx @cobusgreyling/loop-audit . --suggest
npx @cobusgreyling/loop-cost --pattern daily-triage --level L1
```

Grok loop command:

```text
/loop 1d Run agent-ready-proof for https://obolla.com. L1 only. Update STATE.md and loop-run-log.md.
```
