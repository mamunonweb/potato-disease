import {
  createContext,
  useContext,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from 'react'
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

function greetingFor(prediction: PredictionResponse): ChatMessage {
  return {
    role: 'assistant',
    content: `Your leaf was classified as ${prediction.display_name} with ${(prediction.confidence * 100).toFixed(1)}% confidence. Ask me anything about it — symptoms, causes, or what to do next.`,
  }
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const { prediction } = usePrediction()
  const [state, setState] = useState<{
    prediction: PredictionResponse | null
    messages: ChatMessage[]
  }>(() => ({
    prediction: prediction ?? null,
    messages: prediction ? [greetingFor(prediction)] : [],
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
      messages: prediction ? [greetingFor(prediction)] : [],
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
