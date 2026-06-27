import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useNotifications } from '../hooks/useNotifications'
import type { NotificationEvent } from '../types'

type NotificationBellProps = {
  token: string
}

function reviewLink(item: NotificationEvent): string | null {
  const reviewId = item.payload.review_id
  const workflowId = item.payload.workflow_id
  if (item.event_type === 'new_review' && typeof reviewId === 'string') {
    return `/creator?tab=reviews&reviewId=${reviewId}`
  }
  if (
    (item.event_type === 'thread_reply' || item.event_type === 'thread_resolved') &&
    typeof workflowId === 'string' &&
    workflowId
  ) {
    return `/workflows/${workflowId}`
  }
  if (typeof reviewId === 'string') {
    return `/creator?tab=reviews&reviewId=${reviewId}`
  }
  return null
}

export function NotificationBell({ token }: NotificationBellProps) {
  const navigate = useNavigate()
  const { unreadCount, items, toast, connected, markAllRead, markOneRead } = useNotifications(token)
  const [open, setOpen] = useState(false)

  function handleClick(item: NotificationEvent) {
    void markOneRead(item.id)
    const link = reviewLink(item)
    if (link && !link.endsWith('/')) {
      navigate(link)
      setOpen(false)
    }
  }

  return (
    <div className="relative">
      {toast && (
        <button
          type="button"
          onClick={() => handleClick(toast)}
          className="fixed right-4 top-20 z-[60] max-w-sm rounded-lg border border-cyan-500/40 bg-[var(--color-surface-raised)] px-4 py-3 text-left shadow-xl transition hover:border-cyan-400"
        >
          <span className="block text-sm font-medium text-[var(--color-text)]">{toast.title}</span>
          <span className="mt-1 block text-xs text-[var(--color-muted)]">{toast.body}</span>
          <span className="mt-2 block text-xs text-cyan-400">Click to open →</span>
        </button>
      )}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="relative rounded-lg px-2.5 py-2 text-sm text-[var(--color-text-soft)] hover:bg-[var(--color-surface-overlay)] hover:text-[var(--color-text)]"
        aria-label="Notifications"
        title={connected ? 'Live notifications' : 'Connecting…'}
      >
        🔔
        {connected && (
          <span className="absolute bottom-0.5 left-1 h-1.5 w-1.5 rounded-full bg-emerald-400" />
        )}
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-cyan-500 px-1 text-[10px] font-bold text-slate-900">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] shadow-2xl">
          <div className="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3">
            <p className="text-sm font-semibold text-[var(--color-text)]">
              Notifications
              {connected && <span className="ml-2 text-[10px] text-emerald-400">LIVE</span>}
            </p>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={() => markAllRead()}
                className="text-xs text-cyan-400 hover:underline"
              >
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-72 overflow-y-auto">
            {items.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-[var(--color-muted)]">No notifications yet</p>
            ) : (
              items.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleClick(item)}
                  className={`w-full border-b border-[var(--color-border)] px-4 py-3 text-left last:border-0 hover:bg-[var(--color-surface)] ${
                    !item.is_read ? 'bg-cyan-500/5' : ''
                  }`}
                >
                  <span className="block text-sm font-medium text-[var(--color-text)]">{item.title}</span>
                  <span className="mt-0.5 block text-xs text-[var(--color-muted)]">{item.body}</span>
                  <span className="mt-2 block text-xs text-cyan-400">Open thread →</span>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}