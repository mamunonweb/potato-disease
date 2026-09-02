import { useMutation } from '@tanstack/react-query'
import { Link, Navigate } from 'react-router'
import { BookOpen, FileDown, MessageCircle } from 'lucide-react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { usePrediction } from '@/context/prediction'
import { reportPdf } from '@/lib/api'

const DISPLAY_NAMES: Record<string, string> = {
  Potato___Early_blight: 'Early Blight',
  Potato___Late_blight: 'Late Blight',
  Potato___healthy: 'Healthy',
}

const SEVERITY_STYLES: Record<string, string> = {
  Mild: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400',
  Moderate: 'bg-amber-500/15 text-amber-700 dark:text-amber-400',
  Severe: 'bg-red-500/15 text-red-700 dark:text-red-400',
}

export function ResultsPage() {
  const { prediction, imageUrl, file } = usePrediction()

  const reportMutation = useMutation({
    mutationFn: () => {
      if (!file) return Promise.reject(new Error('Original image is gone.'))
      return reportPdf(file)
    },
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'potato_disease_report.pdf'
      link.click()
      URL.revokeObjectURL(url)
      toast.success('PDF report downloaded.')
    },
    onError: (error: Error) => toast.error(error.message),
  })

  if (!prediction || !imageUrl) return <Navigate to="/" replace />

  const isHealthy = prediction.predicted_class === 'Potato___healthy'

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Detection results</h1>
        <Badge variant={isHealthy ? 'secondary' : 'destructive'}>
          {isHealthy ? 'Healthy' : 'Disease detected'}
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Grad-CAM explanation</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <figure>
                <img
                  src={imageUrl}
                  alt="Uploaded potato leaf"
                  className="aspect-square w-full rounded-lg border object-contain"
                />
                <figcaption className="text-muted-foreground mt-1 text-center text-xs">
                  Original
                </figcaption>
              </figure>
              {prediction.gradcam ? (
                <figure>
                  <img
                    src={prediction.gradcam.image_data_uri}
                    alt="Grad-CAM attention overlay"
                    className="aspect-square w-full rounded-lg border object-contain"
                  />
                  <figcaption className="text-muted-foreground mt-1 text-center text-xs">
                    Attention overlay
                  </figcaption>
                </figure>
              ) : (
                <div className="text-muted-foreground flex aspect-square items-center justify-center rounded-lg border border-dashed p-4 text-center text-xs">
                  {prediction.gradcam_note ?? 'Grad-CAM unavailable.'}
                </div>
              )}
            </div>
            {prediction.gradcam && (
              <div className="text-muted-foreground flex flex-wrap items-center gap-2 text-sm">
                <Badge
                  className={
                    SEVERITY_STYLES[prediction.gradcam.severity.level] ?? ''
                  }
                >
                  {prediction.gradcam.severity.level}
                </Badge>
                <span>
                  attention level — an experimental estimate, not a validated
                  severity percentage.
                </span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Prediction</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div>
              <p className="text-2xl font-semibold">
                {prediction.display_name}
              </p>
              <p className="text-muted-foreground text-sm">
                Confidence {(prediction.confidence * 100).toFixed(1)}%
              </p>
            </div>
            <Separator />
            <div className="flex flex-col gap-2">
              <p className="text-sm font-medium">Class probabilities</p>
              {Object.entries(prediction.probabilities).map(
                ([className, value]) => (
                  <div key={className} className="flex flex-col gap-1">
                    <div className="flex justify-between text-sm">
                      <span>{DISPLAY_NAMES[className] ?? className}</span>
                      <span>{(value * 100).toFixed(1)}%</span>
                    </div>
                    <Progress value={value * 100} />
                  </div>
                ),
              )}
            </div>
            <div className="flex flex-wrap gap-2 pt-2">
              <Button asChild>
                <Link to="/chat">
                  <MessageCircle className="size-4" /> Ask AI about this
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link to="/info">
                  <BookOpen className="size-4" /> Disease information
                </Link>
              </Button>
              <Button
                variant="outline"
                disabled={!file || reportMutation.isPending}
                onClick={() => reportMutation.mutate()}
              >
                <FileDown className="size-4" />
                {reportMutation.isPending ? 'Generating…' : 'PDF report'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
