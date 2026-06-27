import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, request } from '../api/client'  // request for custom POSTs
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import { SecurityTrustStrip } from '../components/trust/SecurityTrustStrip'
import { normalizeSiteUrl } from '../utils/normalizeSiteUrl'


export function AgentReadyPro() {
  const { token, user } = useAuth()
  const { locale, tr } = useLocale()
  const navigate = useNavigate()
  const runRef = useRef<HTMLDivElement>(null)

  const [url, setUrl] = useState('')
  const [consentAccepted, setConsentAccepted] = useState(false)
  const [running, setRunning] = useState(false)
  const [runSeconds, setRunSeconds] = useState(0)
  const [error, setError] = useState('')
  const [result, setResult] = useState<any>(null)
  const [initialResult, setInitialResult] = useState<any>(null)
  const [fixPack, setFixPack] = useState<any>(null)
  const [applied, setApplied] = useState(false)
  const [reScanning, setReScanning] = useState(false)
  const [backgroundQueued, setBackgroundQueued] = useState('')
  const [coachSession, setCoachSession] = useState<any>(null)
  const [savedSites, setSavedSites] = useState<any[]>([])
  const [loadingSession, setLoadingSession] = useState(false)

  const isTh = locale === 'th'

  const isEntitledForUrl = useCallback((siteUrl: string) => {
    if (!siteUrl) return false
    const { normalized } = normalizeSiteUrl(siteUrl)
    if (!normalized) return false
    return savedSites.some((s: any) => s.site_url === normalized && s.entitled)
  }, [savedSites])

  const normalizedUrl = useMemo(() => {
    const { normalized } = normalizeSiteUrl(url)
    return normalized || ''
  }, [url])

  const entitled = isEntitledForUrl(url)
  const coachMatchesUrl = Boolean(
    coachSession?.site_url && normalizedUrl && coachSession.site_url === normalizedUrl,
  )

  const applyCoachSession = useCallback((session: any) => {
    if (!session) return
    setCoachSession(session)
    if (session.site_url) setUrl(session.site_url)
    const latest = session.latest_scan
    if (latest) setResult(latest)
    if (session.initial_scan) setInitialResult(session.initial_scan)
    if (session.fix_pack) setFixPack(session.fix_pack)
    if (session.progress?.mcp_applied) setApplied(true)
  }, [initialResult])

  const refreshSavedSites = useCallback(async () => {
    if (!token) return
    try {
      const res: any = await request('/agent-ready/coach/sites', {}, token)
      setSavedSites(res.sites || [])
    } catch {
      /* no sessions yet */
    }
  }, [token])

  useEffect(() => {
    refreshSavedSites()
  }, [refreshSavedSites])

  useEffect(() => {
    if (!token || !url.trim()) return
    const { normalized, error: urlErr } = normalizeSiteUrl(url)
    if (urlErr || !normalized) return
    if (!isEntitledForUrl(normalized)) return
    let cancelled = false
    setLoadingSession(true)
    request(`/agent-ready/coach/session?url=${encodeURIComponent(normalized)}`, {}, token)
      .then((session: any) => { if (!cancelled) applyCoachSession(session) })
      .catch(() => { /* no session */ })
      .finally(() => { if (!cancelled) setLoadingSession(false) })
    return () => { cancelled = true }
  }, [token, url, isEntitledForUrl, applyCoachSession])
  const skillId = '33333333-3333-4333-8333-333333333310'
  const price = 9.99

  const headline = isTh
    ? 'บอท AI มองไม่เห็นเว็บ? ได้ไฟล์แก้จริง'
    : 'AI skips your site. Real fixes — not PDFs.'

  const subline = isTh
    ? 'Growth Score จุดเสียรายได้ · AIBotAuth · PageSpeed · SEO/AEO/AAIO · พิสูจน์ ROI'
    : 'Growth Score · AIBotAuth deep · PageSpeed · SEO/AEO/AAIO · ROI proof'

  const steps = [
    { num: '1', title: isTh ? 'สแกน' : 'Scan', desc: isTh ? '8 บอทบอกว่าเสียตรงไหน' : '8 bots show what blocks you' },
    { num: '2', title: isTh ? 'ไฟล์จริง' : 'Real files', desc: isTh ? 'robots · llms · schema' : 'robots · llms · schema' },
    { num: '3', title: isTh ? 'MCP' : 'MCP', desc: isTh ? 'วางเดียว AI deploy' : 'One paste · AI deploys' },
  ]

  function scrollToRun() {
    runRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  async function handleRun(e: FormEvent) {
    e.preventDefault()
    if (!token) {
      navigate('/register', { state: { from: { pathname: '/agent-ready' } } })
      return
    }
    if (!consentAccepted) {
      setError(tr('skillConsentRequired') || 'Please accept consent')
      return
    }

    const { normalized, error: urlErr } = normalizeSiteUrl(url)
    if (urlErr) {
      setError(urlErr)
      return
    }
    if (isEntitledForUrl(normalized)) {
      setError(
        isTh
          ? 'เว็บนี้ซื้อแล้ว — ใช้ Re-scan ฟรีเท่านั้น (ไม่สามารถสแกนจ่ายซ้ำได้)'
          : 'This site is already purchased — use free re-scan only.',
      )
      return
    }

    setRunning(true)
    setError('')
    setResult(null)
    setInitialResult(null)
    setFixPack(null)
    setApplied(false)
    setReScanning(false)
    const start = Date.now()
    const timer = setInterval(() => setRunSeconds(Math.floor((Date.now() - start) / 1000)), 1000)

    try {
      const workflow = await api.runWorkflow(token, {
        task_description: normalized,
        workflow_type: 'expert_skill',
        expert_skill_id: skillId,
        task_context: { expert_skill_id: skillId, expert_skill_slug: 'agent-ready-auto-fix', target_url: normalized },
      })

      const wfId = workflow.workflow_id
      let scored: any = null
      try {
        const analyze: any = await request('/agent-ready/analyze', { method: 'POST', body: JSON.stringify({ url: normalized, workflow_id: wfId }) }, token)
        scored = analyze?.partial && analyze?.summary?.percent == null
          ? await request('/agent-ready/verify', { method: 'POST', body: JSON.stringify({ url: normalized, workflow_id: wfId, max_attempts: 1, purge_between: false }) }, token).then((v: any) => ({
              ...analyze,
              summary: v?.final ?? v?.attempts?.[0] ?? analyze.summary,
              scan: { level: v?.final?.level, level_name: v?.final?.level_name },
            })).catch(() => analyze)
          : analyze
        setResult(scored)
        setInitialResult(scored)
      } catch (e) {
        console.warn('analyze failed', e)
        try {
          const verify: any = await request('/agent-ready/verify', { method: 'POST', body: JSON.stringify({ url: normalized, workflow_id: wfId, max_attempts: 1, purge_between: false }) }, token)
          scored = {
            url: normalized,
            summary: verify?.final ?? verify?.attempts?.[0] ?? { percent: 0 },
            scan: { level: verify?.final?.level, level_name: verify?.final?.level_name },
            note: 'Score from live verify (analyze unavailable)',
          }
          setResult(scored)
          setInitialResult(scored)
        } catch {
          scored = { url: normalized, summary: { percent: 0 }, note: 'Scan unavailable — try again in a minute' }
          setResult(scored)
          setInitialResult(scored)
        }
      }

      let pack: any = null
      try {
        pack = await request('/agent-ready/fix-pack', { method: 'POST', body: JSON.stringify({ url: normalized, workflow_id: wfId }) }, token)
        setFixPack(pack)
      } catch (e) {
        console.warn('fix-pack failed', e)
        pack = { url: normalized, files: {}, note: 'Fix-pack endpoint not available, basic mode' }
        setFixPack(pack)
      }

      try {
        const session: any = await request('/agent-ready/coach/sync', {
          method: 'POST',
          body: JSON.stringify({
            url: normalized,
            workflow_id: workflow.workflow_id,
            analyze: scored,
            fix_pack: pack,
            progress: { scanned: true, fix_pack_ready: true, mcp_applied: false, reverified: false },
          }),
        }, token)
        applyCoachSession(session)
        await refreshSavedSites()
      } catch (e) {
        console.warn('coach sync failed', e)
      }

      clearInterval(timer)
      setRunning(false)

      // Show rich inline results below
    } catch (err: any) {
      setError(err?.message || 'Failed to start agent flow')
      setRunning(false)
      clearInterval(timer)
    }
  }

  async function handleApplyMCP() {
    if (!url || !token || applied) return
    setApplied(true)
    try {
      // Clean MCP path: calls /apply which builds pack + auto-logs revenue (Billing + CreatorEarning) via moat.
      // Revenue tracked automatically via moat on apply.
      const applyRes: any = await request('/agent-ready/apply', {
        method: 'POST',
        body: JSON.stringify({ url }),
      }, token)

      // New MCP-shaped response: { result: {fix_pack, ...}, sale, message, revenue_logged }
      const returnedPack = applyRes?.result?.fix_pack || applyRes?.pack
      if (returnedPack) {
        setFixPack(returnedPack)
      } else {
        try {
          const pack = await request('/agent-ready/fix-pack', { method: 'POST', body: JSON.stringify({ url }) }, token)
          setFixPack(pack)
        } catch (_) {}
      }

      try {
        await request('/agent-ready/coach/progress', {
          method: 'POST',
          body: JSON.stringify({ url, progress: { mcp_applied: true } }),
        }, token)
      } catch { /* optional */ }
    } catch (e: any) {
      setApplied(false)
      setError('MCP apply start failed: ' + (e.message || ''))
    }
  }

  async function handleReScan() {
    if (!url || !token) return
    const { normalized, error: urlErr } = normalizeSiteUrl(url)
    if (urlErr || !normalized) {
      setError(urlErr || 'Invalid URL')
      return
    }
    setReScanning(true)
    setBackgroundQueued('')
    setError('')
    try {
      const session: any = await request('/agent-ready/coach/rescan', {
        method: 'POST',
        body: JSON.stringify({ url: normalized, notify_email: true }),
      }, token)
      applyCoachSession(session)
      await refreshSavedSites()
      const emailSent = session?.notification?.email?.sent === 'true'
      if (emailSent) {
        setBackgroundQueued(isTh ? 'ส่งสรุปทาง email แล้ว' : 'Summary emailed to you')
      }
    } catch (e: any) {
      setError(isTh ? `Re-scan ล้มเหลว: ${e.message || ''}` : `Re-scan failed: ${e.message || ''}`)
    } finally {
      setReScanning(false)
    }
  }

  async function handleBackgroundReScan() {
    if (!url || !token) return
    const { normalized, error: urlErr } = normalizeSiteUrl(url)
    if (urlErr || !normalized) {
      setError(urlErr || 'Invalid URL')
      return
    }
    setError('')
    try {
      const res: any = await request('/agent-ready/coach/rescan-async', {
        method: 'POST',
        body: JSON.stringify({ url: normalized, notify_email: true }),
      }, token)
      setBackgroundQueued(
        isTh
          ? (res.message_th || 'กำลัง re-scan — เราจะส่ง email เมื่อเสร็จ ปิดหน้าได้เลย')
          : (res.message_en || 'Re-scan queued — we will email you when done.'),
      )
    } catch (e: any) {
      setError(isTh ? `คิว re-scan ล้มเหลว: ${e.message || ''}` : `Background re-scan failed: ${e.message || ''}`)
    }
  }

  const coach = coachMatchesUrl ? coachSession?.coach : null
  const coachHeadlineTh = coach?.headline_th_business || coach?.headline_th
  const coachHeadlineEn = coach?.headline_en
  const coachSummaryTh = coach?.executive_summary_th_business || coach?.executive_summary_th
  const coachSummaryEn = coach?.executive_summary_en
  const coachStepsTh = coach?.next_steps_th_business || coach?.next_steps_th
  const coachStepsEn = coach?.next_steps_en
  const showCoach = Boolean(coach)
  const hasPurchasedSites = savedSites.some((s: any) => s.entitled)
  const isUnpurchasedUrl = Boolean(normalizedUrl && hasPurchasedSites && !entitled)

  return (
    <div className="page-shell mx-auto max-w-5xl px-4 sm:px-6">
      <div className="mb-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs sm:text-sm">
        <Link to="/" className="text-readable-muted hover:text-[var(--color-text)]">← Marketplace</Link>
        <span className="hidden sm:inline text-[var(--color-border)]">·</span>
        <span className="pro-badge text-[10px] sm:text-xs">Agent-Ready</span>
      </div>

      <div className="mt-4 sm:mt-6 max-w-xl">
        <p className="text-[10px] uppercase tracking-[2px] text-[var(--color-coffee)]">OBOLLA × AIBotAuth</p>
        <h1 className="mt-2 text-[1.65rem] leading-tight font-semibold tracking-tight sm:text-4xl">{headline}</h1>
        <p className="mt-2 text-sm sm:text-base text-readable-muted leading-snug">{subline}</p>
      </div>

      <div className="mt-4 sm:mt-5 max-w-xl">
        <button
          type="button"
          onClick={scrollToRun}
          className="w-full sm:w-auto rounded-2xl bg-[var(--color-market)] px-6 py-3 text-sm font-semibold text-white"
        >
          {isTh ? `สแกนเว็บฉัน — $${price}` : `Scan my site — $${price}`}
        </button>
      </div>

      <div className="mt-5 sm:mt-6 grid grid-cols-3 gap-2 sm:gap-3 max-w-xl">
        {steps.map((s, i) => (
          <div key={i} className="rounded-2xl border bg-white px-2 py-3 sm:p-4 text-center">
            <div className="text-[9px] sm:text-[10px] uppercase tracking-wide text-[var(--color-coffee)]">{s.num}</div>
            <div className="mt-0.5 text-sm sm:text-base font-semibold">{s.title}</div>
            <div className="mt-0.5 text-[10px] sm:text-xs text-readable-muted leading-tight">{s.desc}</div>
          </div>
        ))}
      </div>

      {/* Saved sites — bound purchase; free re-scan only for these URLs */}
      {user && savedSites.length > 0 && (
        <div className="mt-6 sm:mt-8 max-w-xl rounded-2xl sm:rounded-3xl border bg-white p-3 sm:p-4">
          <div className="text-[10px] uppercase tracking-[2px] text-[var(--color-coffee)] mb-2">
            {isTh ? 'เว็บที่ซื้อแล้ว · re-scan ฟรี' : 'Purchased · free re-scan'}
          </div>
          <div className="flex flex-wrap gap-2">
            {savedSites.map((s: any) => (
              <button
                key={s.site_host}
                type="button"
                onClick={() => setUrl(s.site_url)}
                className={`rounded-2xl border px-3 py-2 text-left text-xs ${url === s.site_url ? 'border-emerald-600 bg-emerald-50' : 'hover:bg-zinc-50'}`}
              >
                <div className="font-semibold">{s.site_host}</div>
                <div className="text-readable-muted">Growth {s.growth_percent ?? '—'}% · {s.scan_count ?? 0} scans</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Agent coach — smart summary from first scan */}
      {user && showCoach && coach && (
        <div className="mt-5 sm:mt-6 max-w-xl rounded-2xl sm:rounded-3xl border-2 border-[var(--color-coffee)]/20 bg-gradient-to-br from-white to-amber-50/40 p-4 sm:p-5">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <div className="text-[10px] uppercase tracking-[2px] text-[var(--color-coffee)]">
              {isTh ? 'Agent Coach' : 'Agent Coach'}
            </div>
            {coach.gemini_enriched && (
              <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-[10px] font-medium text-blue-700">
                Gemini
              </span>
            )}
          </div>
          <h2 className="text-xl font-semibold leading-snug">
            {isTh ? coachHeadlineTh : coachHeadlineEn}
          </h2>
          <p className="mt-2 text-sm text-readable-muted leading-relaxed">
            {isTh ? coachSummaryTh : coachSummaryEn}
          </p>
          {isTh && coach.revenue_insight_th && (
            <p className="mt-2 text-sm font-medium text-amber-900/90 leading-relaxed">
              {coach.revenue_insight_th}
            </p>
          )}
          {(coach.delta_narrative_en || coach.delta_narrative_th) && (
            <p className="mt-2 text-sm font-medium text-emerald-800">
              {isTh ? coach.delta_narrative_th : coach.delta_narrative_en}
            </p>
          )}
          {coachStepsEn?.length > 0 && (
            <ul className="mt-3 space-y-1 text-xs text-readable-muted">
              {(isTh ? coachStepsTh : coachStepsEn).slice(0, 4).map((step: string, i: number) => (
                <li key={i}><span className="text-emerald-700 font-mono mr-1">{i + 1}.</span>{step}</li>
              ))}
            </ul>
          )}
          {backgroundQueued && (
            <p className="mt-3 text-xs font-medium text-emerald-800">{backgroundQueued}</p>
          )}
          {entitled && (
            <div className="mt-4 space-y-2">
              <button
                type="button"
                onClick={handleReScan}
                disabled={reScanning || loadingSession}
                className="w-full rounded-2xl border border-emerald-600 bg-white py-2.5 text-sm font-semibold text-emerald-800 hover:bg-emerald-50 disabled:opacity-60"
              >
                {reScanning ? (isTh ? 'กำลัง re-scan...' : 'Re-scanning...') : (isTh ? 'Re-scan ฟรี (อัปเดตหน้านี้ + ส่ง email)' : 'Free re-scan (update here + email)')}
              </button>
              <button
                type="button"
                onClick={handleBackgroundReScan}
                disabled={reScanning || loadingSession}
                className="w-full rounded-2xl border border-[var(--color-border)] bg-white py-2.5 text-sm font-medium text-readable-muted hover:bg-zinc-50 disabled:opacity-60"
              >
                {isTh ? 'Re-scan พื้นหลัง — ส่ง email เมื่อเสร็จ (ปิดหน้าได้)' : 'Background re-scan — email when done (leave page)'}
              </button>
            </div>
          )}
        </div>
      )}

      {isUnpurchasedUrl && (
        <div className="mt-5 max-w-xl rounded-2xl border border-amber-300 bg-amber-50 px-3 py-2.5 text-xs sm:text-sm text-amber-900 leading-snug">
          {isTh
            ? `เว็บ ${normalizedUrl} ยังไม่ได้ซื้อ — จ่าย $${price} เพื่อสแกนเว็บใหม่ หรือเลือกเว็บที่ซื้อแล้วด้านบนเพื่อ re-scan ฟรี`
            : `${normalizedUrl} is not purchased — pay $${price} for a new site, or pick a purchased site above for free re-scan.`}
        </div>
      )}

      {/* Super simple run form */}
      <div ref={runRef} className="mt-6 sm:mt-8 max-w-xl">
        {!user ? (
          <Link to="/register" className="block rounded-2xl bg-[var(--color-market)] py-3 text-center font-semibold text-white">Sign up free to try</Link>
        ) : (
          <form onSubmit={handleRun} className="space-y-3">
            <input
              type="text"
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="https://your-site.com"
              className="w-full rounded-2xl border px-4 py-3"
              required
            />
            {entitled ? (
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-4 text-sm text-emerald-900">
                {isTh
                  ? `เว็บนี้ซื้อแล้ว — ใช้ Re-scan ฟรีด้านบนเท่านั้น (ไม่สแกนจ่ายซ้ำ)`
                  : `This site is purchased — use free re-scan above only (no duplicate paid scan)`}
              </div>
            ) : (
              <button 
                type="submit" 
                disabled={running || !consentAccepted}
                className="w-full rounded-2xl bg-black py-3 text-sm font-bold text-white disabled:opacity-60"
              >
                {running
                  ? `Working... ${runSeconds}s`
                  : hasPurchasedSites
                    ? (isTh ? `ซื้อสแกนเว็บใหม่ — $${price}` : `Buy scan for new site — $${price}`)
                    : `Scan & Prepare Fixes — $${price}`}
              </button>
            )}
            {/* Clean professional consent for customers (benefit-focused, non-redundant) */}
            <label className="flex cursor-pointer gap-3 rounded-2xl border border-[var(--color-border)] bg-white p-3.5 text-sm">
              <input
                type="checkbox"
                checked={consentAccepted}
                disabled={running}
                onChange={(e) => setConsentAccepted(e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-[var(--color-border)] accent-[var(--color-market)]"
              />
              <span className="text-readable-muted leading-relaxed">
                {isTh ? (
                  <>ยืนยันว่าฉันมีสิทธิ์สแกนและปรับปรุงเว็บไซต์นี้ ฉันยอมรับ <Link to="/terms" className="font-medium underline decoration-[var(--color-border)] hover:text-[var(--color-text)]">ข้อกำหนดการใช้บริการ</Link> และ <Link to="/security" className="font-medium underline decoration-[var(--color-border)] hover:text-[var(--color-text)]">นโยบายความปลอดภัย</Link></>
                ) : (
                  <>I confirm I have permission to scan and improve this site. I accept the <Link to="/terms" className="font-medium underline decoration-[var(--color-border)] hover:text-[var(--color-text)]">Terms of Service</Link> and <Link to="/security" className="font-medium underline decoration-[var(--color-border)] hover:text-[var(--color-text)]">Safety &amp; Risk Policy</Link>.</>
                )}
              </span>
            </label>
            {error && <p className="text-xs text-red-600">{error}</p>}
          </form>
        )}
      </div>

      {/* Clean zen results — before/after + clear progress for the closed-loop agent */}
      {(result || fixPack) && (
        <div className="mt-10 max-w-2xl space-y-8">

          {/* Agent Progress — visible on the Flagship Closed-Loop */}
          <div>
            <div className="text-[10px] uppercase tracking-[2px] text-[var(--color-coffee)] mb-1.5">Flagship • Closed-Loop Agent-Ready Progress</div>
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
              <span className="rounded-2xl bg-emerald-700 px-3 py-0.5 text-white">1. Scanned</span>
              <span className="text-readable-muted">→</span>
              <span className="rounded-2xl bg-emerald-700 px-3 py-0.5 text-white">2. Fix pack ready</span>
              <span className="text-readable-muted">→</span>
              <span className={`rounded-2xl px-3 py-0.5 ${applied ? 'bg-emerald-700 text-white' : 'border border-[var(--color-border)]'}`}>3. MCP spec to your local AI</span>
              <span className="text-readable-muted">→</span>
              <span className={`rounded-2xl px-3 py-0.5 ${initialResult && result && result.summary?.percent !== initialResult.summary?.percent ? 'bg-emerald-700 text-white' : 'border border-[var(--color-border)]'}`}>4. Updated live by AI</span>
            </div>
            <div className="mt-1 text-[11px] text-readable-muted">The agent process is now visible. Your local AI (Claude/Cursor/Grok) can update the live view here.</div>
          </div>

          {/* OBOLLA Smart Score — layered, honest */}
          {result && (
            <div className="space-y-4">
              <div className="text-xs uppercase tracking-[2px] text-[var(--color-coffee)]">GROWTH SCORE — REVENUE IMPACT (BEFORE / AFTER)</div>

              <div className="flex flex-wrap items-end gap-6">
                <div>
                  <div className="text-xs text-readable-muted">Before</div>
                  <div className="text-5xl font-semibold tabular-nums text-zinc-400">
                    {initialResult?.growth_score ?? initialResult?.summary?.growth_percent ?? initialResult?.summary?.percent ?? '—'}<span className="text-2xl">%</span>
                  </div>
                </div>
                <div className="text-3xl text-readable-muted pb-1">→</div>
                <div>
                  <div className="text-xs text-emerald-700">Live now</div>
                  <div className="text-6xl font-semibold tabular-nums">
                    {result.growth_score ?? result.smart_scorecard?.growth_score ?? result.summary?.percent ?? '—'}<span className="text-3xl">%</span>
                  </div>
                </div>
                <div className="text-xs text-readable-muted pb-2 space-y-0.5">
                  {result.summary?.protocol_percent != null && (
                    <div>Protocol: <strong>{result.summary.protocol_percent}%</strong></div>
                  )}
                  {result.summary?.smart_percent != null && (
                    <div>Technical blend: <strong>{result.summary.smart_percent}%</strong></div>
                  )}
                </div>
              </div>

              {result.smart_scorecard?.special_offer?.included && (
                <div className="rounded-2xl border border-emerald-300 bg-emerald-50 px-4 py-2 text-xs text-emerald-900">
                  ✓ {isTh ? 'รวม AIBotAuth Deep Scan (ลูกค้าจ่ายแล้ว)' : 'Includes paid AIBotAuth.com deep scan'}
                  {result.smart_scorecard.aibotauth_deep_scan?.scanned_at && (
                    <span className="text-readable-muted"> · {result.smart_scorecard.aibotauth_deep_scan.scanned_at}</span>
                  )}
                  {result.smart_scorecard.layers?.aibotauth_deep?.grade && (
                    <span className="ml-2 font-semibold">Grade {result.smart_scorecard.layers.aibotauth_deep.grade}</span>
                  )}
                </div>
              )}

              {result.smart_scorecard?.honest_verdict && (
                <p className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                  {result.smart_scorecard.honest_verdict}
                </p>
              )}

              {result.smart_scorecard?.layers && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                  {(['aibotauth_deep', 'seo', 'aeo', 'bot_readability', 'crawler_access', 'performance', 'social', 'aaio'] as const).map((key) => {
                    const layer = result.smart_scorecard.layers[key]
                    if (!layer) return null
                    const pct = layer.percent ?? 0
                    return (
                      <div key={key} className="rounded-xl border bg-white p-3">
                        <div className="text-[10px] uppercase tracking-wide text-readable-muted">{layer.label || key}</div>
                        <div className={`text-lg font-semibold tabular-nums ${pct >= 70 ? 'text-emerald-700' : pct >= 40 ? 'text-amber-700' : 'text-red-700'}`}>{pct}%</div>
                      </div>
                    )
                  })}
                </div>
              )}

              {result.smart_scorecard?.layers?.performance && (
                <div className="rounded-2xl border bg-white p-4">
                  <div className="text-xs uppercase tracking-widest text-[var(--color-coffee)] mb-2">
                    {isTh ? 'PageSpeed / Core Web Vitals (AIBotAuth deep)' : 'PageSpeed / Core Web Vitals (AIBotAuth deep)'}
                  </div>
                  <div className="flex flex-wrap items-baseline gap-4">
                    <div>
                      <span className="text-3xl font-semibold tabular-nums">{result.smart_scorecard.layers.performance.pagespeed_score ?? result.smart_scorecard.layers.performance.percent}</span>
                      <span className="text-lg text-readable-muted">/100</span>
                    </div>
                    <div className="text-xs text-readable-muted space-y-0.5">
                      {result.smart_scorecard.layers.performance.lcp_ms != null && (
                        <div>LCP: <strong>{result.smart_scorecard.layers.performance.lcp_ms}ms</strong></div>
                      )}
                      {result.smart_scorecard.layers.performance.cls != null && (
                        <div>CLS: <strong>{result.smart_scorecard.layers.performance.cls}</strong></div>
                      )}
                      {result.smart_scorecard.layers.performance.inp_ms != null && (
                        <div>INP: <strong>{result.smart_scorecard.layers.performance.inp_ms}ms</strong></div>
                      )}
                      {result.smart_scorecard.layers.performance.cwv_ratings?.length > 0 && (
                        <div>{result.smart_scorecard.layers.performance.cwv_ratings.join(' · ')}</div>
                      )}
                      <div className="text-[10px]">{result.smart_scorecard.layers.performance.source || 'lab Lighthouse'}</div>
                    </div>
                  </div>
                  <p className="mt-2 text-[11px] text-readable-muted">
                    {isTh ? 'น้ำหนัก ~9% ใน Smart Score · จาก deep scan ที่ลูกค้าจ่ายแล้ว' : '~9% weight in Smart Score · from your paid deep scan'}
                  </p>
                </div>
              )}

              {result.smart_scorecard?.layers?.bot_readability?.bots?.length > 0 && (
                <div className="rounded-2xl border bg-white p-4">
                  <div className="text-xs uppercase tracking-widest text-[var(--color-coffee)] mb-2">
                    {isTh ? 'AIBotAuth สไตล์ — 8 crawlers' : 'AIBotAuth-style — 8 crawlers'}
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead><tr className="text-readable-muted"><th className="py-1">Bot</th><th>Result</th><th>HTTP</th></tr></thead>
                      <tbody>
                        {result.smart_scorecard.layers.bot_readability.bots.map((row: any) => (
                          <tr key={row.bot} className="border-t border-[var(--color-border)]">
                            <td className="py-1 font-medium">{row.bot}</td>
                            <td className={row.result === 'can_read' ? 'text-emerald-700' : row.result === 'served_thin' ? 'text-amber-700' : 'text-red-700'}>
                              {row.result === 'served_thin' ? '⚠ served_thin' : row.result === 'can_read' ? '✓ can read' : row.result}
                            </td>
                            <td>{row.http ?? '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {result.smart_scorecard?.growth_scorecard?.pillars?.length > 0 && (
                <div className="rounded-2xl border bg-white p-4">
                  <div className="text-xs uppercase tracking-widest text-[var(--color-coffee)] mb-3">
                    {isTh ? 'เกณฑ์ Growth → รายได้' : 'Growth criteria → revenue'}
                  </div>
                  <ul className="space-y-2 text-xs">
                    {result.smart_scorecard.growth_scorecard.pillars.map((p: any) => (
                      <li key={p.id} className="flex justify-between gap-2 border-b border-[var(--color-border)] pb-2 last:border-0">
                        <span>
                          <strong>{p.label}</strong>
                          <span className="block text-[10px] text-readable-muted">{p.revenue_link}</span>
                        </span>
                        <span className={`shrink-0 font-semibold tabular-nums ${p.percent >= 75 ? 'text-emerald-700' : p.percent >= 50 ? 'text-amber-700' : 'text-red-700'}`}>
                          {p.percent}%
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {result.smart_scorecard?.revenue_actions?.length > 0 && (
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-4">
                  <div className="text-xs uppercase tracking-widest text-emerald-800 mb-2">
                    {isTh ? 'ลำดับแก้เพื่อรายได้' : 'Revenue action queue'}
                  </div>
                  <ul className="space-y-1.5 text-xs">
                    {result.smart_scorecard.revenue_actions.slice(0, 5).map((a: any, i: number) => (
                      <li key={i}><span className="font-mono text-emerald-800">{a.priority}</span> {a.action} <span className="text-readable-muted">→ {a.revenue}</span></li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="text-xs text-emerald-700">Target: Growth Score 75%+ · PageSpeed ≥75 · proof URL for outreach</div>
            </div>
          )}

          {/* Very short fixes list */}
          {fixPack && Object.keys(fixPack.files || {}).length > 0 && (
            <div>
              <div className="uppercase text-xs tracking-widest text-[var(--color-coffee)] mb-2">REAL FIXES READY (from MCP pack)</div>
              <ul className="space-y-1 text-sm">
                {Object.keys(fixPack.files).slice(0, 3).map(k => (
                  <li key={k} className="flex gap-2">
                    <span className="text-emerald-700">✓</span>
                    <span>{k}</span>
                  </li>
                ))}
              </ul>
              {fixPack.mcp_tool && (
                <div className="mt-2 text-[10px] text-readable-muted">+ MCP spec for your AI (SEO + AEO + AAIO + Revenue)</div>
              )}
            </div>
          )}

          {/* ONE primary zen button — Apply with your AI via MCP */}
          <div>
            <button
              onClick={handleApplyMCP}
              disabled={applied || !fixPack}
              className="w-full rounded-3xl bg-black py-4 text-lg font-semibold text-white disabled:bg-zinc-700"
            >
              {applied ? '✓ MCP Spec Delivered — Revenue Tracked' : 'Apply with your AI (MCP) — Secure'}
            </button>
            <div className="text-center text-xs text-emerald-700 mt-2 font-medium">
              Revenue already logged on this click. Copy the one button below → paste to your AI → it calls MCP and finishes.
            </div>
          </div>

          {/* One-shot complete prompt — copy once, AI calls MCP and finishes */}
          {fixPack && (
            <div className="rounded-3xl border-2 border-emerald-600 bg-emerald-50 p-5">
              <div className="text-center">
                <div className="text-xs uppercase tracking-widest text-emerald-700 mb-1">READY FOR YOUR AI — ONE COPY, COMPLETE</div>
                <button
                  onClick={async () => {
                    const fullPrompt = `You are my local AI with direct access to the live OBOLLA MCP server.

=== MCP ENDPOINT (call this) ===
POST https://obolla.com/mcp
Protocol: JSON-RPC 2.0 (tools/call)

=== TOOL + DATA FROM MY SCAN (USE EXACTLY THIS — NO QUESTIONS) ===
Tool name: apply_agent_ready_fix

url: ${url}

fix_pack: ${JSON.stringify(fixPack, null, 2)}

Tool definition (for reference):
${JSON.stringify(fixPack.mcp_tool, null, 2)}

=== DO THIS NOW ===
Call:
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "apply_agent_ready_fix",
    "arguments": {
      "url": "${url}",
      "fix_pack": <use the exact fix_pack object above>
    }
  }
}

Revenue will be logged automatically.

After the result, reply with a short clear summary only:
- MCP success: yes (pack prepared)
- Pack: number of files + key ones
- Revenue: billing_id + earning_id + $9.99 (status closed)
- auto_deployed: false (no tokens)
- What I should do next (apply the files from the pack or give deploy tokens)

Finish in this response. No asking back.`;

                    await navigator.clipboard.writeText(fullPrompt);
                    alert('✅ Copied! Paste directly to Claude / Cursor / Grok.\n\nEverything is inside: url + full fix_pack + exact MCP call format.\nYour AI will call the MCP and finish in one go.');
                  }}
                  className="w-full rounded-2xl bg-emerald-700 py-4 text-base font-bold text-white active:bg-emerald-800"
                >
                  Copy complete prompt to your AI<br />
                  <span className="text-sm font-normal">(url + fix_pack + MCP instructions — 1 paste, done)</span>
                </button>
                <p className="mt-2 text-[11px] text-emerald-700">
                  Your AI will call https://obolla.com/mcp directly. Revenue auto-tracked.
                </p>
              </div>
            </div>
          )}

          {/* Clear re-scan to see what the local AI did (addresses before/after confusion) */}
          {(applied || entitled) && (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
              <div className="text-sm font-medium">
                {applied
                  ? (isTh ? 'ส่ง MCP ให้ AI แล้ว + บันทึก revenue' : 'MCP delivered to your AI + revenue logged.')
                  : (isTh ? 'คุณมีสิทธิ์ re-scan ฟรีสำหรับเว็บนี้' : 'You have free re-scan entitlement for this site.')}
              </div>
              <button
                onClick={handleReScan}
                disabled={reScanning}
                className="mt-3 w-full rounded-2xl bg-white py-3 text-sm font-semibold border hover:bg-emerald-100 disabled:opacity-60"
              >
                {reScanning
                  ? (isTh ? 'กำลัง re-scan...' : 'Re-scanning live site...')
                  : (isTh ? 'Re-scan ฟรี → อัปเดต before/after + email' : 'Free re-scan → update before/after + email')}
              </button>
              <button
                type="button"
                onClick={handleBackgroundReScan}
                disabled={reScanning}
                className="mt-2 w-full rounded-2xl border border-dashed py-2.5 text-xs font-medium text-readable-muted hover:bg-white disabled:opacity-60"
              >
                {isTh ? 'หรือ re-scan พื้นหลัง — ส่ง email เมื่อเสร็จ (ไม่ต้องเปิดหน้า)' : 'Or background re-scan — email when done (no need to stay)'}
              </button>
              {backgroundQueued && (
                <p className="mt-2 text-xs font-medium text-emerald-800">{backgroundQueued}</p>
              )}
              <p className="mt-2 text-xs text-readable-muted">
                {isTh
                  ? `หลัง deploy fixes ขึ้น ${url || 'เว็บ'} แล้ว กด re-scan — คะแนน before/after จะอัปเดต และส่งสรุปภาษาไทยทาง email`
                  : `After your local AI (or you) deploys fixes to ${url || 'the site'}, re-scan updates scores and emails a Thai business summary.`}
              </p>
            </div>
          )}

          {/* Subtle external proof link only */}
          <div className="pt-2 text-xs">
            <a href={`https://aibotauth.com/?url=${encodeURIComponent(url)}`} target="_blank" rel="noreferrer" className="underline text-readable-muted">Optional: view live proof on Aibotauth</a>
          </div>
        </div>
      )}

      <div className="mt-16">
        <SecurityTrustStrip compact />
      </div>
    </div>
  )
}
