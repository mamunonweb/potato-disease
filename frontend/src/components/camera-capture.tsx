import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
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
  const { t } = useTranslation()
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
      setError('camera.notAvailable')
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
        setError('camera.accessError')
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
          <Camera className="size-4" /> {t('camera.takePhoto')}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t('camera.dialogTitle')}</DialogTitle>
          <DialogDescription>{t('camera.dialogDescription')}</DialogDescription>
        </DialogHeader>
        <div className="overflow-hidden rounded-lg border bg-black">
          {error ? (
            <p className="text-muted-foreground p-6 text-center text-sm">
              {t(error)}
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
                <Loader2 className="size-4 animate-spin" />{' '}
                {t('camera.starting')}
              </>
            ) : (
              <>
                <Camera className="size-4" /> {t('camera.capture')}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
