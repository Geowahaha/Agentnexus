import { useEffect, useState, type FormEvent } from 'react'
import { api } from '../../api/client'
import type { BuyerReviewItem, WorkflowReviewEligibility } from '../../types'
import { BuyerReviewThreadModal } from './BuyerReviewThreadModal'

function StarPicker({
  value,
  onChange,
  disabled,
}: {
  value: number
  onChange: (rating: number) => void
  disabled?: boolean
}) {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={disabled}
          onClick={() => onChange(star)}
          className={`text-2xl transition-transform hover:scale-110 disabled:opacity-50 ${
            star <= value ? 'text-amber-400' : 'text-[var(--color-muted)]'
          }`}
          aria-label={`${star} stars`}
        >
          ★
        </button>
      ))}
    </div>
  )
}

type BuyerReviewPanelProps = {
  token: string
  workflowId: string
}

export function BuyerReviewPanel({ token, workflowId }: BuyerReviewPanelProps) {
  const [eligibility, setEligibility] = useState<WorkflowReviewEligibility | null>(null)
  const [loading, setLoading] = useState(true)
  const [rating, setRating] = useState(5)
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [submittedReview, setSubmittedReview] = useState<BuyerReviewItem | null>(null)
  const [showThread, setShowThread] = useState(false)

  useEffect(() => {
    setLoading(true)
    api
      .getWorkflowReviewEligibility(token, workflowId)
      .then((data) => {
        setEligibility(data)
        if (data.existing_review) setSubmittedReview(data.existing_review)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load review status'))
      .finally(() => setLoading(false))
  }, [token, workflowId])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!eligibility?.expert_skill_id || !comment.trim()) return
    setSubmitting(true)
    setError('')
    setSuccess('')
    try {
      const result = await api.submitBuyerReview(token, {
        workflow_id: workflowId,
        expert_skill_id: eligibility.expert_skill_id,
        rating,
        comment: comment.trim(),
      })
      setSubmittedReview(result.review)
      setSuccess(result.message)
      setEligibility((prev) =>
        prev ? { ...prev, already_reviewed: true, existing_review: result.review } : prev,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit review')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="mt-6 flex items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] py-10">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
      </div>
    )
  }

  if (!eligibility?.eligible) {
    return null
  }

  if (submittedReview || eligibility.already_reviewed) {
    const review = submittedReview ?? eligibility.existing_review
    if (!review) return null
    return (
      <div className="mt-6 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-semibold text-emerald-400">Your review</h2>
            <p className="mt-1 text-sm text-[var(--color-muted)]">
              {review.skill_name} · {'★'.repeat(review.rating)}
              {review.has_creator_reply && (
                <span className="ml-2 text-cyan-400">
                  · Creator replied
                  {review.unread_replies > 0 && ` (${review.unread_replies} new)`}
                </span>
              )}
            </p>
            <p className="mt-3 text-sm text-[var(--color-text-soft)]">{review.comment}</p>
          </div>
          <button
            type="button"
            onClick={() => setShowThread(true)}
            className="rounded-lg border border-cyan-500/40 px-4 py-2 text-sm text-cyan-400 hover:bg-cyan-500/10"
          >
            View thread
          </button>
        </div>
        {success && <p className="mt-3 text-sm text-emerald-400">{success}</p>}
        {showThread && (
          <BuyerReviewThreadModal
            token={token}
            reviewId={review.id}
            skillName={review.skill_name}
            onClose={() => setShowThread(false)}
          />
        )}
      </div>
    )
  }

  return (
    <div className="mt-6 rounded-xl border border-violet-500/30 bg-violet-500/5 p-5">
      <h2 className="font-semibold text-violet-300">Rate this Expert Skill</h2>
      <p className="mt-1 text-sm text-[var(--color-muted)]">
        Share your experience with {eligibility.skill_name}. Your review helps creators improve and
        builds trust for future buyers.
      </p>

      <form onSubmit={handleSubmit} className="mt-5 space-y-4">
        <div>
          <label className="mb-2 block text-xs font-medium uppercase tracking-wider text-[var(--color-muted)]">
            Rating
          </label>
          <StarPicker value={rating} onChange={setRating} disabled={submitting} />
        </div>
        <div>
          <label className="mb-2 block text-xs font-medium uppercase tracking-wider text-[var(--color-muted)]">
            Your review
          </label>
          <textarea
            required
            minLength={3}
            rows={4}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="What worked well? What could be better?"
            className="w-full rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-violet-500/50 focus:outline-none resize-y"
          />
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={submitting || comment.trim().length < 3}
          className="rounded-lg bg-violet-500 px-5 py-2.5 text-sm font-medium text-[var(--color-text)] hover:bg-violet-400 disabled:opacity-50"
        >
          {submitting ? 'Submitting…' : 'Submit review'}
        </button>
      </form>
    </div>
  )
}