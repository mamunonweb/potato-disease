import { Link, Navigate } from 'react-router'
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
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { usePrediction } from '@/context/prediction'

export function InfoPage() {
  const { prediction } = usePrediction()
  if (!prediction) return <Navigate to="/" replace />

  const guidance = prediction.guidance

  const sections = [
    { title: 'Symptoms', icon: Stethoscope, items: guidance.symptoms },
    { title: 'Possible causes', icon: Bug, items: guidance.causes },
    { title: 'Recommended actions', icon: CheckCircle2, items: guidance.actions },
    { title: 'Prevention', icon: ShieldCheck, items: guidance.prevention },
  ]

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">
          {prediction.display_name}
        </h1>
        <Badge variant="outline">
          {guidance.source === 'openrouter'
            ? 'AI-generated guidance'
            : 'Built-in guidance'}
        </Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Info className="size-4 text-primary" /> Overview
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
                <Icon className="size-4 text-primary" /> {title}
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
            <MessageCircle className="size-4" /> Ask AI about this
          </Link>
        </Button>
      </div>
    </div>
  )
}
