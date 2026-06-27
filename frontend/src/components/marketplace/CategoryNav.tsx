import { useLocale } from '../../context/LocaleContext'
import type { StringKey } from '../../i18n/strings'

const CATEGORIES: { id: string; labelKey: StringKey; sub?: string[] }[] = [
  { id: '', labelKey: 'categoryAll' },
  { id: 'coding', labelKey: 'categoryCoding', sub: ['Agent plans', 'Code review', 'Local LoRA'] },
  { id: 'research', labelKey: 'categoryResearch', sub: ['Market intel', 'Competitive scan', 'Data extraction'] },
  { id: 'content', labelKey: 'categoryContent', sub: ['Copywriting', 'Localization', 'Repurposing'] },
  { id: 'quality', labelKey: 'categoryQuality', sub: ['QA review', 'Accessibility', 'Compliance'] },
  { id: 'seo', labelKey: 'categorySeo', sub: ['AI visibility', 'Technical SEO', 'Schema fixes'] },
  { id: 'support', labelKey: 'categorySupport', sub: ['Bridge assist', 'Guided fixes', 'Creator handoff'] },
]

export function CategoryNav({
  active,
  onChange,
}: {
  active: string
  onChange: (id: string) => void
}) {
  const { tr } = useLocale()
  const activeCat = CATEGORIES.find((c) => c.id === active) ?? CATEGORIES[0]

  return (
    <div className="relative z-10 border-b border-[var(--color-border)]/70 bg-white/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-1 px-4 py-2 sm:px-6">
        {CATEGORIES.map((cat) => (
          <div key={cat.id || 'all'} className="relative group">
            <button
              type="button"
              onClick={() => onChange(cat.id)}
              className={`rounded-full px-3 py-1.5 text-sm font-semibold transition-colors ${
                active === cat.id
                  ? 'category-pill-active'
                  : 'text-[var(--color-text-soft)] hover:bg-[var(--color-surface-overlay)] hover:text-[var(--color-text)]'
              }`}
            >
              {tr(cat.labelKey)}
            </button>
            {cat.sub && active === cat.id && (
              <div className="absolute left-0 top-full z-40 mt-1 hidden min-w-[200px] market-dropdown p-2 group-hover:block">
                {cat.sub.map((item) => (
                  <p key={item} className="rounded px-2 py-1.5 text-sm font-medium hover:bg-black/5">
                    {item}
                  </p>
                ))}
              </div>
            )}
          </div>
        ))}
        <span className="ml-auto hidden text-xs font-medium text-readable-muted sm:inline">
          {tr(activeCat.labelKey)} {tr('categoryFlows')}
        </span>
      </div>
    </div>
  )
}