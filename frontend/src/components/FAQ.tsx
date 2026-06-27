const FAQ_ITEMS = [
  {
    q: 'What am I actually buying?',
    a: 'One audit run for your website. You get a visibility score, a plain-English report of what to fix, and ready-to-paste files (like robots.txt and llms.txt). No monthly chat subscription.',
  },
  {
    q: 'How much does it cost?',
    a: 'About $2.60 per run ($2.50 skill fee + a small AI usage fee). New accounts get $5 free credits — enough for two audits.',
  },
  {
    q: 'What if my site blocks the scanner?',
    a: 'Some sites block bots. You still get fix guidance and template files, but scores may be limited until you open access in your firewall.',
  },
  {
    q: 'Can I see results before paying?',
    a: 'Yes. Open Showcase to read sample reports from real sites — including cases where access was limited.',
  },
  {
    q: 'Who is this for?',
    a: 'Website owners, marketers, and agencies who want a fast AI visibility check — not developers building custom bots.',
  },
]

export function FAQ() {
  return (
    <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-6 sm:p-8">
      <h2 className="text-lg font-semibold text-[var(--color-text)]">Common questions</h2>
      <div className="mt-5 space-y-3">
        {FAQ_ITEMS.map((item) => (
          <details
            key={item.q}
            className="group rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3"
          >
            <summary className="cursor-pointer text-sm font-semibold text-[var(--color-text)] group-open:text-[var(--color-market-hover)]">
              {item.q}
            </summary>
            <p className="mt-2 text-sm leading-relaxed text-[var(--color-muted)]">{item.a}</p>
          </details>
        ))}
      </div>
    </section>
  )
}