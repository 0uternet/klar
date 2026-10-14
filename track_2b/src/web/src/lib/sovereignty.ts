/**
 * "AI requests that left this network" (SOV-1/2). Requests to a local endpoint never
 * leave; Swiss cloud and external ones do. If the server did not report a destination,
 * the number is unknown and the UI says so; it is never shown as 0.
 */
import type { AiRequests, Mode } from '@/types'
import { formatNumber, t } from '@/i18n'

export function leftNetwork(ai: AiRequests | null | undefined): number | null {
  if (!ai || ai.swiss_cloud == null || ai.external == null) return null
  return ai.swiss_cloud + ai.external
}

/** The counter sentence, and whether it rests on a number the server actually reported. */
export function aiCounterText(mode: Mode | null, ai: AiRequests | null | undefined, provider: string): { text: string; measured: boolean } {
  const n = leftNetwork(ai)
  const shown = n === null ? t('common.unknown') : formatNumber(n)
  const key = mode === 'swiss_cloud' ? 'sov.counter.swiss' : mode === 'external' ? 'sov.counter.external' : 'sov.counter'
  return { text: t(key, { n: shown, provider }), measured: n !== null }
}

/** Short form for tables: the number, or "unknown". */
export function leftNetworkLabel(ai: AiRequests | null | undefined): string {
  const n = leftNetwork(ai)
  return n === null ? t('common.unknown') : formatNumber(n)
}
