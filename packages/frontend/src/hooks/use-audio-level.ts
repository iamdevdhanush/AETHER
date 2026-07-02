import { useEffect, useRef } from 'react'
import { useAICoreStore } from '@/stores/ai-core-store'

export function useAudioLevel(stream?: MediaStream | null) {
  const setAmplitude = useAICoreStore((state) => state.setAmplitude)
  const contextRef = useRef<AudioContext | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)

  useEffect(() => {
    if (!stream) {
      setAmplitude(0)
      return
    }

    const context = new AudioContext()
    const source = context.createMediaStreamSource(stream)
    const analyser = context.createAnalyser()
    analyser.fftSize = 256
    source.connect(analyser)

    contextRef.current = context
    sourceRef.current = source
    analyserRef.current = analyser

    const dataArray = new Uint8Array(analyser.frequencyBinCount)

    const animate = () => {
      analyser.getByteTimeDomainData(dataArray)
      let sum = 0
      for (let i = 0; i < dataArray.length; i++) {
        const value = (dataArray[i] - 128) / 128
        sum += value * value
      }
      const rms = Math.sqrt(sum / dataArray.length)
      setAmplitude(Math.min(rms * 3, 1))
      requestAnimationFrame(animate)
    }

    animate()

    return () => {
      context.close()
    }
  }, [stream, setAmplitude])

  return null
}
