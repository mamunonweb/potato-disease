import { useTranslation } from 'react-i18next'
import { Languages } from 'lucide-react'

import { Button } from '@/components/ui/button'

export function LanguageToggle() {
  const { i18n, t } = useTranslation()
  const current = i18n.resolvedLanguage ?? i18n.language
  const nextLanguage = current === 'bn' ? 'en' : 'bn'

  return (
    <Button
      variant="ghost"
      size="sm"
      className="gap-1.5 px-2"
      aria-label={`${t('common.language')}: ${
        nextLanguage === 'bn' ? t('common.bengali') : t('common.english')
      }`}
      onClick={() => void i18n.changeLanguage(nextLanguage)}
    >
      <Languages className="size-4" />
      <span className="text-xs font-medium">
        {current === 'bn' ? 'বাংলা' : 'EN'}
      </span>
    </Button>
  )
}
