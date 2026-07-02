import { useEffect, useRef, useCallback } from 'react'

interface VideoBackgroundProps {
  src: string
}

export function VideoBackground({ src }: VideoBackgroundProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const opacityRef = useRef(1)
  const animFrameRef = useRef<number>(0)
  const fadingOutRef = useRef(false)

  const cancelAnim = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current)
      animFrameRef.current = 0
    }
  }, [])

  const fadeTo = useCallback((targetOpacity: number, duration: number, onDone?: () => void) => {
    cancelAnim()
    const startOpacity = opacityRef.current
    const delta = targetOpacity - startOpacity
    const startTime = performance.now()

    function animate(now: number) {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      opacityRef.current = startOpacity + delta * progress
      if (videoRef.current) {
        videoRef.current.style.opacity = String(opacityRef.current)
      }
      if (progress < 1) {
        animFrameRef.current = requestAnimationFrame(animate)
      } else if (onDone) {
        onDone()
      }
    }

    animFrameRef.current = requestAnimationFrame(animate)
  }, [cancelAnim])

  const handleTimeUpdate = useCallback(() => {
    const video = videoRef.current
    if (!video) return

    const remaining = video.duration - video.currentTime

    if (!fadingOutRef.current && remaining <= 0.55 && video.duration > 1) {
      fadingOutRef.current = true
      fadeTo(0, 250, () => {
        video.style.opacity = '0'
      })
    }
  }, [fadeTo])

  const handleEnded = useCallback(() => {
    const video = videoRef.current
    if (!video) return

    video.style.opacity = '0'
    fadingOutRef.current = false

    setTimeout(() => {
      video.currentTime = 0
      video.play()
      fadeTo(1, 250)
    }, 100)
  }, [fadeTo])

  const handleLoadedMetadata = useCallback(() => {
    const video = videoRef.current
    if (!video) return
    video.style.opacity = '0'
    fadingOutRef.current = false
    fadeTo(1, 250)
  }, [fadeTo])

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    video.addEventListener('timeupdate', handleTimeUpdate)
    video.addEventListener('ended', handleEnded)
    video.addEventListener('loadedmetadata', handleLoadedMetadata)

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate)
      video.removeEventListener('ended', handleEnded)
      video.removeEventListener('loadedmetadata', handleLoadedMetadata)
      cancelAnim()
    }
  }, [handleTimeUpdate, handleEnded, handleLoadedMetadata, cancelAnim])

  return (
    <div className="absolute inset-0 w-full h-full overflow-hidden">
      <video
        ref={videoRef}
        src={src}
        muted
        loop
        playsInline
        autoPlay
        preload="auto"
        style={{
          width: '115%',
          height: '115%',
          objectFit: 'cover',
          objectPosition: 'center top',
          opacity: 0,
        }}
      />
      <div className="absolute inset-0 bg-white/70" />
    </div>
  )
}
