import i18n from 'i18next'
import type { Resource } from 'i18next'
import { initReactI18next } from 'react-i18next'

import { resources, supportedLanguages } from './resources'
import type { SupportedLanguage } from './resources'

const STORAGE_KEY = 'potato-language'

function readStoredLanguage(): SupportedLanguage {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && (supportedLanguages as readonly string[]).includes(stored)) {
      return stored as SupportedLanguage
    }
  } catch {
    /* localStorage may be unavailable */
  }
  return 'en'
}

export function currentLanguage(): SupportedLanguage {
  const language = i18n.resolvedLanguage ?? i18n.language
  return (supportedLanguages as readonly string[]).includes(language)
    ? (language as SupportedLanguage)
    : 'en'
}

function syncDocumentLang(language: string) {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = language
  }
}

const initialLanguage = readStoredLanguage()

i18n.use(initReactI18next).init({
  resources: resources as unknown as Resource,
  lng: initialLanguage,
  fallbackLng: 'en',
  supportedLngs: [...supportedLanguages],
  interpolation: { escapeValue: false },
})

syncDocumentLang(initialLanguage)

i18n.on('languageChanged', (language) => {
  try {
    localStorage.setItem(STORAGE_KEY, language)
  } catch {
    /* ignore */
  }
  syncDocumentLang(language)
})

export default i18n
