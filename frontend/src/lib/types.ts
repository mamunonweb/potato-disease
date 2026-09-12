export interface TopPrediction {
  className: string
  displayName: string
  probability: number
}

export interface GradcamSeverity {
  ratio: number
  level: string
}

export interface GradcamInfo {
  image_data_uri: string
  layer_name: string
  severity: GradcamSeverity
}

export interface GuidanceInfo {
  source: 'openrouter' | 'opencode' | 'builtin'
  description: string
  symptoms: string[]
  causes: string[]
  actions: string[]
  prevention: string[]
}

export interface PredictionResponse {
  predicted_class: string
  display_name: string
  confidence: number
  probabilities: Record<string, number>
  top_predictions: TopPrediction[]
  gradcam: GradcamInfo | null
  gradcam_note: string | null
  guidance: GuidanceInfo
  disclaimer: string
}

export interface BatchItemSuccess {
  status: 'ok'
  filename: string
  predicted_class: string
  display_name: string
  confidence: number
  top_predictions: TopPrediction[]
}

export interface BatchItemError {
  status: 'error'
  filename: string
  error: string
}

export type BatchItem = BatchItemSuccess | BatchItemError

export interface BatchResponse {
  results: BatchItem[]
  healthy_count: number
  disease_count: number
  failed_count: number
  disclaimer: string
}

export interface ChatMessagePayload {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequestBody {
  predicted_class: string
  confidence: number
  message: string
  history: ChatMessagePayload[]
}

export interface ChatStreamEvent {
  type: 'delta' | 'done' | 'error'
  text?: string
  disclaimer?: string
}
