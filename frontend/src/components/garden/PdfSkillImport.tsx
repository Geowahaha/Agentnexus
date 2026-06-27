import { useRef, useState, type ChangeEvent, type DragEvent } from 'react'

type Props = {
  locale: 'th' | 'en'
  disabled?: boolean
  importing?: boolean
  onImport: (file: File) => void
  labels: {
    title: string
    hint: string
    drop: string
    browse: string
    maxSize: string
    importing: string
  }
}

export function PdfSkillImport({ locale, disabled, importing, onImport, labels }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  function pickFile(file: File | undefined) {
    if (!file || disabled || importing) return
    onImport(file)
  }

  function onInputChange(e: ChangeEvent<HTMLInputElement>) {
    pickFile(e.target.files?.[0])
    e.target.value = ''
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragOver(false)
    pickFile(e.dataTransfer.files?.[0])
  }

  return (
    <div className="rounded-xl border-2 border-dashed border-[var(--color-sage)]/50 bg-white/60 p-4 sm:p-5">
      <p className="text-base font-semibold text-[var(--color-text)]">{labels.title}</p>
      <p className="mt-1 text-sm font-medium text-readable-muted">{labels.hint}</p>
      <div
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click()
        }}
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`mt-4 cursor-pointer rounded-xl border-2 px-4 py-8 text-center transition-colors ${
          dragOver
            ? 'border-[var(--color-market)] bg-[var(--color-market)]/5'
            : 'border-[var(--color-border)] bg-white hover:border-[var(--color-sage)]'
        } ${disabled || importing ? 'pointer-events-none opacity-60' : ''}`}
      >
        <p className="text-sm font-semibold text-[var(--color-text)]">
          {importing ? labels.importing : labels.drop}
        </p>
        <p className="mt-2 text-xs font-medium text-readable-muted">{labels.maxSize}</p>
        <span className="mt-4 inline-block rounded-lg bg-[var(--color-market)] px-4 py-2 text-sm font-bold text-white">
          {labels.browse}
        </span>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="sr-only"
        onChange={onInputChange}
        aria-label={labels.browse}
      />
      <p className="mt-2 text-xs text-readable-muted">
        {locale === 'th'
          ? 'ฟรี $0 · ไม่เก็บไฟล์บนเซิร์ฟเวอร์ · อ่านแล้วจัด skill ให้ทันที'
          : 'Free $0 · PDF not stored · we read it and draft your skill'}
      </p>
    </div>
  )
}