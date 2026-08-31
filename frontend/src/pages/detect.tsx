import { useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { Loader2, ScanSearch } from 'lucide-react'
import { toast } from 'sonner'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
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
            <span className="absolute inset-x-0 bottom-0 bg-background/80 py-1 text-center text-xs text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100">
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
            className="flex min-h-52 cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-6 text-center text-muted-foreground transition-colors hover:bg-accent/40"
          >
            <ScanSearch className="size-8" />
            <p className="text-sm font-medium">
              Click or drop a potato leaf image
            </p>
            <p className="text-xs">
              JPG or PNG, up to {MAX_SIZE_MB} MB
            </p>
          </div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png"
          className="hidden"
          onChange={(event) =>
            selectFile(event.target.files?.[0] ?? null)
          }
        />
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
        <Alert>
          <AlertDescription className="text-xs">
            This is an AI-based preliminary classification, not a
            definitive diagnosis. For serious or rapidly spreading crop
            disease, consult a qualified agricultural professional.
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  )
}
