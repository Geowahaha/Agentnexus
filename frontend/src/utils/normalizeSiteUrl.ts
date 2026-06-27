/** Domain with at least one dot and valid hostname characters. */
const DOMAIN_RE =
  /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(?:\/[^\s]*)?$/i

const FULL_URL_RE = /^https?:\/\/.+/i

export interface NormalizeSiteUrlResult {
  url: string | null
  normalized: string
  error: string | null
}

function isValidDomain(candidate: string): boolean {
  const host = candidate.split('/')[0]
  if (!host.includes('.')) return false
  return DOMAIN_RE.test(candidate)
}

/**
 * Normalize user input to a fetchable site URL.
 * - aibotauth.com → https://aibotauth.com
 * - www.aibotauth.com → https://www.aibotauth.com
 * - https://aibotauth.com → unchanged
 * - http://aibotauth.com → unchanged
 */
export function normalizeSiteUrl(input: string): NormalizeSiteUrlResult {
  const trimmed = input.trim()
  if (!trimmed) {
    return {
      url: null,
      normalized: '',
      error: 'Please enter a valid URL, e.g. example.com or https://example.com',
    }
  }

  const urlMatch = trimmed.match(/https?:\/\/[^\s<>"']+/i)
  if (urlMatch) {
    const url = urlMatch[0].replace(/[.,);]+$/, '')
    try {
      const parsed = new URL(url)
      if (!parsed.hostname.includes('.')) {
        return {
          url: null,
          normalized: trimmed,
          error: 'Please enter a valid URL, e.g. example.com or https://example.com',
        }
      }
      const rest = trimmed.slice(urlMatch.index! + urlMatch[0].length).trim()
      const normalized = rest ? `${url} ${rest}` : url
      return { url, normalized, error: null }
    } catch {
      return {
        url: null,
        normalized: trimmed,
        error: 'Please enter a valid URL, e.g. example.com or https://example.com',
      }
    }
  }

  const [first, ...restParts] = trimmed.split(/\s+/)
  const candidate = first.replace(/[.,);]+$/, '')
  const rest = restParts.join(' ')

  if (!isValidDomain(candidate)) {
    return {
      url: null,
      normalized: trimmed,
      error: 'Please enter a valid URL, e.g. example.com or https://example.com',
    }
  }

  const url = `https://${candidate}`
  try {
    new URL(url)
  } catch {
    return {
      url: null,
      normalized: trimmed,
      error: 'Please enter a valid URL, e.g. example.com or https://example.com',
    }
  }

  const normalized = rest ? `${url} ${rest}` : url
  return { url, normalized, error: null }
}

export function looksLikeSiteInput(input: string): boolean {
  const t = input.trim()
  if (!t) return false
  if (FULL_URL_RE.test(t)) return true
  return isValidDomain(t.split(/\s+/)[0].replace(/[.,);]+$/, ''))
}