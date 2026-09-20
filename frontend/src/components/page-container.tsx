import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function PageContainer({
  children,
  className,
  contentClassName,
}: {
  children: ReactNode
  className?: string
  contentClassName?: string
}) {
  return (
    <div className={cn('flex min-h-0 flex-1 flex-col', className)}>
      <div
        className={cn(
          'min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 py-1 sm:px-4 [&>*]:shrink-0',
          contentClassName,
        )}
      >
        {children}
      </div>
    </div>
  )
}
