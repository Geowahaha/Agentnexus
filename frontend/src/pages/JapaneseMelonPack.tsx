import { useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'
import { SecurityTrustStrip } from '../components/trust/SecurityTrustStrip'

export function JapaneseMelonPack() {
  const { locale } = useLocale()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const farmId = searchParams.get('farm_id') || ''
  const isTh = locale === 'th'

  const [busy, setBusy] = useState(false)

  const headline = isTh
    ? 'Japanese Melon Greenhouse Dataset Pack'
    : 'Japanese Melon Greenhouse Dataset Pack'

  const dna = isTh
    ? 'ข้อมูลจากสวนจริง — agent ช่วยจัดระเบียบ คุณมีเวลาไปดูแลต้นเมล่อนและนั่งกาแฟ'
    : 'Real telemetry from your greenhouse. Agents do the heavy organizing so you have time for the plants and coffee with people you love.'

  const deliverables = [
    { icon: '📊', title: isTh ? 'JSON / CSV ตามสคีมา' : 'Schema-aligned JSON + CSV', desc: isTh ? 'พร้อมนำไปใช้กับระบบ IoT และ automation' : 'Ready for IoT platforms and automation tools' },
    { icon: '📋', title: isTh ? 'รายงานความครอบคลุม' : 'Channel Coverage Report', desc: isTh ? 'เทียบกับ Japanese melon greenhouse schema' : 'Compared against Japanese melon greenhouse research schema' },
    { icon: '🔗', title: isTh ? 'ลิงก์ดาวน์โหลด' : 'Fresh Download Link', desc: isTh ? 'ข้อมูลล่าสุดจากฟาร์มของคุณ' : 'Latest export from your sensors' },
    { icon: '📝', title: isTh ? 'คู่มือนำเข้า' : 'Import Notes', desc: isTh ? 'วิธีใส่ข้อมูลเข้า Smart Farm ระบบอื่น' : 'Guidance for other IoT / smart-farm systems' },
  ]

  async function handleQuickExport(_format: 'json' | 'csv') {
    if (!farmId) {
      alert(isTh ? 'กรุณาเลือกฟาร์มจากหน้า Smart Farm ก่อน' : 'Please come from a specific Smart Farm page to include farm context.')
      return
    }
    setBusy(true)
    // In real flow this would call backend export. Here we just navigate to smart farm for demo.
    setTimeout(() => {
      setBusy(false)
      navigate(`/smart-farm?farm_id=${farmId}`)
    }, 420)
  }

  return (
    <div className="page-shell mx-auto max-w-5xl">
      <div className="flex items-center gap-2 text-sm mb-4">
        <Link to="/smart-farm" className="text-readable-muted hover:text-[var(--color-text)]">← Smart Farm</Link>
        <span className="text-[var(--color-border)]">·</span>
        <span className="pro-badge">Smart Farm Data Product</span>
      </div>

      <div className="rich-hero p-8 sm:p-12">
        <h1 className="text-4xl font-semibold tracking-[-1.2px] sm:text-[42px]">{headline}</h1>
        <p className="mt-3 max-w-2xl text-lg text-readable-muted">{dna}</p>
        {farmId && (
          <div className="mt-3 inline-block rounded-full bg-emerald-100 px-3 py-0.5 text-xs font-medium text-emerald-900">
            Farm context: {farmId}
          </div>
        )}
      </div>

      {/* Rich Deliverables */}
      <div className="mt-8 pro-section">
        <h2 className="text-xl font-semibold mb-4">{isTh ? 'สิ่งที่คุณได้รับต่อการส่งออก 1 ครั้ง' : 'What You Receive Per Export'}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {deliverables.map((d, i) => (
            <div key={i} className="rounded-2xl border p-5 bg-white hover:border-[var(--color-sage)]/60 transition">
              <div className="text-3xl">{d.icon}</div>
              <div className="mt-3 font-semibold">{d.title}</div>
              <div className="text-sm mt-1 text-readable-muted">{d.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Data Sources + Integration */}
      <div className="mt-6 grid gap-6 lg:grid-cols-5">
        <div className="pro-section lg:col-span-3">
          <h3 className="font-semibold mb-3">Data Sources</h3>
          <div className="space-y-2 text-sm font-mono text-readable-muted">
            <div>POST /api/v1/smart-farm/ingest</div>
            <div>MQTT (TLS) → 43.128.75.149:8883</div>
            <div>Topic: obolla/farm/{farmId || '{farm_id}'}/telemetry</div>
          </div>
          <p className="mt-3 text-xs text-[var(--color-muted)]">All data comes directly from your sensors. No fabrication.</p>
        </div>

        <div className="pro-section lg:col-span-2 coffee-corner">
          <h3 className="font-semibold mb-2">How to Use</h3>
          <ul className="text-sm space-y-1.5 text-[var(--color-text-soft)]">
            <li>1. Connect your farm via Smart Farm page</li>
            <li>2. Export JSON or CSV directly</li>
            <li>3. Import into greenhouse automation, ML models, or dashboards</li>
            <li>4. Credit your farm operator + OBOLLA in published work</li>
          </ul>
        </div>
      </div>

      {/* Physical Loops - vertical competitors can't easily copy */}
      <div className="mt-4 pro-section border-amber-500/40">
        <h3 className="font-semibold mb-2 text-amber-700">Physical Loop: Agent ↔ Farm Machine</h3>
        <p className="text-sm">Live telemetry flows to agent → agent decides (e.g. adjust temp) → triggers real action via Bridge on the farm PC (local agent on machine).</p>
        <button onClick={() => alert('Demo: Agent triggered irrigation adjustment on local farm machine via Bridge.')} className="mt-3 rounded bg-amber-600 text-white px-3 py-1 text-xs">Simulate Agent Action on Physical Farm</button>
      </div>

      {/* Quick actions */}
      <div className="mt-8">
        <div className="flex flex-wrap gap-3">
          {farmId ? (
            <>
              <button disabled={busy} onClick={() => handleQuickExport('json')} className="touch-target rounded-2xl bg-[var(--color-market)] px-6 py-3 font-bold text-white text-sm disabled:opacity-60">
                {busy ? 'Preparing...' : 'Export JSON for this farm'}
              </button>
              <button disabled={busy} onClick={() => handleQuickExport('csv')} className="touch-target rounded-2xl border px-6 py-3 font-semibold text-sm">
                Export CSV
              </button>
            </>
          ) : (
            <Link to="/smart-farm" className="touch-target rounded-2xl bg-[var(--color-market)] px-7 py-3 text-sm font-bold text-white">
              Go to Smart Farm → connect your greenhouse
            </Link>
          )}

          <Link to="/japanese-melon-pack" className="touch-target rounded-2xl border px-6 py-3 text-sm">
            Dedicated page
          </Link>
        </div>
      </div>

      <div className="mt-10">
        <SecurityTrustStrip compact />
        <p className="text-center text-xs text-[var(--color-coffee)] mt-4">☕ Data that grows with your garden. Real sensors. Real value.</p>
      </div>
    </div>
  )
}
