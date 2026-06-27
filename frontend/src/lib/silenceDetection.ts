type SilenceDetectorOptions = {
  silenceMs?: number
  minSpeechMs?: number
  threshold?: number
}

export function attachSilenceDetector(
  stream: MediaStream,
  onSilence: () => void,
  options: SilenceDetectorOptions = {},
): () => void {
  const silenceMs = options.silenceMs ?? 1800
  const minSpeechMs = options.minSpeechMs ?? 700
  const threshold = options.threshold ?? 0.018

  const AudioCtx = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
  if (!AudioCtx) {
    return () => undefined
  }

  const audioContext = new AudioCtx()
  const analyser = audioContext.createAnalyser()
  analyser.fftSize = 2048
  const source = audioContext.createMediaStreamSource(stream)
  source.connect(analyser)

  const samples = new Float32Array(analyser.fftSize)
  let rafId = 0
  let speechStartedAt: number | null = null
  let silentSince: number | null = null
  let stopped = false

  const tick = (now: number) => {
    if (stopped) return
    analyser.getFloatTimeDomainData(samples)
    let sum = 0
    for (let i = 0; i < samples.length; i += 1) {
      const v = samples[i]
      sum += v * v
    }
    const rms = Math.sqrt(sum / samples.length)
    const heardSpeech = rms > threshold

    if (heardSpeech) {
      if (speechStartedAt == null) speechStartedAt = now
      silentSince = null
    } else if (speechStartedAt != null) {
      if (silentSince == null) silentSince = now
      const spokeFor = now - speechStartedAt
      const silentFor = now - silentSince
      if (spokeFor >= minSpeechMs && silentFor >= silenceMs) {
        stopped = true
        onSilence()
        return
      }
    }

    rafId = window.requestAnimationFrame(tick)
  }

  rafId = window.requestAnimationFrame(tick)

  return () => {
    stopped = true
    if (rafId) window.cancelAnimationFrame(rafId)
    source.disconnect()
    void audioContext.close()
  }
}