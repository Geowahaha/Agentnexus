const TESTIMONIALS = [
  {
    quote:
      'We dogfooded the visibility pipeline on aibotauth.com — same skill we sell. Buyers see the live site, not a slide deck.',
    name: 'AIBotAuth Team',
    role: 'Skill creator & reference implementation',
  },
  {
    quote:
      'Expert Skills beat hiring three separate agents. One URL in, one fix pack out — that is what site owners actually want.',
    name: 'AgentNexus',
    role: 'Marketplace positioning',
  },
]

export function Testimonials() {
  return (
    <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-6 sm:p-8">
      <h2 className="text-lg font-semibold text-[var(--color-text)]">Why buyers trust Showcase-first</h2>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        {TESTIMONIALS.map((item) => (
          <blockquote
            key={item.name}
            className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5"
          >
            <p className="text-sm leading-relaxed text-[var(--color-text-soft)]">&ldquo;{item.quote}&rdquo;</p>
            <footer className="mt-4 text-xs text-[var(--color-muted)]">
              <span className="font-medium text-[var(--color-muted)]">{item.name}</span>
              <span className="mx-1">·</span>
              {item.role}
            </footer>
          </blockquote>
        ))}
      </div>
    </section>
  )
}