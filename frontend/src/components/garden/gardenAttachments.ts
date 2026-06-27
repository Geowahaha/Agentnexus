export type GardenAttachment =
  | { id: string; kind: 'image'; name: string; previewUrl: string }
  | { id: string; kind: 'link'; url: string }
  | { id: string; kind: 'pdf'; name: string }

export function newAttachmentId(): string {
  return `att-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export function serializeAttachmentsBlock(
  attachments: GardenAttachment[],
  locale: 'th' | 'en',
): string {
  if (attachments.length === 0) return ''
  const lines =
    locale === 'th'
      ? attachments.map((att) => {
          if (att.kind === 'link') return `- ลิงก์: ${att.url}`
          if (att.kind === 'image') return `- รูป: ${att.name}`
          return `- PDF: ${att.name}`
        })
      : attachments.map((att) => {
          if (att.kind === 'link') return `- Link: ${att.url}`
          if (att.kind === 'image') return `- Image: ${att.name}`
          return `- PDF: ${att.name}`
        })
  const header = locale === 'th' ? '[สิ่งที่แนบมา]' : '[Attachments]'
  return `${header}\n${lines.join('\n')}\n\n`
}

export function mergeStoryWithAttachments(
  story: string,
  attachments: GardenAttachment[],
  locale: 'th' | 'en',
): string {
  const block = serializeAttachmentsBlock(attachments, locale)
  const body = story.trim()
  if (!block) return body
  return body ? `${block}${body}` : block.trimEnd()
}