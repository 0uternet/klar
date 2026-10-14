import { onBeforeUnmount, onMounted } from 'vue'
import { shortcutsEnabled } from '@/stores/app'

type Handler = (e: KeyboardEvent) => void

function isTyping(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null
  if (!el || !el.tagName) return false
  const tag = el.tagName
  if (tag === 'TEXTAREA' || tag === 'SELECT') return true
  if (tag === 'INPUT') {
    const type = (el as HTMLInputElement).type
    return !['checkbox', 'radio', 'button', 'submit', 'reset'].includes(type)
  }
  return el.isContentEditable
}

/**
 * Single-key shortcuts (WCAG 2.1.4): ignored while typing, with modifier keys,
 * inside open dialogs, or when the user turned them off.
 * `Escape` handlers always run (Escape is not a character key).
 */
export function useShortcuts(map: Record<string, Handler>): void {
  const onKey = (e: KeyboardEvent) => {
    if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.altKey) return
    const key = e.key
    if (key !== 'Escape') {
      if (!shortcutsEnabled.value) return
      if (isTyping(e.target)) return
      if (document.querySelector('dialog[open]')) return
    }
    const h = map[key] ?? map[key.toLowerCase()]
    if (h) h(e)
  }
  onMounted(() => window.addEventListener('keydown', onKey))
  onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
}
