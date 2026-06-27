import { useEffect, useRef, useState, type FormEvent } from 'react'
import { api } from '../../api/client'
import type { ReviewThread } from '../../types'

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

type BuyerReviewThreadModalProps = {
  token: string
  reviewId: string
  skillName: string
  onClose: () => void
}

export function BuyerReviewThreadModal({ token, reviewId, skillName, onClose }: BuyerReviewThreadModalProps) {
  const [thread, setThread] = useState<ReviewThread | null>(null)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  function loadThread() {
    setLoading(true)
    api
      .getBuyerReviewThread(token, reviewId)
      .then(setThread)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load thread'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadThread()
  }, [token, reviewId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [thread?.messages.length])

  async function handleSend(e: FormEvent) {
    e.preventDefault()
    if (!message.trim()) return
    setSending(true)
    setError('')
    try {
      const sent = await api.replyAsBuyer(token, reviewId, message.trim())
      setThread((prev) => (prev ? { ...prev, messages: [...prev.messages, sent] } : prev))
      setMessage('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-4 sm:items-center">
      <div className="flex max-h-[90vh] w-full max-w-lg flex-col rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] shadow-2xl">
        <div className="flex items-center justify-between border-b border-[var(--color-border)] px-5 py-4">
          <div>
            <h3 className="font-semibold text-[var(--color-text)]">Review thread</h3>
            <p className="text-xs text-[var(--color-muted)]">{skillName}</p>
          </div>
          <button type="button" onClick={onClose} className="text-[var(--color-muted)] hover:text-[var(--color-text)]">
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {loading && (
            <div className="flex justify-center py-10">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
            </div>
          )}
          {error && !loading && <p className="text-sm text-red-400">{error}</p>}
          {thread && (
            <div className="space-y-3">
              {thread.messages.map((msg) => {
                const isBuyer = msg.sender_role === 'buyer'
                return (
                  <div key={msg.id} className={`flex ${isBuyer ? 'justify-end' : 'justify-start'}`}>
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
                        isBuyer
                          ? 'rounded-br-md bg-violet-500/20 text-violet-100'
                          : 'rounded-bl-md bg-cyan-500/15 text-cyan-50'
                      }`}
                    >
                      <p className="text-[10px] font-medium uppercase tracking-wider opacity-70">
                        {msg.sender_name} · {formatDateTime(msg.created_at)}
                      </p>
                      <p className="mt-1 whitespace-pre-wrap">{msg.body}</p>
                    </div>
                  </div>
                )
              })}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {thread && thread.status !== 'resolved' && (
          <form onSubmit={handleSend} className="border-t border-[var(--color-border)] p-4">
            <div className="flex gap-2">
              <input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Reply to creator…"
                className="flex-1 rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)]"
              />
              <button
                type="submit"
                disabled={sending || !message.trim()}
                className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-medium text-slate-900 disabled:opacity-50"
              >
                Send
              </button>
            </div>
          </form>
        )}
        {thread?.status === 'resolved' && (
          <p className="border-t border-[var(--color-border)] px-4 py-3 text-center text-xs text-[var(--color-muted)]">
            This review has been marked resolved by the creator.
          </p>
        )}
      </div>
    </div>
  )
}