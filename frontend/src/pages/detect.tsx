import { useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { useTranslation } from 'react-i18next'
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
import { PageContainer } from '@/components/page-container'
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
  const { t } = useTranslation()

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
          : t('common.predictionFailed'),
      )
    },
  })

  function selectFile(next: File | null) {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(null)
    setFile(null)
    if (!next) return
    if (!ALLOWED_TYPES.includes(next.type)) {
      toast.error(t('common.unsupportedFile'))
      return
    }
    if (next.size > MAX_SIZE_MB * 1024 * 1024) {
      toast.error(t('common.imageTooLarge', { mb: MAX_SIZE_MB }))
      return
    }
    setFile(next)
    setPreviewUrl(URL.createObjectURL(next))
  }

  return (
    <PageContainer contentClassName="flex flex-col gap-4 sm:gap-8">
      <section className="from-primary/10 via-accent/40 to-background relative overflow-hidden rounded-2xl border bg-linear-to-br px-4 py-4 text-center sm:px-10 sm:py-16">
        <div className="mx-auto flex max-w-2xl flex-col items-center gap-3 sm:gap-4">
          <Badge variant="secondary">{t('detect.badge')}</Badge>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-4xl lg:text-5xl">
            {t('detect.titlePrefix')}{' '}
            <span className="text-primary">{t('detect.titleAccent')}</span>
          </h1>
          <p className="text-muted-foreground max-w-xl text-sm leading-relaxed sm:text-base">
            {t('detect.subtitle')}
          </p>
        </div>
      </section>

      <Card className="mx-auto w-full max-w-xl">
        <CardHeader className="text-center">
          <CardTitle className="text-xl">{t('detect.cardTitle')}</CardTitle>
          <CardDescription>{t('detect.cardDescription')}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {previewUrl ? (
            <div className="flex flex-col items-center gap-2">
              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                className="block max-w-full overflow-hidden rounded-lg border"
              >
                <img
                  src={previewUrl}
                  alt={t('detect.previewAlt')}
                  className="max-h-40 w-auto max-w-full object-contain sm:max-h-80"
                />
              </button>
              <p className="text-muted-foreground text-xs">
                {t('detect.previewHint')}
              </p>
            </div>
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
              className="text-muted-foreground hover:bg-accent/40 flex min-h-32 cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-4 text-center transition-colors sm:min-h-52 sm:p-6"
            >
              <ScanSearch className="size-8" />
              <p className="text-sm font-medium">{t('detect.dropzoneTitle')}</p>
              <p className="text-xs">
                {t('detect.dropzoneHint', { mb: MAX_SIZE_MB })}
              </p>
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
        </CardContent>
      </Card>

      <div className="bg-background/95 sticky bottom-0 z-10 mx-auto w-full max-w-xl pt-2 backdrop-blur sm:static sm:pt-0">
        <Button
          size="lg"
          className="w-full"
          disabled={!file || mutation.isPending}
          onClick={() => file && mutation.mutate(file)}
        >
          {mutation.isPending ? (
            <>
              <Loader2 className="size-4 animate-spin" />{' '}
              {t('detect.analyzing')}
            </>
          ) : (
            <>
              <ScanSearch className="size-4" /> {t('detect.analyze')}
            </>
          )}
        </Button>
      </div>
    </PageContainer>
  )
}
