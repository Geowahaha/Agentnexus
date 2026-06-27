import { useCallback, useEffect, useRef, useState } from 'react'
import { api, ApiError } from '../api/client'
import type { Locale } from '../i18n/strings'
import {
  canUseMediaRecorder,
  canUseWebSpeech,
  getSpeechRecognitionCtor,
  isMobileDevice,
  isSpeechToTextSupported,
  pickRecorderMimeType,
  pickSpeechEngine,
  recorderFileExtension,
  recorderTimesliceMs,
  requestMicrophoneStream,
  type SpeechEngine,
} from '../lib/speechEngine'
import { attachSilenceDetector } from '../lib/silenceDetection'

export type SpeechToTextError =
  | 'unsupported'
  | 'ios'
  | 'not-allowed'
  | 'no-speech'
  | 'network'
  | 'audio-capture'
  | 'aborted'
  | 'server'
  | 'generic'

export { isIOSDevice, isMobileDevice } from '../lib/speechEngine'

const THAI_SCRIPT = /[\u0E00-\u0E7F]/
const TRANSCRIBE_TIMEOUT_MS = 45_000
const ONSTOP_FALLBACK_MS = 1_500

function usesThaiScript(text: string): boolean {
  return THAI_SCRIPT.test(text)
}

export function appendTranscript(current: string, chunk: string, lang?: string): string {
  const trimmed = chunk.trim()
  if (!trimmed) return current
  if (!current.trim()) return trimmed
  const thaiJoin = lang?.startsWith('th') || usesThaiScript(current) || usesThaiScript(trimmed)
  if (thaiJoin) return `${current}${trimmed}`
  const needsSpace = !current.endsWith(' ') && !current.endsWith('\n')
  return `${current}${needsSpace ? ' ' : ''}${trimmed}`
}

export function speechLang(locale: Locale): string {
  return locale === 'th' ? 'th-TH' : 'en-US'
}

export function speechLangCandidates(localeOrLang: Locale | string): string[] {
  const normalized = localeOrLang.toLowerCase()
  if (normalized === 'auto' || normalized === 'detect') {
    return ['th-TH', 'en-US', 'th', 'en-GB', 'en']
  }
  if (normalized === 'th' || normalized.startsWith('th-')) return ['th-TH', 'th', 'en-US', 'en']
  if (normalized === 'en' || normalized.startsWith('en')) return ['en-US', 'en-GB', 'en', 'th-TH', 'th']
  return [localeOrLang]
}

export function collectSpeechResults(event: SpeechRecognitionEvent, mobile: boolean): {
  interimText: string
  finalText: string
  anyText: string
} {
  let interimText = ''
  let finalText = ''
  const startIndex = mobile ? 0 : event.resultIndex
  for (let i = startIndex; i < event.results.length; i += 1) {
    const piece = event.results[i][0]?.transcript ?? ''
    if (!piece) continue
    if (event.results[i].isFinal) finalText += piece
    else interimText += piece
  }
  const anyText = mobile ? `${finalText}${interimText}` : finalText || interimText
  return { interimText, finalText, anyText }
}

function detachRecognition(recognition: SpeechRecognition | null) {
  if (!recognition) return
  recognition.onstart = null
  recognition.onresult = null
  recognition.onerror = null
  recognition.onend = null
  recognition.onspeechend = null
  recognition.onaudioend = null
  try {
    recognition.abort()
  } catch {
    try {
      recognition.stop()
    } catch {
      // ignore
    }
  }
}

function stopMediaStream(stream: MediaStream | null) {
  stream?.getTracks().forEach((track) => track.stop())
}

function mapMicError(err: unknown): SpeechToTextError {
  if (err instanceof DOMException) {
    if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') return 'not-allowed'
    if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') return 'audio-capture'
    if (err.name === 'NotReadableError' || err.name === 'TrackStartError') return 'audio-capture'
    if (err.name === 'SecurityError') return 'not-allowed'
    if (err.name === 'AbortError') return 'network'
  }
  return 'not-allowed'
}

