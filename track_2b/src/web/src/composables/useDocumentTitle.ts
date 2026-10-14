import { watchEffect } from 'vue'

/** Reactive document title: "<page> – Klar." (WCAG 2.4.2 for Klar. itself). */
export function useDocumentTitle(get: () => string, standalone = false): void {
  watchEffect(() => {
    const t = get()
    document.title = standalone ? t : `${t} – Klar.`
  })
}
