import { onBeforeUnmount, ref } from 'vue'

/** A ticking timestamp for live durations. */
export function useNow(intervalMs = 100) {
  const now = ref(Date.now())
  const id = window.setInterval(() => (now.value = Date.now()), intervalMs)
  onBeforeUnmount(() => window.clearInterval(id))
  return now
}
