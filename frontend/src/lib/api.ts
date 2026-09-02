import type {
  BatchResponse,
  ChatRequestBody,
  ChatStreamEvent,
  PredictionResponse,
} from './types'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {}

async function errorDetail(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown }
    if (typeof body.detail === 'string') return body.detail
  } catch {
    /* ignore malformed error bodies */
  }
  return `Request failed with status ${res.status}.`
}

export async function predictImage(file: File): Promise<PredictionResponse> {
  const form = new FormData()
  form.append('image', file)
  const res = await fetch(`${API_BASE_URL}/api/predict`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new ApiError(await errorDetail(res))
  return (await res.json()) as PredictionResponse
}

export async function predictBatch(files: File[]): Promise<BatchResponse> {
  const form = new FormData()
  for (const file of files) form.append('images', file)
  const res = await fetch(`${API_BASE_URL}/api/predict/batch`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new ApiError(await errorDetail(res))
  return (await res.json()) as BatchResponse
}

export async function reportPdf(file: File): Promise<Blob> {
  const form = new FormData()
  form.append('image', file)
  const res = await fetch(`${API_BASE_URL}/api/report`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new ApiError(await errorDetail(res))
  return await res.blob()
}

export async function streamChat(
  body: ChatRequestBody,
  onEvent: (event: ChatStreamEvent) => void,
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok || !res.body) throw new ApiError(await errorDetail(res))

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''
    for (const part of parts) {
      const line = part.trim()
      if (!line.startsWith('data: ')) continue
      try {
        onEvent(JSON.parse(line.slice(6)) as ChatStreamEvent)
      } catch {
        /* ignore malformed SSE chunks */
      }
    }
  }
}
