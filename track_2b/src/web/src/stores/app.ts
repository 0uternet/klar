import { computed, ref, watch } from 'vue'
import { STORAGE } from '@/config'
import type { Health } from '@/types'
import { api, boot, type DemoReason } from '@/api'

/* ---- Server health / sovereignty ---------------------------------------- */

export const health = ref<Health | null>(null)
/** 'forced' = explicit `?mock=1` mock-up mode (dev/demo builds only). */
export const demo = ref<DemoReason>(null)
/** The Klar. server did not answer GET /api/health. No sample data is shown instead. */
export const unreachable = ref(false)
export const booted = ref(false)

let booting: Promise<void> | null = null

export function ensureBooted(): Promise<void> {
  booting ??= boot().then(({ health: h, demo: d, unreachable: u }) => {
    health.value = h
    demo.value = d
    unreachable.value = u
    booted.value = true
    document.documentElement.classList.toggle('is-mock', d !== null)
  })
  return booting
}

/**
 * M1: while the server is unreachable, try again every 5 s for 60 s
 * (it may still be starting). `healthRetrying` drives the "Retrying…" line.
 */
export const healthRetrying = ref(false)
let retryTimer: number | undefined
watch(unreachable, (down) => {
  window.clearTimeout(retryTimer)
  healthRetrying.value = false
  if (!down) return
  let tries = 0
  healthRetrying.value = true
  const tick = async () => {
    tries++
    const ok = await refreshHealth()
    if (ok) return
    if (tries >= 12) healthRetrying.value = false
    else retryTimer = window.setTimeout(tick, 5000)
  }
  retryTimer = window.setTimeout(tick, 5000)
})

export async function refreshHealth(): Promise<boolean> {
  try {
    health.value = await api().health()
    unreachable.value = false
    return true
  } catch {
    if (!demo.value) unreachable.value = true
    return false
  }
}

/* ---- Theme -------------------------------------------------------------- */

export type ThemePref = 'system' | 'light' | 'dark'

function readTheme(): ThemePref {
  try {
    const v = localStorage.getItem(STORAGE.theme)
    return v === 'light' || v === 'dark' ? v : 'system'
  } catch {
    return 'system'
  }
}

export const theme = ref<ThemePref>(readTheme())

watch(
  theme,
  (t) => {
    const root = document.documentElement
    if (t === 'system') root.removeAttribute('data-theme')
    else root.setAttribute('data-theme', t)
    try {
      if (t === 'system') localStorage.removeItem(STORAGE.theme)
      else localStorage.setItem(STORAGE.theme, t)
    } catch {
      /* storage unavailable */
    }
  },
  { immediate: true },
)

export function cycleTheme(): void {
  theme.value = theme.value === 'system' ? 'light' : theme.value === 'light' ? 'dark' : 'system'
}

/* ---- Single-key shortcuts (WCAG 2.1.4: can be turned off) ---------------- */

function readShortcuts(): boolean {
  try {
    return localStorage.getItem(STORAGE.shortcuts) !== 'off'
  } catch {
    return true
  }
}

export const shortcutsEnabled = ref(readShortcuts())
watch(shortcutsEnabled, (on) => {
  try {
    if (on) localStorage.removeItem(STORAGE.shortcuts)
    else localStorage.setItem(STORAGE.shortcuts, 'off')
  } catch {
    /* storage unavailable */
  }
})

export const shortcutsDialogOpen = ref(false)

/* ---- Last scan (for "What a human must still check") ---------------------- */

export const lastScanId = ref<string | null>(null)

/* ---- Hand-over to the start page ("Edit the address", "Paste HTML instead") ---- */

export const prefill = ref<{ url?: string; mode?: 'html' } | null>(null)

/* ---- Modal finding panel (UX-14): header and footer become inert while it is open ---- */

export const modalOpen = ref(false)

export const isDemo = computed(() => demo.value !== null)
