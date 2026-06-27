import type { ReactNode } from 'react'

const MARKDOWN_IMAGE = /!\[([^\]]*)\]\((https?:\/\/[^)\s]+)\)/g
const BARE_IMAGE_URL = /^(https?:\/\/\S+\.(?:png|jpe?g|webp|gif)(?:\?\S*)?)$/im
const MARKDOWN_LINK = /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g
const BARE_URL = /(https?:\/\/[^\s<>)]+)/g

type Segment =
  | { kind: 'text'; value: string }
  | { kind: 'image'; alt: string; url: string }

function parseStepOutput(output: string): Segment[] {
  const segments: Segment[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  MARKDOWN_IMAGE.lastIndex = 0
  while ((match = MARKDOWN_IMAGE.exec(output)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ kind: 'text', value: output.slice(lastIndex, match.index) })
    }
    segments.push({ kind: 'image', alt: match[1] || 'Generated image', url: match[2] })
    lastIndex = match.index + match[0].length
  }

  const tail = output.slice(lastIndex)
  const bare = BARE_IMAGE_URL.exec(tail)
  if (bare && bare.index !== undefined) {
    if (bare.index > 0) {
      segments.push({ kind: 'text', value: tail.slice(0, bare.index) })
    }
    segments.push({ kind: 'image', alt: 'Generated image', url: bare[1] })
    const after = tail.slice(bare.index + bare[0].length)
    if (after.trim()) {
      segments.push({ kind: 'text', value: after })
    }
  } else if (tail) {
    segments.push({ kind: 'text', value: tail })
  }

  if (segments.length === 0) {
    segments.push({ kind: 'text', value: output })
  }
  return segments
}

function linkifyText(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = []
  const combined = new RegExp(
    `${MARKDOWN_LINK.source}|${BARE_URL.source}`,
    'g',
  )
  let last = 0
  let match: RegExpExecArray | null
  let index = 0

  while ((match = combined.exec(text)) !== null) {
    if (match.index > last) {
      nodes.push(text.slice(last, match.index))
    }
    const label = match[1]
    const mdUrl = match[2]
    const bareUrl = match[3]
    if (label && mdUrl) {
      nodes.push(
        <a
          key={`${keyPrefix}-md-${index}`}
          href={mdUrl}
          target="_blank"
          rel="noreferrer"
          className="break-all text-cyan-600 underline decoration-cyan-600/40 hover:text-cyan-500"
        >
          {label}
        </a>,
      )
    } else if (bareUrl) {
      nodes.push(
        <a
          key={`${keyPrefix}-url-${index}`}
          href={bareUrl}
          target="_blank"
          rel="noreferrer"
          className="break-all text-cyan-600 underline decoration-cyan-600/40 hover:text-cyan-500"
        >
          {bareUrl}
        </a>,
      )
    }
    last = match.index + match[0].length
    index += 1
  }

  if (last < text.length) {
    nodes.push(text.slice(last))
  }
  if (nodes.length === 0) {
    nodes.push(text)
  }
  return nodes
}

function renderTextSegment(text: string, keyPrefix: string) {
  return (
    <pre key={keyPrefix} className="whitespace-pre-wrap text-sm">
      {linkifyText(text, keyPrefix)}
    </pre>
  )
}

export function ExpertStepOutput({ output }: { output: string }) {
  const segments = parseStepOutput(output)
  const hasImage = segments.some((segment) => segment.kind === 'image')
  const hasLink =
    /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/.test(output) ||
    /(https?:\/\/[^\s<>)]+)/.test(output)

  if (!hasImage && !hasLink) {
    return <pre className="workflow-step-output">{output}</pre>
  }

  return (
    <div className="workflow-step-output mt-3 space-y-3">
      {segments.map((segment, index) =>
        segment.kind === 'image' ? (
          <figure key={`img-${index}`} className="overflow-hidden rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
            <img
              src={segment.url}
              alt={segment.alt}
              className="max-h-[480px] w-full object-contain"
              loading="lazy"
            />
            <figcaption className="border-t border-[var(--color-border)] px-3 py-2 text-xs text-[var(--color-muted)]">
              <a href={segment.url} target="_blank" rel="noreferrer" className="break-all text-cyan-600 hover:underline">
                {segment.url}
              </a>
            </figcaption>
          </figure>
        ) : (
          renderTextSegment(segment.value, `text-${index}`)
        ),
      )}
    </div>
  )
}