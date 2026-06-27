import { useEffect, useRef, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import type { StringKey } from '../i18n/strings'
import {
  appendTranscript,
  isMobileDevice,
  speechLang,
  useSpeechToText,
  type SpeechToTextError,
} from '../hooks/useSpeechToText'

export type SpeechToTextLanguage = 'th-TH' | 'en-US'

type SpeechToTextControlProps = {
  value: string
  onChange: (next: string) => void
  disabled?: boolean
  prominent?: boolean
  hintKey?: StringKey
  className?: string
  defaultSpeechLang?: SpeechToTextLanguage
  showLanguageToggle?: boolean
  showClearButton?: boolean
  onClear?: () => void
  clearLabelKey?: StringKey
}

function errorMessageKey(err: SpeechToTextError): StringKey {
  switch (err) {
    case 'not-allowed':
      return 'sttErrorMic'
    case 'server':
      return 'sttErrorServer'
    case 'no-speech':
      return 'sttErrorNoSpeech'
    case 'network':
      return 'sttErrorNetwork'
    case 'audio-capture':
      return 'sttErrorMic'
    case 'ios':
    case 'unsupported':
      return 'sttUnsupported'
    default:
      return 'sttErrorGeneric'
  }
}

export function SpeechToTextControl({
  value,
  onChange,
  disabled = false,
  prominent = false,
  hintKey = 'sttGardenHint',
  className = '',
  defaultSpeechLang,
  showLanguageToggle = false,
  showClearButton = false,
  onClear,
  clearLabelKey = 'sttClear',
}: SpeechToTextControlProps) {
  const { locale, tr, trf } = useLocale()
  const valueRef = useRef(value)
  const listenBaseRef = useRef(value)
  const [sttLang, setSttLang] = useState<SpeechToTextLanguage>(
    () => defaultSpeechLang ?? (speechLang(locale) as SpeechToTextLanguage),
  )
  const effectiveSpeechLang = showLanguageToggle ? sttLang : 'auto'

  useEffect(() => {
    valueRef.current = value
  }, [value])

  useEffect(() => {
    if (!defaultSpeechLang) {
      setSttLang(speechLang(locale) as SpeechToTextLanguage)
    }
  }, [defaultSpeechLang, locale])

  const {
    supported,
    listening,
    transcribing,
    recordingSeconds,
    interim,
    error,
    requestingMic,
    stop,
    handleMicPress,
  } = useSpeechToText({
    locale,
    speechLang: effectiveSpeechLang,
    onFinalTranscript: (text) => {
      const next = appendTranscript(listenBaseRef.current, text)
      listenBaseRef.current = next
      valueRef.current = next
      onChange(next)
    },
    onInterimTranscript: (text) => {
      if (!isMobileDevice()) return
      onChange(appendTranscript(listenBaseRef.current, text))
    },
  })

  useEffect(() => {
    if (listening) {
      listenBaseRef.current = valueRef.current
    }
  }, [listening])

  const pickSpeechLang = (next: SpeechToTextLanguage) => {
    if (next === sttLang) return
    if (listening || transcribing) stop()
    setSttLang(next)
  }

  const handleClear = () => {
    if (listening || transcribing || requestingMic) stop()
    listenBaseRef.current = ''
    valueRef.current = ''
    if (onClear) {
      onClear()
      return
    }
    onChange('')
  }

  if (!supported) {
    return (
      <p className={`text-xs font-medium text-amber-900/90 ${className}`} role="status">
        {tr('sttUnsupported')}
      </p>
    )
  }

  const active = listening || transcribing || requestingMic

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={disabled}
          onClick={handleMicPress}
          aria-pressed={active}
          aria-label={
            transcribing ? tr('sttCancel') : listening ? tr('sttListening') : tr('sttSpeak')
          }
          className={`touch-target inline-flex items-center gap-2.5 rounded-2xl border-2 font-bold transition-all ${
            prominent ? 'min-h-[3.25rem] px-5 py-3 text-base sm:text-lg' : 'min-h-[2.75rem] px-4 py-2.5 text-sm'
          } ${
            active
              ? 'border-red-300 bg-red-50 text-red-900 shadow-[0_0_0_4px_rgba(248,113,113,0.25)]'
              : 'border-[var(--color-sage)]/60 bg-white text-[var(--color-text)] hover:border-[var(--color-market)] hover:bg-[var(--color-surface-overlay)]'
          } ${listening ? 'animate-pulse' : ''} disabled:cursor-not-allowed disabled:opacity-50`}
        >
          <span className="text-xl leading-none" aria-hidden>
            {listening ? '⏹' : transcribing ? '✕' : '🎙️'}
          </span>
          <span>
            {requestingMic
              ? tr('sttRequestingMic')
              : transcribing
                ? tr('sttCancel')
                : listening
                  ? tr('sttStop')
                  : tr('sttSpeak')}
          </span>
        </button>

        {showClearButton && value.trim() && (
          <button
            type="button"
            disabled={disabled}
            onClick={handleClear}
            aria-label={tr(clearLabelKey)}
            className={`touch-target inline-flex items-center gap-2 rounded-2xl border-2 border-[var(--color-border)] bg-white font-bold text-[var(--color-text-soft)] transition-colors hover:border-[var(--color-market)]/50 hover:bg-[var(--color-surface-overlay)] hover:text-[var(--color-text)] disabled:cursor-not-allowed disabled:opacity-50 ${
              prominent ? 'min-h-[3.25rem] px-4 py-3 text-base' : 'min-h-[2.75rem] px-3.5 py-2.5 text-sm'
            }`}
          >
            <span className="text-lg leading-none" aria-hidden>
              🗑️
            </span>
            <span>{tr(clearLabelKey)}</span>
          </button>
        )}

        {showLanguageToggle && (
          <div
            className="inline-flex rounded-xl border-2 border-[var(--color-border)] bg-white p-1"
            role="group"
            aria-label={tr('sttLangLabel')}
          >
            {(['th-TH', 'en-US'] as const).map((code) => (
              <button
                key={code}
                type="button"
                disabled={disabled || active}
                aria-pressed={sttLang === code}
                onClick={() => pickSpeechLang(code)}
                className={`min-h-[2.5rem] rounded-lg px-3 py-1.5 text-sm font-bold transition-colors ${
                  sttLang === code
                    ? 'bg-[var(--color-market)] text-white shadow-sm'
                    : 'text-[var(--color-text-soft)] hover:bg-[var(--color-surface-overlay)] hover:text-[var(--color-text)]'
                } disabled:cursor-not-allowed disabled:opacity-50`}
              >
                {tr(code === 'th-TH' ? 'sttLangTh' : 'sttLangEn')}
              </button>
            ))}
          </div>
        )}

        <p className="text-sm font-medium text-readable-muted">{tr(hintKey)}</p>
      </div>

      {error && (
        <p
          className="rounded-xl border border-amber-300/80 bg-amber-50 px-3 py-2 text-sm font-medium text-amber-950"
          role="alert"
        >
          {tr(errorMessageKey(error))}
        </p>
      )}

      {active && !error && (
        <p
          className="rounded-xl border border-red-200/80 bg-red-50/60 px-3 py-2 text-sm font-medium text-red-950"
          role="status"
        >
          {transcribing ? (
            tr('sttTranscribing')
          ) : listening ? (
            trf('sttListeningSeconds', { seconds: String(recordingSeconds) })
          ) : (
            tr('sttRequestingMic')
          )}
          {transcribing ? (
            <span className="mt-1 block text-xs font-medium text-[var(--color-text-soft)]">
              {tr('sttTranscribingHint')}
            </span>
          ) : listening ? (
            <>
              {interim ? (
                <span className="mt-1 block text-[var(--color-text-soft)]">“{interim}”</span>
              ) : (
                <span className="mt-1 block text-xs font-medium text-[var(--color-text-soft)]">
                  {tr('sttSpeakNow')}
                </span>
              )}
            </>
          ) : null}
        </p>
      )}
    </div>
  )
}