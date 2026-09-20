import { Link, Navigate } from 'react-router'
import { useTranslation } from 'react-i18next'
import {
  Bug,
  CheckCircle2,
  Info,
  MessageCircle,
  ShieldCheck,
  Stethoscope,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PageContainer } from '@/components/page-container'
import { usePrediction } from '@/context/prediction'

export function InfoPage() {
  const { prediction } = usePrediction()
  const { t } = useTranslation()
  if (!prediction) return <Navigate to="/" replace />

  const guidance = prediction.guidance

  const sections = [
    { title: t('info.symptoms'), icon: Stethoscope, items: guidance.symptoms },
    { title: t('info.causes'), icon: Bug, items: guidance.causes },
    {
      title: t('info.actions'),
      icon: CheckCircle2,
      items: guidance.actions,
    },
    {
      title: t('info.prevention'),
      icon: ShieldCheck,
      items: guidance.prevention,
    },
  ]

  return (
    <PageContainer contentClassName="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">{prediction.display_name}</h1>
        <Badge variant="outline">
          {guidance.source === 'builtin'
            ? t('info.builtin')
            : t('info.aiGenerated')}
        </Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Info className="text-primary size-4" /> {t('info.overview')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed">{guidance.description}</p>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        {sections.map(({ title, icon: Icon, items }) => (
          <Card key={title}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Icon className="text-primary size-4" /> {title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="flex flex-col gap-2">
                {items.map((item) => (
                  <li key={item} className="flex gap-2 text-sm">
                    <span className="text-muted-foreground">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button asChild>
          <Link to="/chat">
            <MessageCircle className="size-4" /> {t('results.askAi')}
          </Link>
        </Button>
      </div>
    </PageContainer>
  )
}
