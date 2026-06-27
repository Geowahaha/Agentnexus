import type { Locale } from '../i18n/strings'

export type ParsedScanStep = {
  limited: boolean
  statusCode: number | null
  warningLines: string[]
  rawJson: string | null
}

export function parseScanStepOutput(output: string): ParsedScanStep {
  const limited =
    output.includes('⚠️ Scan access limited') ||
    output.includes('Scan access limited') ||
    output.includes('สแกนไม่ครบ')
  let body = output
  const warningLines: string[] = []

  if (limited) {
    const chunks = output.split('\n\n')
    const header = chunks[0] ?? ''
    body = chunks.slice(1).join('\n\n').trim()
    for (const line of header.split('\n')) {
      const trimmed = line.replace(/^⚠️\s*/, '').trim()
      if (trimmed.startsWith('- ')) warningLines.push(trimmed.slice(2).trim())
      else if (trimmed && !trimmed.includes('Scan access limited')) warningLines.push(trimmed)
    }
  }

  let statusCode: number | null = null
  let rawJson: string | null = null
  const jsonCandidate = body.trim()
  if (jsonCandidate.startsWith('{')) {
    try {
      const parsed = JSON.parse(jsonCandidate) as { status?: number }
      if (typeof parsed.status === 'number') statusCode = parsed.status
      rawJson = jsonCandidate
    } catch {
      rawJson = null
    }
  }

  return { limited, statusCode, warningLines, rawJson }
}

export function localizeScanWarning(locale: Locale, warning: string): string {
  if (locale === 'en') return warning

  const httpMatch = warning.match(
    /Target site returned HTTP (\d+) for the scanner — (.+?) may block bots or require authentication\. Layer scores will be limited; fix site access or WAF rules for a full audit\./,
  )
  if (httpMatch) {
    return `เว็บเป้าหมายตอบ HTTP ${httpMatch[1]} ต่อสแกนเนอร์ — ${httpMatch[2]} อาจบล็อกบอทหรือต้องล็อกอิน คะแนนแต่ละชั้นจะจำกัด แก้การเข้าถึงหรือกฎ WAF เพื่อ audit เต็มรูปแบบ`
  }

  if (warning.startsWith('Scanner reported:')) {
    return warning.replace('Scanner reported:', 'สแกนเนอร์รายงาน:')
  }

  if (warning.startsWith('Site intelligence partial:')) {
    return warning.replace('Site intelligence partial:', 'ข้อมูลเว็บได้บางส่วน:')
  }

  return warning
}

export function shouldHideRawScanJson(parsed: ParsedScanStep): boolean {
  if (!parsed.rawJson) return false
  try {
    const data = JSON.parse(parsed.rawJson) as Record<string, unknown>
    const keys = Object.keys(data)
    return keys.length <= 2 && typeof data.status === 'number'
  } catch {
    return false
  }
}