import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import type { DnaAuditReport } from '../../types'

const STATUS_COLOR: Record<string, string> = {
  pass: 'text-emerald-600',
  warn: 'text-amber-600',
  fail: 'text-red-600',
}

export function DnaVerifiedPanel() {
  const { locale } = useLocale()
  const [report, setReport] = useState<DnaAuditReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    api
      .getDnaAudit()
      .then(setReport)
      .catch(() => setReport(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <section className="garden-card mt-8 p-6">
        <p className="text-sm text-[var(--color-muted)]">
          {locale === 'th' ? 'กำลังตรวจสอบ DNA…' : 'Verifying DNA alignment…'}
        </p>
      </section>
    )
  }

  if (!report) return null

  const status = report.overall_status
  const summary = report.summary
  const title =
    locale === 'th'
      ? summary.dna_aligned
        ? 'ตรวจสอบ DNA แล้ว — ทุกข้อพิสูจน์ได้'
        : 'ตรวจสอบ DNA — มีข้อที่ต้องแก้'
      : summary.dna_aligned
        ? 'DNA verified — claims backed by evidence'
        : 'DNA audit — action needed'

  return (
    <section className="garden-card mt-8 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-emerald-600">
            {locale === 'th' ? 'พิสูจน์ได้' : 'Provable trust'}
          </p>
          <h2 className="mt-1 text-xl font-bold text-[var(--color-text)]">{title}</h2>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            {locale === 'th'
              ? `${summary.passed}/${summary.total} ข้อผ่าน · ไม่มี eval/exec แอบแฝง · QA gate · ราคาซื่อสัตย์`
              : `${summary.passed}/${summary.total} checks passed · no hidden exec · QA gate · honest pricing`}
          </p>
          <p className={`mt-1 text-xs font-semibold uppercase ${STATUS_COLOR[status] ?? ''}`}>
            {status}
            {report.audited_at ? ` · ${new Date(report.audited_at).toLocaleString()}` : ''}
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:items-end">
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="rounded-lg border border-emerald-200 bg-white/80 px-4 py-2 text-sm font-semibold text-emerald-800 hover:bg-white"
          >
            {expanded
              ? locale === 'th'
                ? 'ซ่อนรายละเอียด'
                : 'Hide details'
              : locale === 'th'
                ? 'ดูหลักฐานทุกข้อ'
                : 'View all evidence'}
          </button>
          <Link to="/security" className="text-xs text-[var(--color-muted)] hover:text-emerald-700">
            {locale === 'th' ? 'นโยบายความปลอดภัย →' : 'Safety policy →'}
          </Link>
        </div>
      </div>

      {expanded && (
        <ul className="mt-6 space-y-3">
          {report.checks.map((check) => (
            <li
              key={check.id}
              className="rounded-xl border border-emerald-100 bg-white/70 p-4 text-sm"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className={`font-bold uppercase text-xs ${STATUS_COLOR[check.status] ?? ''}`}>
                  {check.status}
                </span>
                <span className="font-mono text-xs text-[var(--color-muted)]">{check.id}</span>
              </div>
              <p className="mt-1 font-medium text-[var(--color-text)]">
                {locale === 'th' ? check.claim_th : check.claim_en}
              </p>
              <p className="mt-1 text-xs text-[var(--color-muted)]">
                {locale === 'th' ? 'พิสูจน์โดย' : 'Proved by'}: {check.proved_by}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}