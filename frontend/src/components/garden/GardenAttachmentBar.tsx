import { useRef, useState, type ChangeEvent } from 'react'
import type { GardenAttachment } from './gardenAttachments'
import { newAttachmentId } from './gardenAttachments'

type Props = {
  locale: 'th' | 'en'
  disabled?: boolean
  pdfImporting?: boolean
  onPdfImport: (file: File) => void
  onAttachmentsChange: (next: GardenAttachment[]) => void
  attachments: GardenAttachment[]
  labels: {
    attach: string
    pdf: string
    image: string
    link: string
    linkPrompt: string
    addLink: string
    cancel: string
  }
}

export function GardenAttachmentBar({
  locale,
  disabled,
  pdfImporting,
  onPdfImport,
  onAttachmentsChange,
  attachments,
  labels,
}: Props) {
  const pdfRef = useRef<HTMLInputElement>(null)
  const imageRef = useRef<HTMLInputElement>(null)
  const [linkOpen, setLinkOpen] = useState(false)
  const [linkDraft, setLinkDraft] = useState('')

  function addAttachment(att: GardenAttachment) {
    onAttachmentsChange([...attachments, att])
  }

  function removeAttachment(id: string) {
    const removed = attachments.find((a) => a.id === id)
    if (removed?.kind === 'image') URL.revokeObjectURL(removed.previewUrl)
    onAttachmentsChange(attachments.filter((a) => a.id !== id))
  }

  function onPdfChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || disabled || pdfImporting) return
    addAttachment({ id: newAttachmentId(), kind: 'pdf', name: file.name })
    onPdfImport(file)
  }

  function onImageChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || disabled) return
    addAttachment({
      id: newAttachmentId(),
      kind: 'image',
      name: file.name,
      previewUrl: URL.createObjectURL(file),
    })
  }

  function submitLink() {
    const url = linkDraft.trim()
    if (!url || disabled) return
    try {
      // eslint-disable-next-line no-new
      new URL(url)
    } catch {
      return
    }
    addAttachment({ id: newAttachmentId(), kind: 'link', url })
    setLinkDraft('')
    setLinkOpen(false)
  }

  const btnClass =
    'inline-flex min-h-[44px] min-w-[44px] flex-1 items-center justify-center gap-1.5 rounded-xl border border-[var(--color-border)] bg-white px-3 py-2.5 text-sm font-semibold text-[var(--color-text)] transition-colors hover:border-[var(--color-sage)] hover:bg-[var(--color-surface-overlay)] disabled:opacity-50 sm:flex-none sm:px-4'

  return (
    <div className="space-y-3">
      {attachments.length > 0 && (
        <ul className="flex flex-wrap gap-2">
          {attachments.map((att) => (
            <li
              key={att.id}
              className="flex max-w-full items-center gap-2 rounded-full border border-[var(--color-border)] bg-white px-3 py-1.5 text-xs font-medium text-[var(--color-text)]"
            >
              {att.kind === 'image' && (
                <img src={att.previewUrl} alt="" className="h-6 w-6 rounded object-cover" />
              )}
              <span className="truncate max-w-[10rem] sm:max-w-[14rem]">
                {att.kind === 'link' ? att.url : att.name}
              </span>
              <button
                type="button"
                onClick={() => removeAttachment(att.id)}
                className="shrink-0 text-[var(--color-muted)] hover:text-red-600"
                aria-label={locale === 'th' ? 'ลบ' : 'Remove'}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={disabled || pdfImporting}
          onClick={() => pdfRef.current?.click()}
          className={btnClass}
        >
          <span aria-hidden>📄</span>
          <span>{pdfImporting ? '…' : labels.pdf}</span>
        </button>
        <button type="button" disabled={disabled} onClick={() => imageRef.current?.click()} className={btnClass}>
          <span aria-hidden>🖼️</span>
          <span>{labels.image}</span>
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={() => setLinkOpen((v) => !v)}
          className={btnClass}
        >
          <span aria-hidden>🔗</span>
          <span>{labels.link}</span>
        </button>
      </div>

      {linkOpen && (
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            type="url"
            inputMode="url"
            value={linkDraft}
            onChange={(e) => setLinkDraft(e.target.value)}
            placeholder={labels.linkPrompt}
            className="min-h-[44px] flex-1 rounded-xl border-2 border-[var(--color-border)] bg-white px-4 text-base text-[var(--color-text)] focus:border-[var(--color-sage)] focus:outline-none"
          />
          <button
            type="button"
            onClick={submitLink}
            disabled={!linkDraft.trim()}
            className="min-h-[44px] rounded-xl bg-[var(--color-market)] px-4 text-sm font-bold text-white disabled:opacity-50"
          >
            {labels.addLink}
          </button>
          <button
            type="button"
            onClick={() => {
              setLinkOpen(false)
              setLinkDraft('')
            }}
            className="min-h-[44px] rounded-xl border border-[var(--color-border)] px-4 text-sm font-medium text-[var(--color-muted)]"
          >
            {labels.cancel}
          </button>
        </div>
      )}

      <input ref={pdfRef} type="file" accept="application/pdf,.pdf" className="sr-only" onChange={onPdfChange} />
      <input ref={imageRef} type="file" accept="image/*" className="sr-only" onChange={onImageChange} />
    </div>
  )
}