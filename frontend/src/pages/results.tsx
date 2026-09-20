import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link, Navigate } from 'react-router'
import { useTranslation } from 'react-i18next'
import { BookOpen, FileDown, MessageCircle } from 'lucide-react'
import { toast } from 'sonner'
import { PageContainer } from '@/components/page-container'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { usePrediction } from '@/context/prediction'
import { reportPdf } from '@/lib/api'

const SEVERITY_STYLES: Record<string, string> = {
  Mild: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400',
  Moderate: 'bg-amber-500/15 text-amber-700 dark:text-amber-400',
  Severe: 'bg-red-500/15 text-red-700 dark:text-red-400',
}

export function ResultsPage() {
  const { prediction, imageUrl, file } = usePrediction()
  const { t } = useTranslation()
  const [showAll, setShowAll] = useState(false)

  const reportMutation = useMutation({
    mutationFn: () => {
      if (!file) return Promise.reject(new Error(t('results.originalGone')))
      return reportPdf(file)
    },
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'potato_disease_report.pdf'
      link.click()
      URL.revokeObjectURL(url)
      toast.success(t('results.reportDownloaded'))
    },
    onError: (error: Error) => toast.error(error.message),
  })

  if (!prediction || !imageUrl) return <Navigate to="/" replace />

  const isHealthy = prediction.predicted_class === 'Healthy'

  const sortedProbabilities = Object.entries(prediction.probabilities).sort(
    ([, a], [, b]) => b - a,
  )
  const visibleProbabilities = showAll
    ? sortedProbabilities
    : sortedProbabilities.slice(0, 3)

  return (
    <PageContainer contentClassName="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">{t('results.title')}</h1>
        <Badge variant={isHealthy ? 'secondary' : 'destructive'}>
          {isHealthy ? t('results.healthy') : t('results.diseaseDetected')}
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {t('results.gradcamTitle')}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <Tabs defaultValue="original" className="sm:hidden">
              <TabsList className="w-full">
                <TabsTrigger value="original">
                  {t('results.original')}
                </TabsTrigger>
                <TabsTrigger value="gradcam">
                  {t('results.attentionOverlay')}
                </TabsTrigger>
              </TabsList>
              <TabsContent value="original" className="mt-3">
                <img
                  src={imageUrl}
                  alt={t('results.uploadedAlt')}
                  className="max-h-[45vh] w-full rounded-lg border object-contain"
                />
              </TabsContent>
              <TabsContent value="gradcam" className="mt-3">
                {prediction.gradcam ? (
                  <img
                    src={prediction.gradcam.image_data_uri}
                    alt={t('results.gradcamAlt')}
                    className="max-h-[45vh] w-full rounded-lg border object-contain"
                  />
                ) : (
                  <div className="text-muted-foreground flex min-h-40 items-center justify-center rounded-lg border border-dashed p-4 text-center text-xs">
                    {t('results.gradcamUnavailable')}
                  </div>
                )}
              </TabsContent>
            </Tabs>

            <div className="hidden gap-3 sm:grid sm:grid-cols-2">
              <figure>
                <img
                  src={imageUrl}
                  alt={t('results.uploadedAlt')}
                  className="aspect-square w-full rounded-lg border object-contain"
                />
                <figcaption className="text-muted-foreground mt-1 text-center text-xs">
                  {t('results.original')}
                </figcaption>
              </figure>
              {prediction.gradcam ? (
                <figure>
                  <img
                    src={prediction.gradcam.image_data_uri}
                    alt={t('results.gradcamAlt')}
                    className="aspect-square w-full rounded-lg border object-contain"
                  />
                  <figcaption className="text-muted-foreground mt-1 text-center text-xs">
                    {t('results.attentionOverlay')}
                  </figcaption>
                </figure>
              ) : (
                <div className="text-muted-foreground flex aspect-square items-center justify-center rounded-lg border border-dashed p-4 text-center text-xs">
                  {t('results.gradcamUnavailable')}
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
                  {t(`severity.${prediction.gradcam.severity.level}`, {
                    defaultValue: prediction.gradcam.severity.level,
                  })}
                </Badge>
                <span>
                  {t('results.attentionLevel', {
                    level: t(`severity.${prediction.gradcam.severity.level}`, {
                      defaultValue: prediction.gradcam.severity.level,
                    }),
                  })}
                </span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {t('results.predictionTitle')}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div>
              <p className="text-2xl font-semibold">
                {prediction.display_name}
              </p>
              <p className="text-muted-foreground text-sm">
                {t('results.confidence', {
                  value: (prediction.confidence * 100).toFixed(1),
                })}
              </p>
            </div>
            <Separator />
            <div className="flex flex-col gap-2">
              <p className="text-sm font-medium">
                {t('results.classProbabilities')}
              </p>
              {visibleProbabilities.map(([className, value]) => (
                <div key={className} className="flex flex-col gap-1">
                  <div className="flex justify-between text-sm">
                    <span>
                      {t(`classes.${className}`, {
                        defaultValue: className,
                      })}
                    </span>
                    <span>{(value * 100).toFixed(1)}%</span>
                  </div>
                  <Progress value={value * 100} />
                </div>
              ))}
              {sortedProbabilities.length > 3 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-1 w-fit"
                  onClick={() => setShowAll((current) => !current)}
                >
                  {showAll
                    ? t('results.showTopClasses')
                    : t('results.showAllClasses')}
                </Button>
              )}
            </div>
            <div className="flex flex-wrap gap-2 pt-2">
              <Button asChild>
                <Link to="/chat">
                  <MessageCircle className="size-4" /> {t('results.askAi')}
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link to="/info">
                  <BookOpen className="size-4" /> {t('results.diseaseInfo')}
                </Link>
              </Button>
              <Button
                variant="outline"
                disabled={!file || reportMutation.isPending}
                onClick={() => reportMutation.mutate()}
              >
                <FileDown className="size-4" />
                {reportMutation.isPending
                  ? t('results.generating')
                  : t('results.pdfReport')}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
