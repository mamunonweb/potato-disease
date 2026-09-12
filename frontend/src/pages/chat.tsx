import { useEffect, useRef, useState } from 'react'
import { Navigate } from 'react-router'
import { useTranslation } from 'react-i18next'
import { Bot, Send, User } from 'lucide-react'
import { toast } from 'sonner'
import { MarkdownContent } from '@/components/markdown-content'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Textarea } from '@/components/ui/textarea'
import { useChat } from '@/context/chat'
import { usePrediction } from '@/context/prediction'
import { ApiError, streamChat } from '@/lib/api'
import { cn } from '@/lib/utils'

export function ChatPage() {
  const { prediction } = usePrediction()
  const { messages, setMessages, streaming, setStreaming } = useChat()
  const { t } = useTranslation()
  const [input, setInput] = useState('')
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
            toast.error(event.text || t('chat.unavailable'))
          }
        },
      )
    } catch (error) {
      toast.error(
        error instanceof ApiError ? error.message : t('chat.cannotReach'),
      )
    } finally {
      setMessages((prev) => {
        const next = [...prev]
        const last = next[next.length - 1]
        if (!last.content) {
          next[next.length - 1] = {
            ...last,
            content: t('chat.fallback'),
          }
        }
        return next
      })
      setStreaming(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-105 w-full max-w-2xl flex-1 flex-col gap-4">
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">{t('chat.title')}</h1>
        <Badge
          variant={
            prediction.predicted_class === 'Healthy'
              ? 'secondary'
              : 'destructive'
          }
        >
          {prediction.display_name}
        </Badge>
      </div>

      <ScrollArea className="min-h-0 flex-1 rounded-lg border">
        <div className="flex flex-col gap-3 p-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={cn(
                'flex items-end gap-2',
                message.role === 'user' ? 'justify-end' : 'justify-start',
              )}
            >
              {message.role === 'assistant' && (
                <div className="bg-primary/10 flex size-7 shrink-0 items-center justify-center rounded-full">
                  <Bot className="text-primary size-4" />
                </div>
              )}
              <div
                className={cn(
                  'max-w-[85%] rounded-2xl px-4 py-2 text-sm',
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-br-sm whitespace-pre-wrap'
                    : 'bg-muted text-foreground rounded-bl-sm',
                )}
              >
                {message.role === 'assistant' ? (
                  <MarkdownContent>
                    {message.content ||
                      (streaming && index === messages.length - 1 ? '…' : '')}
                  </MarkdownContent>
                ) : (
                  message.content
                )}
              </div>
              {message.role === 'user' && (
                <div className="bg-secondary flex size-7 shrink-0 items-center justify-center rounded-full">
                  <User className="text-secondary-foreground size-4" />
                </div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <div className="flex shrink-0 items-end gap-2">
        <Textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              void send()
            }
          }}
          placeholder={t('chat.placeholder')}
          rows={2}
          maxLength={2000}
          className="resize-none"
        />
        <Button
          size="icon"
          aria-label={t('chat.send')}
          disabled={streaming || !input.trim()}
          onClick={() => void send()}
        >
          <Send className="size-4" />
        </Button>
      </div>
    </div>
  )
}
