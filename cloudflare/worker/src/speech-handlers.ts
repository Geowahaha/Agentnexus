const WHISPER_MAX_BYTES = 10 * 1024 * 1024
const WORKERS_AI_WHISPER = '@cf/openai/whisper-large-v3-turbo'
const WORKERS_AI_POLISH = '@cf/meta/llama-3.1-8b-instruct'
const THAI_SCRIPT = /[\u0E00-\u0E7F]/
const LATIN_SCRIPT = /[A-Za-z]/

const THAI_WHISPER_PROMPT =
  'สวัสดีครับ ผมอยากสร้างเอเจนต์ช่วยงานลูกค้า ขายสินค้าออนไลน์ ภาษาไทย ขอบคุณครับ'

type SpeechEnv = {
  AI?: Ai
  OPENAI_API_KEY?: string
}

type WhisperResult = {
  text?: string
  transcription_info?: { language?: string }
}
type LlamaResult = { response?: string }

function normalizeWhisperLanguage(lang: string | null): string | undefined {
  if (!lang) return undefined
  const normalized = lang.trim().toLowerCase()
  if (normalized.startsWith('th')) return 'th'
  if (normalized.startsWith('en')) return 'en'
  if (normalized.length === 2) return normalized
  return undefined
}

function isAutoLanguage(lang: string): boolean {
  const normalized = lang.trim().toLowerCase()
  return !normalized || normalized === 'auto' || normalized === 'detect'
}

function shouldPolishThai(lang: string, detectedLang: string | undefined, text: string): boolean {
  if (THAI_SCRIPT.test(text) || !LATIN_SCRIPT.test(text)) return false
  if (detectedLang?.startsWith('th')) return true
  if (!isAutoLanguage(lang) && normalizeWhisperLanguage(lang) === 'th') return true
  return false
}

function normalizeAudioContentType(filename: string, contentType: string): string {
  const lowered = filename.toLowerCase()
  if (lowered.endsWith('.m4a') || lowered.endsWith('.mp4') || lowered.endsWith('.caf')) {
    return 'audio/mp4'
  }
  if (lowered.endsWith('.webm')) return 'audio/webm'
  if (lowered.endsWith('.ogg')) return 'audio/ogg'
  if (lowered.endsWith('.wav')) return 'audio/wav'
  if (lowered.endsWith('.mp3') || lowered.endsWith('.mpeg') || lowered.endsWith('.mpga')) {
    return 'audio/mpeg'
  }
  if (contentType && contentType !== 'application/octet-stream') {
    return contentType.split(';', 1)[0].trim()
  }
  return 'application/octet-stream'
}

function bytesToBase64(bytes: ArrayBuffer): string {
  const u8 = new Uint8Array(bytes)
  let binary = ''
  for (let i = 0; i < u8.length; i += 1) {
    binary += String.fromCharCode(u8[i])
  }
  return btoa(binary)
}

async function transcribeWithWorkersAi(
  ai: Ai,
  bytes: ArrayBuffer,
  lang: string,
): Promise<{ text: string | null; detectedLang?: string }> {
  const whisperLang = isAutoLanguage(lang) ? undefined : normalizeWhisperLanguage(lang)
  const input: Record<string, string | boolean> = {
    audio: bytesToBase64(bytes),
    task: 'transcribe',
    vad_filter: true,
  }
  if (whisperLang) {
    input.language = whisperLang
    if (whisperLang === 'th') input.initial_prompt = THAI_WHISPER_PROMPT
  }

  const result = (await ai.run(WORKERS_AI_WHISPER, input)) as WhisperResult
  const text = String(result.text ?? '').trim()
  return {
    text: text || null,
    detectedLang: result.transcription_info?.language,
  }
}

async function polishThaiRomanization(ai: Ai, text: string): Promise<string> {
  if (THAI_SCRIPT.test(text) || !LATIN_SCRIPT.test(text)) return text

  try {
    const result = (await ai.run(WORKERS_AI_POLISH, {
      messages: [
        {
          role: 'system',
          content:
            'แปลงข้อความภาษาไทยที่เขียนด้วยตัวอักษรอังกฤษ (คาราโอเกะ/romanized Thai) ให้เป็นภาษาไทยที่ถูกต้อง ตอบเฉพาะข้อความภาษาไทยเท่านั้น ไม่ต้องอธิบาย',
        },
        { role: 'user', content: text },
      ],
      max_tokens: 320,
    })) as LlamaResult

    const polished = String(result.response ?? '').trim()
    if (polished && THAI_SCRIPT.test(polished)) return polished
  } catch {
    // keep raw transcript
  }

  return text
}

async function transcribeWithOpenAi(
  apiKey: string,
  bytes: ArrayBuffer,
  filename: string,
  contentType: string,
  lang: string,
): Promise<string | null> {
  const whisperForm = new FormData()
  const resolvedType = normalizeAudioContentType(filename, contentType)
  whisperForm.append('file', new Blob([bytes], { type: resolvedType }), filename)
  whisperForm.append('model', 'whisper-1')
  const whisperLang = normalizeWhisperLanguage(lang)
  if (whisperLang) whisperForm.append('language', whisperLang)

  const upstream = await fetch('https://api.openai.com/v1/audio/transcriptions', {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey}` },
    body: whisperForm,
  })

  if (!upstream.ok) return null

  const payload = (await upstream.json()) as WhisperResult
  const text = String(payload.text ?? '').trim()
  return text || null
}

export async function handleSpeechTranscribe(
  request: Request,
  env: SpeechEnv,
): Promise<Response> {
  let form: FormData
  try {
    form = await request.formData()
  } catch {
    return Response.json({ detail: 'Invalid multipart form data.' }, { status: 400 })
  }

  const audio = form.get('audio')
  const lang = form.get('lang')?.toString() ?? 'auto'
  if (!audio || typeof audio === 'string') {
    return Response.json({ detail: 'Audio file is required.' }, { status: 400 })
  }

  const filename = audio.name || 'speech.webm'
  const bytes = await audio.arrayBuffer()
  if (!bytes.byteLength) {
    return Response.json({ detail: 'Audio file is empty.' }, { status: 400 })
  }
  if (bytes.byteLength > WHISPER_MAX_BYTES) {
    return Response.json({ detail: 'Audio file is too large. Maximum size is 10 MB.' }, { status: 400 })
  }

  if (!env.AI) {
    return Response.json(
      { detail: 'Speech transcription is not configured. Enable Workers AI on the edge worker.' },
      { status: 503 },
    )
  }

  try {
    const workersResult = await transcribeWithWorkersAi(env.AI, bytes, lang)
    let text = workersResult.text
    let detectedLang = workersResult.detectedLang

    if (!text && env.OPENAI_API_KEY?.trim() && !isAutoLanguage(lang)) {
      text = await transcribeWithOpenAi(
        env.OPENAI_API_KEY.trim(),
        bytes,
        filename,
        audio.type,
        lang,
      )
    }

    if (!text) {
      return Response.json({ detail: 'No speech detected in the recording.' }, { status: 400 })
    }

    if (shouldPolishThai(lang, detectedLang, text)) {
      text = await polishThaiRomanization(env.AI, text)
    }

    return Response.json({ text })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Speech transcription failed'
    return Response.json({ detail: `Speech transcription failed: ${message}` }, { status: 502 })
  }
}