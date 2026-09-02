import { useCallback, useEffect, useRef, useState } from 'react'
import { Camera, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

interface CameraCaptureProps {
  onCapture: (file: File) => void
}

export function CameraCapture({ onCapture }: CameraCaptureProps) {
  const [open, setOpen] = useState(false)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    setReady(false)
  }, [])

  useEffect(() => {
    if (!open) {
      stopStream()
      return
    }
    setError(null)
    setStarting(true)

    if (!navigator.mediaDevices?.getUserMedia) {
      setError(
        'Camera access is not available. Use HTTPS (or localhost) and a browser that supports getUserMedia.',
      )
      setStarting(false)
      return
    }

    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: 'environment' } })
      .then((stream) => {
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.play()
        }
        setStarting(false)
        setReady(true)
      })
      .catch(() => {
        setError(
          'Could not access the camera. Check browser permissions and try again.',
        )
        setStarting(false)
      })

    return stopStream
  }, [open, stopStream])

  function capture() {
    const video = videoRef.current
    if (!video || !ready) return
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const context = canvas.getContext('2d')
    if (!context) return
    context.drawImage(video, 0, 0)
    canvas.toBlob(
      (blob) => {
        if (!blob) return
        onCapture(
          new File([blob], 'camera_capture.jpg', { type: 'image/jpeg' }),
        )
        setOpen(false)
      },
      'image/jpeg',
      0.92,
    )
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Camera className="size-4" /> Take a photo
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Take a photo of the leaf</DialogTitle>
          <DialogDescription>
            Hold the leaf steady in good light, then capture.
          </DialogDescription>
        </DialogHeader>
        <div className="overflow-hidden rounded-lg border bg-black">
          {error ? (
            <p className="text-muted-foreground p-6 text-center text-sm">
              {error}
            </p>
          ) : (
            <video
              ref={videoRef}
              playsInline
              muted
              className="aspect-4/3 w-full object-cover"
            />
          )}
        </div>
        <DialogFooter>
          <Button className="w-full" disabled={!ready} onClick={capture}>
            {starting ? (
              <>
                <Loader2 className="size-4 animate-spin" /> Starting camera…
              </>
            ) : (
              <>
                <Camera className="size-4" /> Capture photo
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
