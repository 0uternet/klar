import { ref } from 'vue'

export type ToastTone = 'neutral' | 'success' | 'danger' | 'info'

export interface Toast {
  id: number
  message: string
  tone: ToastTone
  tag?: string
  /** One button in the toast (E4: "Retry"). */
  action?: { label: string; run: () => void }
}

export const toasts = ref<Toast[]>([])
let seq = 0

/** `tag`: a new toast replaces an older one with the same tag (e.g. rapid review decisions). */
export function toast(message: string, tone: ToastTone = 'neutral', ms = 3800, tag?: string, action?: Toast['action']): void {
  const id = ++seq
  const kept = tag ? toasts.value.filter((x) => x.tag !== tag) : toasts.value
  // Keep at most three on screen. A toast with an action stays longer (WCAG 2.2.1).
  toasts.value = [...kept.slice(-2), { id, message, tone, tag, action }]
  if (action) ms = Math.max(ms, 10000)
  window.setTimeout(() => dismissToast(id), ms)
}

export function dismissToast(id: number): void {
  toasts.value = toasts.value.filter((t) => t.id !== id)
}
