/**
 * Time left in a running step, from its own pace so far: the server's duration
 * for `current` of `total` items, counted down since that event arrived. Null
 * when the step has no total yet or nothing is done (no pace to go by).
 */
import type { ProgressStep } from '@/types'

export function stepEta(s: ProgressStep, now: number, receivedAt: number | undefined, paused: boolean): number | null {
  if (s.state !== 'running' || typeof s.current !== 'number' || typeof s.total !== 'number') return null
  if (s.total <= 0 || s.current <= 0 || s.current >= s.total || !s.duration_ms || s.duration_ms <= 0) return null
  const perItem = s.duration_ms / s.current
  const since = paused || receivedAt == null ? 0 : Math.max(0, now - receivedAt)
  return Math.max(1, (perItem * (s.total - s.current) - since) / 1000)
}

/** "40 s", "3 min" (rounded up, so the estimate never promises less than it means). */
export function etaText(seconds: number): string {
  return seconds < 90 ? `${Math.ceil(seconds)} s` : `${Math.ceil(seconds / 60)} min`
}