function mapSpeechError(code: string): SpeechToTextError {
  if (code === 'not-allowed' || code === 'service-not-allowed') return 'not-allowed'
  if (code === 'no-speech') return 'no-speech'
  if (code === 'network') return 'network'
  if (code === 'audio-capture') return 'audio-capture'
  if (code === 'aborted') return 'aborted'
  return 'generic'
}

export function useSpeechToText({
  locale,
  speechLang: speechLangOverride,
  onFinalTranscript,
  onInterimTranscript,
}: {
  locale: Locale
  speechLang?: string
  onFinalTranscript: (text: string) => void
  onInterimTranscript?: (text: string) => void
}) {
  const [supported, setSupported] = useState(false)
  const [listening, setListening] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const [interim, setInterim] = useState('')
  const [error, setError] = useState<SpeechToTextError | null>(null)
  const [requestingMic, setRequestingMic] = useState(false)
  const [recordingSeconds, setRecordingSeconds] = useState(0)
  const engineRef = useRef<SpeechEngine>(pickSpeechEngine())
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const mimeRef = useRef<string | undefined>(undefined)
  const listeningIntentRef = useRef(false)
  const restartTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const listenTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const transcribeWatchdogRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const onstopFallbackRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const uploadAbortRef = useRef<AbortController | null>(null)
  const uploadTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const stopHandledRef = useRef(false)
  const userCancelledRef = useRef(false)
  const uploadSessionRef = useRef(0)
  const silenceCleanupRef = useRef<(() => void) | null>(null)
  const recordingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const recordingStartedAtRef = useRef(0)
  const langCandidatesRef = useRef<string[]>(speechLangCandidates(speechLangOverride ?? locale))
  const langIndexRef = useRef(0)
  const pendingTranscriptRef = useRef('')
  const sessionIdRef = useRef(0)
  const hadResultRef = useRef(false)
  const onFinalRef = useRef(onFinalTranscript)
  const onInterimRef = useRef(onInterimTranscript)
  const speechLangRef = useRef(speechLangOverride ?? speechLang(locale))
  const mobileRef = useRef(isMobileDevice())

  useEffect(() => {
    onFinalRef.current = onFinalTranscript
  }, [onFinalTranscript])

  useEffect(() => {
    onInterimRef.current = onInterimTranscript
  }, [onInterimTranscript])

  useEffect(() => {
    speechLangRef.current = speechLangOverride ?? speechLang(locale)
    langCandidatesRef.current = speechLangCandidates(speechLangRef.current)
    langIndexRef.current = 0
  }, [locale, speechLangOverride])

  useEffect(() => {
    setSupported(isSpeechToTextSupported())
  }, [])

  const commitPendingTranscript = useCallback(() => {
    const pending = pendingTranscriptRef.current.trim()
    if (!pending) return
    pendingTranscriptRef.current = ''
    hadResultRef.current = true
    onFinalRef.current(pending)
    setInterim('')
    onInterimRef.current?.('')
  }, [])

  const clearRestartTimer = useCallback(() => {
    if (restartTimerRef.current) {
      clearTimeout(restartTimerRef.current)
      restartTimerRef.current = null
    }
  }, [])

  const clearListenTimeout = useCallback(() => {
    if (listenTimeoutRef.current) {
      clearTimeout(listenTimeoutRef.current)
      listenTimeoutRef.current = null
    }
  }, [])

  const clearTranscribeWatchdog = useCallback(() => {
    if (transcribeWatchdogRef.current) {
      clearTimeout(transcribeWatchdogRef.current)
      transcribeWatchdogRef.current = null
    }
  }, [])

  const clearOnstopFallback = useCallback(() => {
    if (onstopFallbackRef.current) {
      clearTimeout(onstopFallbackRef.current)
      onstopFallbackRef.current = null
    }
  }, [])

  const clearUploadTimeout = useCallback(() => {
    if (uploadTimeoutRef.current) {
      clearTimeout(uploadTimeoutRef.current)
      uploadTimeoutRef.current = null
    }
  }, [])

  const clearSilenceDetector = useCallback(() => {
    silenceCleanupRef.current?.()
    silenceCleanupRef.current = null
  }, [])

  const clearRecordingTimer = useCallback(() => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current)
      recordingTimerRef.current = null
    }
    setRecordingSeconds(0)
  }, [])

  const startRecordingTimer = useCallback(() => {
    clearRecordingTimer()
    recordingStartedAtRef.current = Date.now()
    recordingTimerRef.current = setInterval(() => {
      setRecordingSeconds(Math.floor((Date.now() - recordingStartedAtRef.current) / 1000))
    }, 200)
  }, [clearRecordingTimer])

  const invalidateSession = useCallback(() => {
    sessionIdRef.current += 1
    clearRestartTimer()
    clearListenTimeout()
    clearTranscribeWatchdog()
    clearOnstopFallback()
    clearUploadTimeout()
    clearSilenceDetector()
    clearRecordingTimer()
  }, [
    clearListenTimeout,
    clearOnstopFallback,
    clearRecordingTimer,
    clearRestartTimer,
    clearSilenceDetector,
    clearTranscribeWatchdog,
    clearUploadTimeout,
  ])

  const teardownWhisper = useCallback(() => {
    clearSilenceDetector()
    clearRecordingTimer()
    const recorder = recorderRef.current
    recorderRef.current = null
    if (recorder && recorder.state !== 'inactive') {
      recorder.ondataavailable = null
      recorder.onstop = null
      recorder.onerror = null
      try {
        recorder.stop()
      } catch {
        // ignore
      }
    }
    stopMediaStream(streamRef.current)
    streamRef.current = null
    chunksRef.current = []
  }, [clearRecordingTimer, clearSilenceDetector])

  const finishListening = useCallback(
    (commit: boolean) => {
      invalidateSession()
      listeningIntentRef.current = false
      userCancelledRef.current = false
      uploadAbortRef.current?.abort()
      uploadAbortRef.current = null
      stopHandledRef.current = true
      detachRecognition(recognitionRef.current)
      recognitionRef.current = null
      teardownWhisper()
      if (commit) commitPendingTranscript()
      setListening(false)
      setRequestingMic(false)
      setTranscribing(false)
      setInterim('')
    },
    [commitPendingTranscript, invalidateSession, teardownWhisper],
  )

  const startTranscribeWatchdog = useCallback((session: number) => {
    clearTranscribeWatchdog()
    transcribeWatchdogRef.current = setTimeout(() => {
      if (session !== uploadSessionRef.current || userCancelledRef.current) return
      uploadAbortRef.current?.abort()
      uploadAbortRef.current = null
      clearUploadTimeout()
      clearOnstopFallback()
      stopHandledRef.current = true
      teardownWhisper()
      setTranscribing(false)
      setListening(false)
      setRequestingMic(false)
      setError('network')
    }, TRANSCRIBE_TIMEOUT_MS)
  }, [clearOnstopFallback, clearTranscribeWatchdog, clearUploadTimeout, teardownWhisper])

  const cancelActiveWork = useCallback(() => {
    uploadSessionRef.current += 1
    userCancelledRef.current = true
    listeningIntentRef.current = false
    uploadAbortRef.current?.abort()
    uploadAbortRef.current = null
    clearUploadTimeout()
    clearTranscribeWatchdog()
    clearOnstopFallback()
    stopHandledRef.current = true
    teardownWhisper()
    setListening(false)
    setRequestingMic(false)
    setTranscribing(false)
    setInterim('')
    setError(null)
  }, [clearOnstopFallback, clearTranscribeWatchdog, clearUploadTimeout, teardownWhisper])

  const uploadRecording = useCallback(
    async (blob: Blob, filename?: string) => {
      if (blob.size < 200) {
        setTranscribing(false)
        setListening(false)
        setRequestingMic(false)
        setError('no-speech')
        return
      }

      const session = ++uploadSessionRef.current
      const controller = new AbortController()
      uploadAbortRef.current = controller
      clearUploadTimeout()
      uploadTimeoutRef.current = setTimeout(() => {
        if (session === uploadSessionRef.current) controller.abort()
      }, TRANSCRIBE_TIMEOUT_MS)

      setTranscribing(true)
      setRequestingMic(false)
      setListening(false)
      startTranscribeWatchdog(session)

      try {
        const resolvedFilename =
          filename ?? `speech.${recorderFileExtension(mimeRef.current || blob.type)}`
        const result = await api.transcribeSpeech(
          blob,
          speechLangRef.current,
          resolvedFilename,
          controller.signal,
        )
        if (session !== uploadSessionRef.current) return
        const text = result.text?.trim()
        if (!text) {
          setError('no-speech')
          return
        }
        onFinalRef.current(text)
        setError(null)
      } catch (err) {
        if (session !== uploadSessionRef.current || userCancelledRef.current) return
        if (err instanceof DOMException && err.name === 'AbortError') {
          setError('network')
          return
        }
        if (err instanceof ApiError) {
          if (err.status === 503 || err.status === 502) {
            setError('server')
          } else if (err.status === 400) {
            setError('no-speech')
          } else {
            setError('network')
          }
        } else {
          setError('network')
        }
      } finally {
        if (session !== uploadSessionRef.current) return
        userCancelledRef.current = false
        uploadAbortRef.current = null
        clearUploadTimeout()
        clearTranscribeWatchdog()
        setTranscribing(false)
        setListening(false)
        setRequestingMic(false)
      }
    },
    [clearTranscribeWatchdog, clearUploadTimeout, startTranscribeWatchdog],
  )

  const finalizeRecordingRef = useRef<(recorder: MediaRecorder) => void>(() => undefined)

  const finalizeRecording = useCallback(
    (recorder: MediaRecorder) => {
      if (stopHandledRef.current) return
      stopHandledRef.current = true
      clearTranscribeWatchdog()
      clearOnstopFallback()
      stopMediaStream(streamRef.current)
      streamRef.current = null
      recorderRef.current = null
      const blobType = mimeRef.current || recorder.mimeType || 'audio/webm'
      const blob = new Blob(chunksRef.current, { type: blobType })
      chunksRef.current = []
      void uploadRecording(blob)
    },
    [clearOnstopFallback, clearTranscribeWatchdog, uploadRecording],
  )

  finalizeRecordingRef.current = finalizeRecording

  const beginWhisperRecording = useCallback(
    (stream: MediaStream) => {
      if (!canUseMediaRecorder()) {
        stopMediaStream(stream)
        setError('unsupported')
        return false
      }

      const mimeType = pickRecorderMimeType()
      mimeRef.current = mimeType || undefined
      streamRef.current = stream
      chunksRef.current = []
      stopHandledRef.current = false
      userCancelledRef.current = false

      let recorder: MediaRecorder
      try {
        recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream)
      } catch {
        stopMediaStream(stream)
        streamRef.current = null
        setRequestingMic(false)
        setError('audio-capture')
        return false
      }

      mimeRef.current = recorder.mimeType || mimeType

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data)
      }

      recorder.onerror = () => {
        finishListening(false)
        setError('audio-capture')
      }

      recorder.onstop = () => {
        finalizeRecordingRef.current(recorder)
      }

      recorderRef.current = recorder
      const timeslice = recorderTimesliceMs()
      try {
        if (timeslice) recorder.start(timeslice)
        else recorder.start()
      } catch {
        finishListening(false)
        setError('audio-capture')
        return false
      }

      silenceCleanupRef.current = attachSilenceDetector(stream, () => {
        if (listeningIntentRef.current && recorderRef.current?.state === 'recording') {
          stopWhisperRef.current()
        }
      })

      startRecordingTimer()
      setRequestingMic(false)
      setListening(true)
      setError(null)
      return true
    },
    [finishListening, startRecordingTimer],
  )

  const stopWhisperRef = useRef<() => void>(() => undefined)

  const acquireAndBeginWhisperFromGesture = useCallback(() => {
    const micPromise = requestMicrophoneStream()
    micPromise
      .then((stream) => {
        if (!listeningIntentRef.current) {
          stopMediaStream(stream)
          return
        }
        beginWhisperRecording(stream)
      })
      .catch((err) => {
        listeningIntentRef.current = false
        setRequestingMic(false)
        setError(mapMicError(err))
      })
  }, [beginWhisperRecording])

  const stopWhisper = useCallback(() => {
    listeningIntentRef.current = false
    const recorder = recorderRef.current
    if (!recorder || recorder.state === 'inactive') {
      teardownWhisper()
      setListening(false)
      setRequestingMic(false)
      setTranscribing(false)
      return
    }

    setTranscribing(true)
    setRequestingMic(false)
    setListening(false)
    stopHandledRef.current = false
    const session = ++uploadSessionRef.current
    startTranscribeWatchdog(session)

    clearOnstopFallback()
    onstopFallbackRef.current = setTimeout(() => {
      if (!stopHandledRef.current && recorderRef.current === recorder) {
        finalizeRecordingRef.current(recorder)
      }
    }, ONSTOP_FALLBACK_MS)

    try {
      if (recorder.state === 'recording' && typeof recorder.requestData === 'function') {
        recorder.requestData()
      }
      recorder.stop()
    } catch {
      clearOnstopFallback()
      clearTranscribeWatchdog()
      if (!stopHandledRef.current) {
        finalizeRecordingRef.current(recorder)
      }
    }
  }, [clearOnstopFallback, clearTranscribeWatchdog, startTranscribeWatchdog, teardownWhisper])

  stopWhisperRef.current = stopWhisper

  const spawnRecognition = useCallback(() => {
    const Ctor = getSpeechRecognitionCtor()
    if (!Ctor || !listeningIntentRef.current) return false

    const sessionId = sessionIdRef.current
    const mobile = mobileRef.current
    const candidates = langCandidatesRef.current
    const recognition = new Ctor()
    recognition.lang = candidates[langIndexRef.current] ?? candidates[0] ?? speechLang(locale)
    recognition.continuous = !mobile
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      if (sessionId !== sessionIdRef.current) return
      setRequestingMic(false)
      setListening(true)
      setError(null)
      if (mobile) {
        clearListenTimeout()
        listenTimeoutRef.current = setTimeout(() => {
          if (sessionId !== sessionIdRef.current || !listeningIntentRef.current) return
          const active = recognitionRef.current
          if (!active) return
          try {
            active.stop()
          } catch {
            // ignore
          }
        }, 15000)
      }
    }

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      if (sessionId !== sessionIdRef.current) return
      const { finalText, anyText } = collectSpeechResults(event, mobile)
      if (!anyText.trim()) return
      hadResultRef.current = true

      if (finalText.trim() && !mobile) {
        pendingTranscriptRef.current = ''
        onFinalRef.current(finalText)
        setInterim('')
        onInterimRef.current?.('')
        return
      }

      pendingTranscriptRef.current = anyText
      setInterim(anyText)
      onInterimRef.current?.(anyText)
    }

    recognition.onspeechend = () => {
      if (sessionId !== sessionIdRef.current || !mobile) return
      try {
        recognition.stop()
      } catch {
        // ignore
      }
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (sessionId !== sessionIdRef.current) return

      if (event.error === 'language-not-supported') {
        const nextIndex = langIndexRef.current + 1
        const langs = langCandidatesRef.current
        if (nextIndex < langs.length && listeningIntentRef.current) {
          langIndexRef.current = nextIndex
          recognitionRef.current = null
          detachRecognition(recognition)
          spawnRecognition()
          return
        }
      }

      const mapped = mapSpeechError(event.error)
      if (mapped === 'aborted') return
      if (mapped === 'no-speech') {
        if (!hadResultRef.current && !pendingTranscriptRef.current.trim()) {
          setError('no-speech')
        }
        return
      }

      if (canUseMediaRecorder()) {
        recognitionRef.current = null
        detachRecognition(recognition)
        engineRef.current = 'whisper'
        if (listeningIntentRef.current) {
          acquireAndBeginWhisperFromGesture()
        }
        return
      }

      listeningIntentRef.current = false
      setRequestingMic(false)
      setError(mapped)
      setListening(false)
      recognitionRef.current = null
      detachRecognition(recognition)
    }

    recognition.onend = () => {
      if (sessionId !== sessionIdRef.current) return
      recognitionRef.current = null
      clearListenTimeout()
      commitPendingTranscript()

      if (!listeningIntentRef.current) {
        setListening(false)
        setRequestingMic(false)
        setInterim('')
        return
      }

      setInterim('')
      clearRestartTimer()
      const restartDelayMs = mobile ? 200 : 300
      restartTimerRef.current = setTimeout(() => {
        if (!listeningIntentRef.current) {
          setListening(false)
          return
        }
        spawnRecognition()
      }, restartDelayMs)
    }

    recognitionRef.current = recognition
    try {
      recognition.start()
      return true
    } catch {
      recognitionRef.current = null
      detachRecognition(recognition)
      return false
    }
  }, [acquireAndBeginWhisperFromGesture, clearListenTimeout, clearRestartTimer, commitPendingTranscript, locale])

  const startWebSpeech = useCallback(() => {
    if (!canUseWebSpeech()) return false

    setError(null)
    setRequestingMic(true)
    hadResultRef.current = false
    pendingTranscriptRef.current = ''

    invalidateSession()
    detachRecognition(recognitionRef.current)
    recognitionRef.current = null

    listeningIntentRef.current = true
    langCandidatesRef.current = speechLangCandidates(speechLangRef.current)
    langIndexRef.current = 0

    if (!spawnRecognition()) {
      finishListening(false)
      setError('generic')
      return false
    }
    return true
  }, [finishListening, invalidateSession, spawnRecognition])

  const stopWebSpeech = useCallback(() => {
    listeningIntentRef.current = false
    clearRestartTimer()
    clearListenTimeout()
    const recognition = recognitionRef.current
    recognitionRef.current = null
    if (recognition) {
      sessionIdRef.current += 1
      recognition.onend = () => {
        commitPendingTranscript()
        setListening(false)
        setRequestingMic(false)
        setInterim('')
      }
      recognition.onerror = null
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        const { finalText, anyText } = collectSpeechResults(event, mobileRef.current)
        if (finalText.trim()) {
          pendingTranscriptRef.current = ''
          onFinalRef.current(finalText)
        } else if (anyText.trim()) {
          pendingTranscriptRef.current = anyText
        }
      }
      try {
        recognition.stop()
        return
      } catch {
        detachRecognition(recognition)
      }
    }
    commitPendingTranscript()
    setListening(false)
    setRequestingMic(false)
    setInterim('')
  }, [clearListenTimeout, clearRestartTimer, commitPendingTranscript])

  const stop = useCallback(() => {
    if (uploadAbortRef.current || transcribing) {
      cancelActiveWork()
      return
    }
    if (engineRef.current === 'whisper' || recorderRef.current) {
      stopWhisper()
      return
    }
    stopWebSpeech()
  }, [cancelActiveWork, stopWebSpeech, stopWhisper, transcribing])

  /** Must run synchronously inside click/tap handler (iOS user-gesture requirement). */
  const handleMicPress = useCallback(() => {
    if (listening || listeningIntentRef.current || transcribing) {
      stop()
      return
    }

    engineRef.current = pickSpeechEngine()
    setError(null)
    setTranscribing(false)

    if (engineRef.current === 'whisper') {
      listeningIntentRef.current = true
      setRequestingMic(true)
      acquireAndBeginWhisperFromGesture()
      return
    }

    startWebSpeech()
  }, [acquireAndBeginWhisperFromGesture, listening, startWebSpeech, stop, transcribing])

  useEffect(() => () => finishListening(true), [finishListening])

  return {
    supported,
    listening,
    transcribing,
    interim,
    error,
    requestingMic,
    recordingSeconds,
    stop,
    handleMicPress,
  }
}