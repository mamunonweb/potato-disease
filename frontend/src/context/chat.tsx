import {
  createContext,
  useContext,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { usePrediction } from '@/context/prediction'
import type { PredictionResponse } from '@/lib/types'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface ChatContextValue {
  messages: ChatMessage[]
  setMessages: Dispatch<SetStateAction<ChatMessage[]>>
  streaming: boolean
  setStreaming: Dispatch<SetStateAction<boolean>>
}

const ChatContext = createContext<ChatContextValue | null>(null)

function greetingFor(
  prediction: PredictionResponse,
  t: TFunction,
): ChatMessage {
  return {
    role: 'assistant',
    content: t('chat.greeting', {
      name: t(`classes.${prediction.predicted_class}`, {
        defaultValue: prediction.display_name,
      }),
      confidence: (prediction.confidence * 100).toFixed(1),
    }),
  }
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const { prediction } = usePrediction()
  const { t, i18n } = useTranslation()
  const language = i18n.resolvedLanguage ?? i18n.language

  const [state, setState] = useState<{
    prediction: PredictionResponse | null
    language: string
    messages: ChatMessage[]
  }>(() => ({
    prediction: prediction ?? null,
    language,
    messages: prediction ? [greetingFor(prediction, t)] : [],
  }))
  const [streaming, setStreaming] = useState(false)

  const setMessages: Dispatch<SetStateAction<ChatMessage[]>> = (action) => {
    setState((prev) => ({
      ...prev,
      messages: typeof action === 'function' ? action(prev.messages) : action,
    }))
  }

  if (state.prediction !== prediction) {
    setState({
      prediction: prediction ?? null,
      language,
      messages: prediction ? [greetingFor(prediction, t)] : [],
    })
  } else if (state.language !== language) {
    // Language changed: refresh the opening greeting without dropping the chat.
    setState((prev) => {
      const messages = [...prev.messages]
      if (
        messages.length > 0 &&
        messages[0].role === 'assistant' &&
        prediction
      ) {
        messages[0] = greetingFor(prediction, t)
      }
      return { ...prev, language, messages }
    })
  }

  const value = {
    messages: state.messages,
    setMessages,
    streaming,
    setStreaming,
  }

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

export function useChat(): ChatContextValue {
  const context = useContext(ChatContext)
  if (!context) {
    throw new Error('useChat must be used within ChatProvider')
  }
  return context
}
