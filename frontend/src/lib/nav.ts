import type { ComponentType } from 'react'
import {
  BarChart3,
  BookOpen,
  Layers,
  MessageCircle,
  ScanSearch,
} from 'lucide-react'

export interface NavItem {
  to: string
  labelKey: string
  icon: ComponentType<{ className?: string }>
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/', labelKey: 'nav.detect', icon: ScanSearch },
  { to: '/results', labelKey: 'nav.results', icon: BarChart3 },
  { to: '/batch', labelKey: 'nav.batch', icon: Layers },
  { to: '/chat', labelKey: 'nav.chat', icon: MessageCircle },
  { to: '/info', labelKey: 'nav.info', icon: BookOpen },
]
