import { useEffect, useRef, useState } from 'react'
import { Navigate } from 'react-router'
import { Send } from 'lucide-react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Textarea } from '@/components/ui/textarea'
import { usePrediction } from '@/context/prediction'
import { ApiError, streamChat } from '@/lib/api'
import { cn } from '@/lib/utils'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export function ChatPage() {
  const { prediction } = usePrediction()
  const [messages, setMessages] = useState<ChatMessage[]>(() =>
    prediction
      ? [
          {
            role: 'assistant',
            content: `Your leaf was classified as ${prediction.display_name} with ${(prediction.confidence * 100).toFixed(1)}% confidence. Ask me anything about it — symptoms, causes, or what to do next.`,
          },
        ]
      : [],
  )
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (!prediction) return <Navigate to="/" replace />

  const send = async () => {
    const text = input.trim()
    if (!text || streaming) return
    const history = [...messages]
    setInput('')
    setMessages([
      ...history,
      { role: 'user', content: text },
      { role: 'assistant', content: '' },
    ])
    setStreaming(true)

    try {
      await streamChat(
        {
          predicted_class: prediction.predicted_class,
          confidence: prediction.confidence,
          message: text,
          history,
        },
        (event) => {
          if (event.type === 'delta' && event.text) {
            setMessages((prev) => {
              const next = [...prev]
              const last = next[next.length - 1]
              next[next.length - 1] = {
                ...last,
                content: last.content + event.text,
              }
              return next
            })
          } else if (event.type === 'error') {
            toast.error(event.text || 'The assistant is unavailable right now.')
          }
        },
      )
    } catch (error) {
      toast.error(
        error instanceof ApiError
          ? error.message
          : 'Could not reach the chat service.',
      )
    } finally {
      setMessages((prev) => {
        const next = [...prev]
        const last = next[next.length - 1]
        if (!last.content) {
          next[next.length - 1] = {
            ...last,
            content: 'Sorry — I could not answer right now. Please try again.',
          }
        }
        return next
      })
      setStreaming(false)
    }
  }

  return (
    <div className="mx-auto flex h-[calc(100svh-9rem)] w-full max-w-2xl flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">Disease assistant</h1>
        <Badge variant={prediction.predicted_class === 'Potato___healthy' ? 'secondary' : 'destructive'}>
          {prediction.display_name}
        </Badge>
      </div>

      <ScrollArea className="flex-1 rounded-lg border">
        <div className="flex flex-col gap-3 p-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={cn(
                'flex',
                message.role === 'user' ? 'justify-end' : 'justify-start',
              )}
            >
              <div
                className={cn(
                  'max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm',
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground',
                )}
              >
                {message.content ||
                  (streaming && index === messages.length - 1 ? '…' : '')}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <div className="flex items-end gap-2">
        <Textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              void send()
            }
          }}
          placeholder="Ask about this condition…"
          rows={2}
          maxLength={2000}
          className="resize-none"
        />
        <Button
          size="icon"
          aria-label="Send message"
          disabled={streaming || !input.trim()}
          onClick={() => void send()}
        >
          <Send className="size-4" />
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">{prediction.disclaimer}</p>
    </div>
  )
}
