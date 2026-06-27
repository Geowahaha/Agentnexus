import { useEffect, useRef, useState, type FormEvent } from 'react'
import { api } from '../../api/client'
import type { QuickReply, ReviewInboxItem, ReviewThread, ThreadMessage } from '../../types'

function Stars({ rating }: { rating: number }) {
  return (
    <span className="text-amber-400 text-sm">
      {'★'.repeat(rating)}
      <span className="text-[var(--color-muted)]">{'★'.repeat(5 - rating)}</span>
    </span>
  )
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

type ReviewThreadModalProps = {
  token: string
  item: ReviewInboxItem
  onClose: () => void
  onUpdated: () => void
}

export function ReviewThreadModal({ token, item, onClose, onUpdated }: ReviewThreadModalProps) {
  const [thread, setThread] = useState<ReviewThread | null>(null)
  const [quickReplies, setQuickReplies] = useState<QuickReply[]>([])
  const [message, setMessage] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [resolving, setResolving] = useState(false)
  const [error, setError] = useState('')
  const [successPulse, setSuccessPulse] = useState(false)
  const [showQuickReplies, setShowQuickReplies] = useState(false)
  const [showManageReplies, setShowManageReplies] = useState(false)
  const [newReplyTitle, setNewReplyTitle] = useState('')
  const [newReplyBody, setNewReplyBody] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setLoading(true)
    setError('')
    Promise.all([api.getReviewThread(token, item.id), api.getQuickReplies(token)])
      .then(([t, replies]) => {
        setThread(t)
        setQuickReplies(replies)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load thread'))
      .finally(() => setLoading(false))
  }, [token, item.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [thread?.messages.length])

  async function handleSend(e: FormEvent) {
    e.preventDefault()
    if (!message.trim() && files.length === 0) return
    setSending(true)
    setError('')
    try {
      const sent = await api.replyToReview(token, item.id, message.trim() || '(attachment)', files)
      setThread((prev) =>
        prev
          ? {
              ...prev,
              status: prev.status === 'unread' ? 'replied' : prev.status,
              messages: [...prev.messages, sent],
            }
          : prev,
      )
      setMessage('')
      setFiles([])
      setSuccessPulse(true)
      setTimeout(() => setSuccessPulse(false), 1200)
      onUpdated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send reply')
    } finally {
      setSending(false)
    }
  }

  async function handleResolve() {
    setResolving(true)
    setError('')
    try {
      await api.resolveReview(token, item.id)
      setThread((prev) => (prev ? { ...prev, status: 'resolved' } : prev))
      onUpdated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve')
    } finally {
      setResolving(false)
    }
  }

  async function handleAddQuickReply() {
    if (!newReplyTitle.trim() || !newReplyBody.trim()) return
    try {
      const created = await api.createQuickReply(token, {
        title: newReplyTitle.trim(),
        body: newReplyBody.trim(),
      })
      setQuickReplies((prev) => [...prev, created])
      setNewReplyTitle('')
      setNewReplyBody('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save quick reply')
    }
  }

  function applyQuickReply(reply: QuickReply) {
    setMessage(reply.body)
    setShowQuickReplies(false)
  }

  function renderMessage(msg: ThreadMessage) {
    const isCreator = msg.sender_role === 'creator'
    return (
      <div key={msg.id} className={`flex ${isCreator ? 'justify-end' : 'justify-start'}`}>
        <div
          className={`max-w-[85%] rounded-2xl px-4 py-3 ${
            isCreator
              ? 'rounded-br-md bg-cyan-500/15 border border-cyan-500/30'
              : 'rounded-bl-md bg-[var(--color-surface-overlay)] border border-[var(--color-border)]'
          }`}
        >
          <div className="mb-1 flex items-center gap-2 text-xs text-[var(--color-muted)]">
            <span className="font-medium text-[var(--color-text-soft)]">{msg.sender_name}</span>
            {msg.is_initial_review && (
              <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] text-amber-400">Review</span>
            )}
            <span>{formatDateTime(msg.created_at)}</span>
          </div>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-200">{msg.body}</p>
          {msg.attachments.length > 0 && (
            <ul className="mt-2 space-y-1">
              {msg.attachments.map((att) => (
                <li key={att.id}>
                  <button
                    type="button"
                    onClick={() => api.downloadReviewAttachment(token, att.id, att.file_name)}
                    className="inline-flex items-center gap-1.5 rounded-md bg-black/20 px-2 py-1 text-xs text-cyan-300 hover:text-cyan-200"
                  >
                    📎 {att.file_name}
                    <span className="text-[var(--color-muted)]">({formatFileSize(att.file_size)})</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-end justify-center bg-black/70 p-0 sm:items-center sm:p-4">
      <div
        className={`flex h-[95vh] w-full max-w-2xl flex-col rounded-t-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] shadow-2xl sm:h-[85vh] sm:rounded-2xl ${
          successPulse ? 'ring-2 ring-emerald-400/50' : ''
        }`}
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-start justify-between border-b border-[var(--color-border)] px-5 py-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-cyan-400">Review Thread</p>
            <h2 className="mt-0.5 text-lg font-semibold text-[var(--color-text)]">{item.skill_name}</h2>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-[var(--color-muted)]">
              <span>{item.buyer_name}</span>
              <Stars rating={item.rating} />
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-medium uppercase ${
                  thread?.status === 'resolved'
                    ? 'bg-slate-500/20 text-[var(--color-muted)]'
                    : thread?.status === 'replied'
                      ? 'bg-emerald-500/15 text-emerald-400'
                      : 'bg-amber-500/15 text-amber-400'
                }`}
              >
                {thread?.status ?? item.status}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-[var(--color-muted)] hover:bg-[var(--color-surface-overlay)] hover:text-[var(--color-text)]"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {loading && <p className="text-sm text-[var(--color-muted)]">Loading conversation…</p>}
          {error && (
            <div className="mb-3 rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              {error}
            </div>
          )}
          {thread && (
            <div className="space-y-4">
              {thread.messages.map(renderMessage)}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {thread?.status !== 'resolved' && (
          <form onSubmit={handleSend} className="border-t border-[var(--color-border)] px-5 py-4">
            <div className="mb-2 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setShowQuickReplies((v) => !v)}
                className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs text-[var(--color-text-soft)] hover:border-cyan-500/40"
              >
                Quick Replies
              </button>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs text-[var(--color-text-soft)] hover:border-cyan-500/40"
              >
                Attach file
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*,.pdf,.doc,.docx,.txt"
                className="hidden"
                onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
              />
              {files.length > 0 && (
                <span className="text-xs text-cyan-400">{files.length} file(s) selected</span>
              )}
            </div>

            {showQuickReplies && (
              <div className="mb-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-xs font-medium text-[var(--color-muted)]">Quick Replies</p>
                  <button
                    type="button"
                    onClick={() => setShowManageReplies((v) => !v)}
                    className="text-xs text-cyan-400"
                  >
                    {showManageReplies ? 'Done' : 'Manage'}
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {quickReplies.map((reply) => (
                    <button
                      key={reply.id}
                      type="button"
                      onClick={() => applyQuickReply(reply)}
                      className="rounded-lg bg-[var(--color-surface-overlay)] px-3 py-1.5 text-left text-xs text-[var(--color-text-soft)] hover:bg-cyan-500/10 hover:text-cyan-200"
                      title={reply.body}
                    >
                      {reply.title}
                    </button>
                  ))}
                </div>
                {showManageReplies && (
                  <div className="mt-3 space-y-2 border-t border-[var(--color-border)] pt-3">
                    {quickReplies.map((reply) => (
                      <div key={reply.id} className="flex items-start justify-between gap-2 text-xs">
                        <span className="text-[var(--color-muted)] line-clamp-2">{reply.body}</span>
                        <button
                          type="button"
                          onClick={() =>
                            api.deleteQuickReply(token, reply.id).then(() =>
                              setQuickReplies((prev) => prev.filter((r) => r.id !== reply.id)),
                            )
                          }
                          className="shrink-0 text-red-400"
                        >
                          Delete
                        </button>
                      </div>
                    ))}
                    <div className="grid gap-2 sm:grid-cols-2">
                      <input
                        value={newReplyTitle}
                        onChange={(e) => setNewReplyTitle(e.target.value)}
                        placeholder="Template title"
                        className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1.5 text-xs text-white"
                      />
                      <input
                        value={newReplyBody}
                        onChange={(e) => setNewReplyBody(e.target.value)}
                        placeholder="Template message"
                        className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1.5 text-xs text-white sm:col-span-2"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={handleAddQuickReply}
                      className="text-xs text-cyan-400 hover:text-cyan-300"
                    >
                      + Add template
                    </button>
                  </div>
                )}
              </div>
            )}

            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={3}
              placeholder="Type your reply…"
              className="w-full resize-none rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-sm text-white placeholder:text-[var(--color-muted)]"
            />
            <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
              <button
                type="button"
                disabled={resolving || thread?.status === 'resolved'}
                onClick={handleResolve}
                className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm text-[var(--color-text-soft)] hover:border-emerald-500/40 disabled:opacity-40"
              >
                {resolving ? 'Resolving…' : 'Mark as Resolved'}
              </button>
              <button
                type="submit"
                disabled={sending || (!message.trim() && files.length === 0)}
                className="rounded-lg bg-cyan-500 px-5 py-2 text-sm font-semibold text-slate-900 disabled:opacity-50 hover:bg-cyan-400"
              >
                {sending ? 'Sending…' : 'Send Reply'}
              </button>
            </div>
          </form>
        )}

        {thread?.status === 'resolved' && (
          <div className="border-t border-[var(--color-border)] px-5 py-4 text-center text-sm text-emerald-400">
            This review thread is resolved.
          </div>
        )}
      </div>
    </div>
  )
}