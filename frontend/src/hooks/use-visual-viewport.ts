import { useEffect } from 'react'

export function useVisualViewport() {
  useEffect(() => {
    const viewport = window.visualViewport
    if (!viewport) return

    const root = document.documentElement

    const update = () => {
      const keyboardOpen = viewport.height < window.innerHeight - 1
      if (keyboardOpen) {
        root.style.setProperty('--app-height', `${viewport.height}px`)
      } else {
        root.style.removeProperty('--app-height')
      }
    }

    update()
    viewport.addEventListener('resize', update)
    viewport.addEventListener('scroll', update)
    return () => {
      viewport.removeEventListener('resize', update)
      viewport.removeEventListener('scroll', update)
      root.style.removeProperty('--app-height')
    }
  }, [])
}
