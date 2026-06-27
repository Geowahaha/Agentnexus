import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { ReviewInboxItem, ReviewInboxResponse, ReviewNotificationSettings } from '../../types'
import { ReviewThreadModal } from './ReviewThreadModal'

function Stars({ rating }: { rating: number }) {
  return (
    <span className="text-amber-400 text-sm">
      {'★'.repeat(rating)}
      <span className="text-[var(--color-muted)]">{'★'.repeat(5 - rating)}</span>
    </span>
  )
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function statusBadge(status: string) {
  if (status === 'resolved') return 'bg-slate-500/15 text-[var(--color-muted)]'
  if (status === 'replied') return 'bg-emerald-500/15 text-emerald-400'
  return 'bg-amber-500/15 text-amber-400'
}

function statusLabel(status: string) {
  if (status === 'resolved') return 'Resolved'
  if (status === 'replied') return 'Replied'
  return 'Unread'
}

type ReviewInboxProps = {
  token: string
  onBadgeChange?: (count: number) => void
  openReviewId?: string | null
}

export function ReviewInbox({ token, onBadgeChange, openReviewId }: ReviewInboxProps) {
  const [inbox, setInbox] = useState<ReviewInboxResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [ratingFilter, setRatingFilter] = useState<number | ''>('')
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<'newest' | 'unanswered' | 'response_time'>('newest')
  const [activeThread, setActiveThread] = useState<ReviewInboxItem | null>(null)
  const [notifySettings, setNotifySettings] = useState<ReviewNotificationSettings | null>(null)
  const [showNotifySettings, setShowNotifySettings] = useState(false)
  const [toast, setToast] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api.getReviewInbox(token, {
        status: statusFilter === 'all' ? undefined : statusFilter,
        rating: ratingFilter === '' ? undefined : ratingFilter,
        search: search.trim() || undefined,
        sort,
      })
      setInbox(data)
      onBadgeChange?.(data.stats.unread_count)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load inbox')
    } finally {
      setLoading(false)
    }
  }, [token, statusFilter, ratingFilter, search, sort, onBadgeChange])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (!openReviewId || !inbox?.items.length) return
    const target = inbox.items.find((item) => item.id === openReviewId)
    if (target) setActiveThread(target)
  }, [openReviewId, inbox?.items])

  useEffect(() => {
    api.getReviewNotificationSettings(token).then(setNotifySettings).catch(() => null)
  }, [token])

  useEffect(() => {
    const interval = setInterval(() => {
      Promise.all([api.getReviewInboxBadge(token), api.getNotificationBadge(token)])
        .then(([badge, notif]) => {
          onBadgeChange?.(badge.unread_count)
          const hasNewReview = notif.unread_count > 0
          if (badge.unread_count > (inbox?.stats.unread_count ?? 0) || hasNewReview) {
            setToast('New review activity')
            setTimeout(() => setToast(''), 4000)
            if (notifySettings?.notify_mode === 'all') load()
          }
        })
        .catch(() => null)
    }, 15000)
    return () => clearInterval(interval)
  }, [token, inbox?.stats.unread_count, notifySettings?.notify_mode, load, onBadgeChange])

  async function updateNotifyMode(mode: 'all' | 'unread_only') {
    const updated = await api.updateReviewNotificationSettings(token, mode)
    setNotifySettings(updated)
    setShowNotifySettings(false)
  }

  if (loading && !inbox) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
      </div>
    )
  }

  const stats = inbox?.stats

  return (
    <div className="space-y-6">
      {toast && (
        <div className="animate-pulse rounded-lg border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-sm text-cyan-300">
          {toast}
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">{error}</div>
      )}

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-[var(--color-text)]">Review Inbox</h2>
          <p className="text-sm text-[var(--color-muted)]">Respond to buyers and build trust through conversation.</p>
        </div>
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowNotifySettings((v) => !v)}
            className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm text-[var(--color-text-soft)] hover:border-cyan-500/40"
          >
            🔔 Notifications
          </button>
          {showNotifySettings && notifySettings && (
            <div className="absolute right-0 z-10 mt-2 w-56 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-3 shadow-xl">
              <p className="mb-2 text-xs font-medium text-[var(--color-muted)]">Alert me when</p>
              <label className="flex items-center gap-2 py-1 text-sm text-[var(--color-text-soft)]">
                <input
                  type="radio"
                  checked={notifySettings.notify_mode === 'all'}
                  onChange={() => updateNotifyMode('all')}
                />
                Every new review
              </label>
              <label className="flex items-center gap-2 py-1 text-sm text-[var(--color-text-soft)]">
                <input
                  type="radio"
                  checked={notifySettings.notify_mode === 'unread_only'}
                  onChange={() => updateNotifyMode('unread_only')}
                />
                Unread only
              </label>
            </div>
          )}
        </div>
      </div>

      {stats && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {[
            { label: 'Average Rating', value: stats.average_rating != null ? `${stats.average_rating.toFixed(1)} ★` : '—' },
            { label: 'Total Reviews', value: String(stats.total_reviews) },
            { label: 'Unread', value: String(stats.unread_count) },
            { label: 'Response Rate', value: `${stats.response_rate_percent}%` },
            {
              label: 'Avg Response',
              value: stats.average_response_time_label ?? '—',
            },
          ].map((card) => (
            <div
              key={card.label}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-4"
            >
              <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-muted)]">{card.label}</p>
              <p className="mt-1 font-mono text-lg font-semibold text-[var(--color-text)]">{card.value}</p>
            </div>
          ))}
        </div>
      )}

      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search buyer or skill…"
            className="flex-1 rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)]"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)]"
          >
            <option value="all">All</option>
            <option value="unread">Unread</option>
            <option value="replied">Replied</option>
            <option value="resolved">Resolved</option>
          </select>
          <select
            value={ratingFilter}
            onChange={(e) => setRatingFilter(e.target.value ? Number(e.target.value) : '')}
            className="rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)]"
          >
            <option value="">All ratings</option>
            {[5, 4, 3, 2, 1].map((n) => (
              <option key={n} value={n}>{n} stars</option>
            ))}
          </select>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as typeof sort)}
            className="rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)]"
          >
            <option value="newest">Newest first</option>
            <option value="unanswered">Unanswered first</option>
            <option value="response_time">Response time</option>
          </select>
        </div>
      </div>

      {!inbox?.items.length ? (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] py-16 text-center">
          <p className="text-4xl">💬</p>
          <p className="mt-3 text-[var(--color-muted)]">No reviews match your filters.</p>
          <p className="mt-1 text-sm text-[var(--color-muted)]">Reviews appear when buyers run your Expert Skills.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {inbox.items.map((item) => (
            <article
              key={item.id}
              className={`rounded-xl border bg-[var(--color-surface-raised)] p-4 transition-colors hover:border-cyan-500/30 ${
                item.status === 'unread' ? 'border-amber-500/30' : 'border-[var(--color-border)]'
              }`}
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex gap-3">
                  <img
                    src={item.buyer_avatar_url ?? undefined}
                    alt=""
                    className="h-10 w-10 shrink-0 rounded-full bg-[var(--color-surface-overlay)]"
                  />
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-medium text-[var(--color-text)]">{item.buyer_name}</p>
                      <Stars rating={item.rating} />
                      <span className="text-xs text-[var(--color-muted)]">{formatDate(item.created_at)}</span>
                    </div>
                    <p className="mt-0.5 text-xs text-cyan-400">{item.skill_name}</p>
                    <p className="mt-2 text-sm leading-relaxed text-[var(--color-text-soft)] line-clamp-2">{item.comment_preview}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                      <span className={`rounded-full px-2 py-0.5 font-medium ${statusBadge(item.status)}`}>
                        {statusLabel(item.status)}
                      </span>
                      {item.response_time_hours != null && (
                        <span className="text-[var(--color-muted)]">
                          Responded in {item.response_time_hours < 1
                            ? `${Math.round(item.response_time_hours * 60)}m`
                            : `${item.response_time_hours.toFixed(1)}h`}
                        </span>
                      )}
                      <span className="text-[var(--color-muted)]">{item.message_count} messages</span>
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveThread(item)}
                  className="shrink-0 rounded-lg bg-cyan-500/15 px-4 py-2 text-sm font-medium text-cyan-300 hover:bg-cyan-500/25"
                >
                  View Thread
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      {activeThread && (
        <ReviewThreadModal
          token={token}
          item={activeThread}
          onClose={() => setActiveThread(null)}
          onUpdated={load}
        />
      )}
    </div>
  )
}