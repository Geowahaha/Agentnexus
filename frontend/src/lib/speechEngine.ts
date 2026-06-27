export type SpeechEngine = 'webspeech' | 'whisper'

const RECORDER_MIME_CANDIDATES = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/mp4',
  'audio/aac',
  'audio/ogg;codecs=opus',
  'audio/ogg',
]

export function getSpeechRecognitionCtor(): SpeechRecognitionConstructor | null {
  if (typeof window === 'undefined') return null
  return window.SpeechRecognition ?? window.webkitSpeechRecognition ?? null
}

export function isIOSDevice(): boolean {
  if (typeof navigator === 'undefined') return false
  const ua = navigator.userAgent
  if (/iPhone|iPad|iPod/i.test(ua)) return true
  return navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1
}

export function isMobileDevice(): boolean {
  if (typeof navigator === 'undefined') return false
  return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent)
}

export function isTouchSpeechDevice(): boolean {
  return isIOSDevice() || isMobileDevice()
}

export function canUseMediaRecorder(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof MediaRecorder !== 'undefined' &&
    !!navigator.mediaDevices?.getUserMedia
  )
}

export function canUseWebSpeech(): boolean {
  return !isTouchSpeechDevice() && getSpeechRecognitionCtor() != null
}

export function isSpeechToTextSupported(): boolean {
  return canUseWebSpeech() || canUseMediaRecorder()
}

export function pickSpeechEngine(): SpeechEngine {
  if (isTouchSpeechDevice()) return 'whisper'
  if (!canUseWebSpeech()) return 'whisper'
  return 'webspeech'
}

export function pickRecorderMimeType(): string | undefined {
  if (typeof MediaRecorder === 'undefined') return undefined
  const ordered = isIOSDevice()
    ? ['audio/mp4', 'audio/aac', ...RECORDER_MIME_CANDIDATES]
    : RECORDER_MIME_CANDIDATES
  for (const candidate of ordered) {
    if (MediaRecorder.isTypeSupported(candidate)) return candidate
  }
  return undefined
}

/** Call synchronously inside a user gesture (click/tap) — required for iOS. */
export function requestMicrophoneStream(): Promise<MediaStream> {
  if (!navigator.mediaDevices?.getUserMedia) {
    return Promise.reject(new DOMException('Microphone is not available', 'NotSupportedError'))
  }
  return navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
      channelCount: 1,
    },
    video: false,
  })
}

export function recorderTimesliceMs(): number | undefined {
  return isIOSDevice() ? 250 : undefined
}

export function recorderFileExtension(mimeType: string | undefined): string {
  if (!mimeType) return 'webm'
  if (mimeType.includes('mp4') || mimeType.includes('m4a')) return 'm4a'
  if (mimeType.includes('aac')) return 'aac'
  if (mimeType.includes('ogg')) return 'ogg'
  if (mimeType.includes('caf')) return 'caf'
  return 'webm'
}