import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import type { PredictionResponse } from '@/lib/types'

interface PredictionContextValue {
  prediction: PredictionResponse | null
  imageUrl: string | null
  setPrediction: (prediction: PredictionResponse, file: File) => void
  clear: () => void
}

const PredictionContext = createContext<PredictionContextValue | null>(null)

export function PredictionProvider({ children }: { children: ReactNode }) {
  const [prediction, setPredictionState] = useState<PredictionResponse | null>(null)
  const [imageUrl, setImageUrl] = useState<string | null>(null)

  const value = useMemo<PredictionContextValue>(
    () => ({
      prediction,
      imageUrl,
      setPrediction: (next, file) => {
        setImageUrl((current) => {
          if (current) URL.revokeObjectURL(current)
          return URL.createObjectURL(file)
        })
        setPredictionState(next)
      },
      clear: () => {
        setImageUrl((current) => {
          if (current) URL.revokeObjectURL(current)
          return null
        })
        setPredictionState(null)
      },
    }),
    [prediction, imageUrl],
  )

  return (
    <PredictionContext.Provider value={value}>
      {children}
    </PredictionContext.Provider>
  )
}

export function usePrediction(): PredictionContextValue {
  const context = useContext(PredictionContext)
  if (!context) {
    throw new Error('usePrediction must be used within PredictionProvider')
  }
  return context
}
