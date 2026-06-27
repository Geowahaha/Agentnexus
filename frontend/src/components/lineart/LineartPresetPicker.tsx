import {
  defaultEditStyleId,
  editStylesForFormat,
  LINEART_TOPIC_PRESETS,
  type LineartFormat,
  type LineartPresetSelection,
} from '../../config/lineartKemlifePresets'

type Props = {
  format: LineartFormat
  locale: 'th' | 'en'
  selection: LineartPresetSelection
  onChange: (next: LineartPresetSelection) => void
  compact?: boolean
}

export function LineartPresetPicker({ format, locale, selection, onChange, compact }: Props) {
  const isTh = locale === 'th'
  const editStyles = editStylesForFormat(format)

  function setTopic(topicId: string) {
    onChange({ ...selection, topicId, format })
  }

  function setEditStyle(editStyleId: string) {
    onChange({ ...selection, editStyleId, format })
  }

  function setLanguage(language: 'th' | 'en') {
    onChange({ ...selection, language })
  }

  const chipClass = (active: boolean) =>
    `rounded-lg border px-3 py-2 text-sm font-semibold transition-colors ${
      active
        ? 'border-[var(--color-market)] bg-[var(--color-market)]/10 text-[var(--color-market-hover)]'
        : 'border-[var(--color-border)] bg-white/80 text-[var(--color-text-soft)] hover:border-[var(--color-sage)]/60 hover:text-[var(--color-text)]'
    }`

  return (
    <div className={compact ? 'space-y-4' : 'space-y-5 rounded-xl border border-[var(--color-sage)]/30 bg-[var(--color-surface-overlay)]/40 p-4 sm:p-5'}>
      <div>
        <p className="form-label mb-2">
          {isTh ? 'หัวข้อ (เลือกได้)' : 'Topic (pick one)'}
        </p>
        <div className="flex flex-wrap gap-2">
          {LINEART_TOPIC_PRESETS.map((topic) => (
            <button
              key={topic.id}
              type="button"
              onClick={() => setTopic(topic.id)}
              className={chipClass(selection.topicId === topic.id)}
              title={isTh ? topic.brief_th : topic.brief_en}
            >
              {isTh ? topic.label_th : topic.label_en}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="form-label mb-2">
          {isTh ? 'สไตล์ตัดต่อ (เลือกได้)' : 'Edit style (pick one)'}
        </p>
        <div className="flex flex-wrap gap-2">
          {editStyles.map((style) => (
            <button
              key={style.id}
              type="button"
              onClick={() => setEditStyle(style.id)}
              className={chipClass(selection.editStyleId === style.id)}
              title={isTh ? style.notes_th : style.notes_en}
            >
              {isTh ? style.label_th : style.label_en}
            </button>
          ))}
        </div>
        {selection.editStyleId && (
          <p className="mt-2 text-xs font-medium text-readable-muted">
            {isTh
              ? editStyles.find((s) => s.id === selection.editStyleId)?.notes_th
              : editStyles.find((s) => s.id === selection.editStyleId)?.notes_en}
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-end gap-4">
        <div>
          <p className="form-label mb-2">{isTh ? 'ภาษาบท' : 'Script language'}</p>
          <div className="flex gap-2">
            <button type="button" onClick={() => setLanguage('th')} className={chipClass(selection.language === 'th')}>
              ไทย
            </button>
            <button type="button" onClick={() => setLanguage('en')} className={chipClass(selection.language === 'en')}>
              English
            </button>
          </div>
        </div>

        {selection.topicId === 'custom' && (
          <div className="min-w-[200px] flex-1">
            <label className="form-label mb-1.5 block">
              {isTh ? 'หัวข้อเฉพาะ' : 'Your specific topic'}
            </label>
            <input
              type="text"
              value={selection.customTopic ?? ''}
              onChange={(e) => onChange({ ...selection, customTopic: e.target.value })}
              placeholder={isTh ? 'เช่น ทำไมคุณลืมความฝัน' : 'e.g. Why you forget dreams'}
              className="form-input"
            />
          </div>
        )}
      </div>
    </div>
  )
}

export function defaultLineartSelection(format: LineartFormat, locale: 'th' | 'en'): LineartPresetSelection {
  return {
    format,
    topicId: 'body-secrets',
    editStyleId: defaultEditStyleId(format),
    language: locale,
  }
}