import { useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { Loader2, ScanSearch } from 'lucide-react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { CameraCapture } from '@/components/camera-capture'
import { usePrediction } from '@/context/prediction'
import { ApiError, predictImage } from '@/lib/api'

const ALLOWED_TYPES = ['image/jpeg', 'image/png']
const MAX_SIZE_MB = 10

export function DetectPage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const { setPrediction } = usePrediction()
  const navigate = useNavigate()

  const mutation = useMutation({
    mutationFn: (selected: File) => predictImage(selected),
    onSuccess: (data, selected) => {
      setPrediction(data, selected)
      navigate('/results')
    },
    onError: (error) => {
      toast.error(
        error instanceof ApiError
          ? error.message
          : 'Prediction failed. Is the backend running?',
      )
    },
  })

  function selectFile(next: File | null) {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(null)
    setFile(null)
    if (!next) return
    if (!ALLOWED_TYPES.includes(next.type)) {
      toast.error('Unsupported file type. Upload a JPG or PNG image.')
      return
    }
    if (next.size > MAX_SIZE_MB * 1024 * 1024) {
      toast.error(`Image too large. Maximum size is ${MAX_SIZE_MB} MB.`)
      return
    }
    setFile(next)
    setPreviewUrl(URL.createObjectURL(next))
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="from-primary/10 via-accent/40 to-background grid items-center gap-6 overflow-hidden rounded-2xl border bg-linear-to-br p-6 sm:p-8 lg:grid-cols-[1.2fr_1fr]">
        <div className="flex flex-col gap-3">
          <Badge className="w-fit" variant="secondary">
            Explainable CNN · Grad-CAM · AI chat
          </Badge>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Spot potato diseases{' '}
            <span className="text-primary">in seconds</span>
          </h1>
          <p className="text-muted-foreground max-w-md text-sm leading-relaxed sm:text-base">
            Upload a leaf photo and get a prediction with a heatmap showing
            exactly where the model looked — then ask the AI assistant what to
            do about it.
          </p>
        </div>
        <img
          src="/og-image.png"
          alt="Potato leaf with Grad-CAM attention overlay"
          className="hidden w-full rounded-xl border shadow-lg lg:block"
          loading="eager"
        />
      </section>

      <Card className="mx-auto w-full max-w-xl">
        <CardHeader className="text-center">
          <CardTitle className="text-xl">Analyze a potato leaf</CardTitle>
          <CardDescription>
            Upload a clear photo of a potato leaf. The CNN predicts the
            condition and Grad-CAM shows where it looked.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {previewUrl ? (
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="group relative overflow-hidden rounded-lg border"
            >
              <img
                src={previewUrl}
                alt="Selected leaf preview"
                className="max-h-80 w-full object-contain"
              />
              <span className="bg-background/80 text-muted-foreground absolute inset-x-0 bottom-0 py-1 text-center text-xs opacity-0 transition-opacity group-hover:opacity-100">
                Click to choose a different image
              </span>
            </button>
          ) : (
            <div
              role="button"
              tabIndex={0}
              onClick={() => inputRef.current?.click()}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  inputRef.current?.click()
                }
              }}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault()
                selectFile(event.dataTransfer.files?.[0] ?? null)
              }}
              className="text-muted-foreground hover:bg-accent/40 flex min-h-52 cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-6 text-center transition-colors"
            >
              <ScanSearch className="size-8" />
              <p className="text-sm font-medium">
                Click or drop a potato leaf image
              </p>
              <p className="text-xs">JPG or PNG, up to {MAX_SIZE_MB} MB</p>
            </div>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png"
            className="hidden"
            onChange={(event) => selectFile(event.target.files?.[0] ?? null)}
          />
          <CameraCapture onCapture={selectFile} />
          <Button
            size="lg"
            disabled={!file || mutation.isPending}
            onClick={() => file && mutation.mutate(file)}
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="size-4 animate-spin" /> Analyzing…
              </>
            ) : (
              <>
                <ScanSearch className="size-4" /> Analyze image
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
