import { Link } from 'react-router-dom'

const SECTIONS = [
  {
    heading: 'Remote support & Local Bridge',
    body: 'When a creator offers remote assistance, agents may request access to files or commands on your machine through the Local Bridge. Every tool invocation requires your explicit approval in the browser. You can deny any request or disconnect devices at any time from Bridge settings.',
  },
  {
    heading: 'Creator responsibilities',
    body: 'Creators are responsible for the accuracy, legality, and maintenance of their agent flows, tools, and deliverables. AgentNexus provides hosting, billing, and execution infrastructure but does not guarantee outcomes. Creators must respond to buyer support threads in good faith and disclose limitations of their flows.',
  },
  {
    heading: 'Client responsibilities & risk acceptance',
    body: 'Before running a workflow you must confirm you have permission to scan or modify the targets you submit (URLs, files, accounts). You accept that AI outputs may be incomplete or incorrect, that third-party LLM providers process your inputs, and that remote support carries inherent operational risk.',
  },
  {
    heading: 'Data handling',
    body: 'Tasks, outputs, and billing records are stored to deliver the service. URLs and content you submit may be sent to LLM providers and integrated tools (e.g. scanners, MCP servers) configured by the creator\'s product. Do not submit secrets, credentials, or personal data you are not authorized to share.',
  },
  {
    heading: 'Disputes & failed runs',
    body: 'Failed runs before deliverables are produced may qualify for billing review. Completed runs are generally non-refundable because provider costs are incurred immediately. Use the review thread on your workflow to contact the creator; unresolved disputes may be escalated per our Refund Policy.',
  },
]

export function Security() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <Link to="/" className="text-sm text-[var(--color-muted)] hover:text-[var(--color-market)]">
        ← Marketplace
      </Link>
      <p className="mt-6 text-xs font-semibold uppercase tracking-widest text-[var(--color-market)]">
        Trust & safety
      </p>
      <h1 className="text-display mt-2 text-3xl font-bold text-[var(--color-text)]">Safety, security & risk</h1>
      <p className="mt-3 text-sm leading-relaxed text-[var(--color-muted)]">
        AgentNexus is an agent flow marketplace. Creators sell workflows; clients run them with clear consent,
        especially when remote support or local bridge tools are involved.
      </p>
      <div className="mt-8 space-y-6">
        {SECTIONS.map((section) => (
          <section key={section.heading} className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
            <h2 className="text-lg font-semibold text-[var(--color-text)]">{section.heading}</h2>
            <p className="mt-2 text-sm leading-relaxed text-[var(--color-muted)]">{section.body}</p>
          </section>
        ))}
      </div>
      <p className="mt-8 text-sm text-[var(--color-muted)]">
        Also see{' '}
        <Link to="/terms" className="text-[var(--color-market)] hover:underline">Terms of Service</Link>
        {' '}and{' '}
        <Link to="/privacy" className="text-[var(--color-market)] hover:underline">Privacy Policy</Link>.
      </p>
    </div>
  )
}