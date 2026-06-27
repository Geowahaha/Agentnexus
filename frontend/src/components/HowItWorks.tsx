const STEPS = [
  {
    title: 'Pick a proven skill',
    body: 'Browse case studies and see sample reports before you pay.',
    color: 'text-amber-800',
  },
  {
    title: 'Enter your URL',
    body: 'One website address. About $5. Results in minutes.',
    color: 'text-violet-800',
  },
  {
    title: 'Deploy the fixes',
    body: 'Download scorecard, report, and paste-ready files.',
    color: 'text-[var(--color-market-hover)]',
  },
]

export function HowItWorks() {
  return (
    <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-6 sm:p-8">
      <h2 className="text-lg font-semibold text-[var(--color-text)]">How it works</h2>
      <ol className="mt-6 grid gap-4 sm:grid-cols-3">
        {STEPS.map((step, index) => (
          <li
            key={step.title}
            className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
          >
            <span className={`font-mono text-sm font-bold ${step.color}`}>{index + 1}</span>
            <h3 className="mt-2 font-medium text-[var(--color-text)]">{step.title}</h3>
            <p className="mt-1 text-sm text-[var(--color-muted)]">{step.body}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}