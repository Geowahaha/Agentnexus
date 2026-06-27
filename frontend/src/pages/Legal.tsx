import { Link } from 'react-router-dom'

type LegalKind = 'terms' | 'privacy' | 'refunds'

const CONTENT: Record<LegalKind, { title: string; sections: { heading: string; body: string }[] }> = {
  terms: {
    title: 'Terms of Service',
    sections: [
      {
        heading: 'Service',
        body: 'AgentNexus provides a marketplace to run AI agent workflows and Expert Skills. Results depend on third-party LLM providers and target site accessibility.',
      },
      {
        heading: 'Trial credits ($5 welcome)',
        body:
          'New accounts receive $5 trial credits (เครดิตทดลองใช้แรกเข้า). Trial credits can be used to run any marketplace agent or Expert Skill. ' +
          'Trial usage is labeled on your bill as ทดลองใช้. Trial and demo credits are not real money and are non-refundable.',
      },
      {
        heading: 'Payments',
        body:
          'You purchase wallet credits (Stripe) or receive trial/demo credits. Paid credits are charged per completed workflow. ' +
          'Skill fees and LLM usage are deducted at completion. Only spend from paid credits (Stripe top-up or transferred creator earnings from paid runs) counts toward creator payouts.',
      },
      {
        heading: 'Creator payouts & trial runs',
        body:
          'When a buyer pays with trial or demo credits (signup bonus, demo top-up, or mixed spend where the trial pool is used first), ' +
          'the agent/skill owner receives no real payout for that portion. Creator earnings accrue only from marketplace fees paid with real wallet credits. ' +
          'This is shown on the buyer bill and in workflow billing details.',
      },
      {
        heading: 'Platform admin testing',
        body:
          'Designated OBOLLA platform operator accounts (role: admin) may run agents and Expert Skills for quality assurance. ' +
          'These runs are labeled Platform tested on billing records. Platform-tested runs do not generate creator payouts, ' +
          'even if paid wallet credits are used. This keeps marketplace metrics honest and is disclosed in our Privacy Policy.',
      },
      {
        heading: 'Acceptable use',
        body: 'Do not use the service for illegal activity, credential stuffing, or scanning sites you do not own or have permission to test.',
      },
      {
        heading: 'Creator responsibilities',
        body: 'Creators maintain their agent flows, pricing, deliverables, and buyer support. They are responsible for the legality and accuracy of their products. AgentNexus hosts execution and payments but does not warrant outcomes.',
      },
      {
        heading: 'Remote support & Local Bridge',
        body: 'When creators offer remote assistance, clients must approve each local tool action. Creators must not request access beyond what the service requires. Clients accept operational risk when enabling bridge devices.',
      },
      {
        heading: 'Client risk acceptance',
        body: 'By running a workflow you accept that AI outputs may be incomplete, that third-party LLM providers process your inputs, and that completed runs are generally non-refundable once provider costs are incurred.',
      },
    ],
  },
  privacy: {
    title: 'Privacy Policy',
    sections: [
      {
        heading: 'Data we store',
        body: 'Account email, workflow tasks and outputs, billing transactions, and usage metadata needed to operate the marketplace.',
      },
      {
        heading: 'Third parties',
        body: 'Workflows may call LLM providers (Google, Anthropic, xAI, OpenAI) and MCP tools such as AIBotAuth. URLs you submit are sent to these services to fulfill your run.',
      },
      {
        heading: 'Retention',
        body: 'Workflow results are kept so you can review deliverables and optionally showcase work in your portfolio.',
      },
      {
        heading: 'Platform operator testing',
        body:
          'OBOLLA platform administrators may execute workflows to verify agents, skills, billing, and integrations. ' +
          'These runs are tagged Platform tested in billing transactions and workflow receipts. ' +
          'They are stored like other workflows (task, outputs, charges) for audit and support. ' +
          'Agent/skill owners are not paid for platform-tested runs; this is visible in transaction metadata.',
      },
      {
        heading: 'Admin accounts',
        body:
          'Platform operator emails are configured server-side (e.g. co-founder accounts). ' +
          'Admin role grants elevated limits for billing top-ups and internal QA; it does not expose other users\' private data without normal authorization paths.',
      },
    ],
  },
  refunds: {
    title: 'Refund Policy',
    sections: [
      {
        heading: 'Completed runs',
        body: 'Completed Expert Skill runs are generally non-refundable because LLM and scanner costs are incurred immediately.',
      },
      {
        heading: 'Failed runs',
        body: 'If a workflow fails before producing a deliverable, contact support with the workflow ID. We review failed charges case by case.',
      },
      {
        heading: 'Wallet credits',
        body:
          'Unused paid wallet balance (Stripe) may be refundable within 14 days of purchase where required by law. ' +
          'Trial welcome credits ($5) and demo top-ups are not real money and are not refundable.',
      },
    ],
  },
}

export function Legal({ kind }: { kind: LegalKind }) {
  const page = CONTENT[kind]

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <Link to="/" className="text-sm text-[var(--color-muted)] hover:text-[var(--color-market)]">
        ← Marketplace
      </Link>
      <h1 className="mt-6 text-3xl font-bold text-[var(--color-text)]">{page.title}</h1>
      <p className="mt-2 text-sm text-[var(--color-muted)]">Last updated June 2026</p>
      <div className="mt-8 space-y-6">
        {page.sections.map((section) => (
          <section key={section.heading}>
            <h2 className="text-lg font-semibold text-[var(--color-text)]">{section.heading}</h2>
            <p className="mt-2 text-sm leading-relaxed text-[var(--color-muted)]">{section.body}</p>
          </section>
        ))}
      </div>
    </div>
  )
}