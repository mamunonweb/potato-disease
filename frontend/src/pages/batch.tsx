import { useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Download, Layers, Loader2, ScanSearch, X } from 'lucide-react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { predictBatch } from '@/lib/api'
import type { BatchItem, BatchResponse } from '@/lib/types'
import { cn } from '@/lib/utils'

const MAX_BATCH_FILES = 12
const MAX_FILE_MB = 10

const PREDICTION_STYLES: Record<string, string> = {
  Bacteria: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
  Fungi:
    'bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300',
  Healthy:
    'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
  Phytopthora: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300',
  Virus: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
}

function csvEscape(value: string): string {
  if (/[",\n]/.test(value)) return `"${value.replace(/"/g, '""')}"`
  return value
}

function downloadCsv(results: BatchItem[], header: string[], errorLabel: string) {
  const rows = results.map((item) => {
    if (item.status === 'error') {
      return [item.filename, errorLabel, '', '', '', item.error]
    }
    const top = item.top_predictions.slice(0, 3)
    return [
      item.filename,
      item.display_name,
      (item.confidence * 100).toFixed(2),
      ...[0, 1, 2].map((i) =>
        top[i]
          ? `${top[i].displayName} (${(top[i].probability * 100).toFixed(2)}%)`
          : '',
      ),
    ]
  })
  const csv = [header, ...rows]
    .map((row) => row.map((cell) => csvEscape(String(cell))).join(','))
    .join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'potato_batch_analysis.csv'
  link.click()
  URL.revokeObjectURL(url)
}

export function BatchPage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [files, setFiles] = useState<File[]>([])
  const [response, setResponse] = useState<BatchResponse | null>(null)
  const { t } = useTranslation()

  const mutation = useMutation({
    mutationFn: predictBatch,
    onSuccess: (data) => {
      setResponse(data)
      toast.success(
        t('batch.analyzed', {
          done: data.results.length - data.failed_count,
          total: data.results.length,
        }),
      )
    },
    onError: (error: Error) => toast.error(error.message),
  })

  function addFiles(selected: FileList | null) {
    if (!selected) return
    const accepted: File[] = []
    for (const file of selected) {
      const ext = file.name.split('.').pop()?.toLowerCase()
      if (!['jpg', 'jpeg', 'png'].includes(ext ?? '')) {
        toast.error(t('batch.unsupportedType', { name: file.name }))
        continue
      }
      if (file.size > MAX_FILE_MB * 1024 * 1024) {
        toast.error(t('batch.tooLarge', { name: file.name, mb: MAX_FILE_MB }))
        continue
      }
      accepted.push(file)
    }
    setFiles((current) => {
      const merged = [...current, ...accepted].slice(0, MAX_BATCH_FILES)
      if (current.length + accepted.length > MAX_BATCH_FILES) {
        toast.error(t('batch.tooMany', { max: MAX_BATCH_FILES }))
      }
      return merged
    })
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          {t('batch.title')}
        </h1>
        <p className="text-muted-foreground text-sm">
          {t('batch.subtitle', { max: MAX_BATCH_FILES })}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Layers className="text-primary size-4" /> {t('batch.selectImages')}
          </CardTitle>
          <CardDescription>
            {t('batch.selectHint', { mb: MAX_FILE_MB, max: MAX_BATCH_FILES })}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png"
            multiple
            className="hidden"
            onChange={(event) => addFiles(event.target.files)}
          />
          <Button
            variant="outline"
            onClick={() => inputRef.current?.click()}
            disabled={mutation.isPending}
          >
            {t('batch.chooseImages')}
          </Button>
          {files.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {files.map((file, index) => (
                <Badge
                  key={`${file.name}-${index}`}
                  variant="secondary"
                  className="gap-1 pr-1.5"
                >
                  {file.name}
                  <button
                    type="button"
                    aria-label={t('batch.remove', { name: file.name })}
                    className="hover:bg-foreground/10 rounded-full p-0.5"
                    disabled={mutation.isPending}
                    onClick={() =>
                      setFiles((current) =>
                        current.filter((_, i) => i !== index),
                      )
                    }
                  >
                    <X className="size-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
          <Button
            size="lg"
            disabled={files.length === 0 || mutation.isPending}
            onClick={() => mutation.mutate(files)}
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="size-4 animate-spin" />{' '}
                {t('batch.analyzing', { count: files.length })}
              </>
            ) : (
              <>
                <ScanSearch className="size-4" />{' '}
                {t('batch.analyze', { count: files.length })}
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {response && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t('batch.results')}</CardTitle>
            <div className="flex flex-wrap gap-2">
              <Badge className={PREDICTION_STYLES.Healthy}>
                {t('batch.healthyCount', { count: response.healthy_count })}
              </Badge>
              <Badge className={PREDICTION_STYLES.Bacteria}>
                {t('batch.diseaseCount', { count: response.disease_count })}
              </Badge>
              {response.failed_count > 0 && (
                <Badge variant="destructive">
                  {t('batch.failedCount', { count: response.failed_count })}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('batch.tableImage')}</TableHead>
                  <TableHead>{t('batch.tablePrediction')}</TableHead>
                  <TableHead>{t('batch.tableConfidence')}</TableHead>
                  <TableHead>{t('batch.tableTop3')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {response.results.map((item, index) => (
                  <TableRow key={`${item.filename}-${index}`}>
                    <TableCell className="max-w-40 truncate font-medium">
                      {item.filename}
                    </TableCell>
                    {item.status === 'ok' ? (
                      <>
                        <TableCell>
                          <Badge
                            className={cn(
                              PREDICTION_STYLES[item.predicted_class] ?? '',
                            )}
                          >
                            {item.display_name}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {(item.confidence * 100).toFixed(2)}%
                        </TableCell>
                        <TableCell className="text-muted-foreground text-xs">
                          {item.top_predictions
                            .slice(0, 3)
                            .map(
                              (p) =>
                                `${p.displayName} ${(p.probability * 100).toFixed(1)}%`,
                            )
                            .join(' · ')}
                        </TableCell>
                      </>
                    ) : (
                      <TableCell
                        colSpan={3}
                        className="text-destructive text-xs"
                      >
                        {item.error}
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Button
              variant="outline"
              className="w-fit"
              onClick={() =>
                downloadCsv(
                  response.results,
                  [
                    t('batch.csvImage'),
                    t('batch.csvPrediction'),
                    t('batch.csvConfidence'),
                    t('batch.csvTop1'),
                    t('batch.csvTop2'),
                    t('batch.csvTop3'),
                  ],
                  t('batch.errorLabel'),
                )
              }
            >
              <Download className="size-4" /> {t('batch.downloadCsv')}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
