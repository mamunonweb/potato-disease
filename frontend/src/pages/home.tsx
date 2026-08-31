import { Leaf } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export function HomePage() {
  return (
    <div className="flex min-h-svh items-center justify-center bg-background p-4">
      <Card className="w-full max-w-lg text-center">
        <CardHeader>
          <div className="mx-auto mb-2 flex size-12 items-center justify-center rounded-full bg-primary/10">
            <Leaf className="size-6 text-primary" />
          </div>
          <CardTitle className="text-2xl">Potato Disease Detection</CardTitle>
          <CardDescription>
            Upload a potato leaf image to detect diseases with an explainable
            CNN, then chat about the result.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center gap-4">
          <div className="flex flex-wrap justify-center gap-2">
            <Badge variant="secondary">Grad-CAM</Badge>
            <Badge variant="secondary">AI Guidance</Badge>
            <Badge variant="secondary">Chat</Badge>
          </div>
          <Button size="lg" disabled>
            Coming soon
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
