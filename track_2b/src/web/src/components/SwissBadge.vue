<script setup lang="ts">
/**
 * The Swiss badge: Klar.'s red square + "Swiss AI · Apertus", and where the model runs.
 * Computed from GET /api/health, never hard-coded, and honest by construction:
 *  - the Swiss claim needs an Apertus model AND a sovereign mode (local, Swiss cloud, replay);
 *  - an external endpoint, or another model, gets a neutral line with no Swiss claim.
 * No Swiss cross, flag or coat of arms (Coat of Arms Protection Act): only Klar.'s own square.
 */
import { computed } from 'vue'
import type { Health } from '@/types'
import { t } from '@/i18n'
import { MODE_COLOR, MODE_SHAPE, isApertus, prettyModel, providerName } from '@/lib/format'
import ShapeIcon from './ShapeIcon.vue'

const props = defineProps<{ health: Health | null }>()

const mode = computed(() => props.health?.mode ?? null)

/** Apertus answers this instance: the configured model, or (replay) every recorded model. */
const apertus = computed(() => {
  const h = props.health
  if (!h) return false
  if (h.mode === 'replay' && h.replay_models?.length) return h.replay_models.every(isApertus)
  return isApertus(h.model)
})

const swiss = computed(() => apertus.value && (mode.value === 'local' || mode.value === 'swiss_cloud' || mode.value === 'replay'))

const name = computed(() => {
  if (swiss.value) return t('swiss.badge.name')
  if (mode.value === 'replay') return t('sov.replay')
  return prettyModel(props.health?.model)
})

const sub = computed(() => {
  const h = props.health
  switch (mode.value) {
    case 'local':
      return t('swiss.badge.local')
    case 'swiss_cloud':
      return t('swiss.badge.swiss_cloud', { provider: providerName(h?.provider, h?.base_url_host) })
    case 'replay':
      return t('swiss.badge.replay')
    case 'external':
      return t('swiss.badge.external')
    default:
      return ''
  }
})
</script>

<template>
  <p v-if="mode" :key="`${mode}-${swiss}`" class="swiss" :class="{ 'is-swiss': swiss, [`swiss--${mode}`]: true }">
    <span v-if="swiss" class="swiss__mark" aria-hidden="true" />
    <ShapeIcon v-else class="swiss__shape" :shape="MODE_SHAPE[mode]" :color="MODE_COLOR[mode]" :size="9" />
    <span class="swiss__name" :translate="swiss ? undefined : 'no'">{{ name }}</span><span class="sr-only">, </span>
    <span class="swiss__sep" aria-hidden="true" />
    <span class="swiss__sub">{{ sub }}</span>
  </p>
</template>

<style scoped>
/* A flat label, not a button: square corners and no border, so it never reads as the demo pill. */
.swiss {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  column-gap: 10px;
  row-gap: 2px;
  max-width: 100%;
  min-height: 28px;
  padding: 4px 12px 4px 10px;
  background: var(--surface-2);
  border: 1px solid transparent;
  border-radius: var(--r-sm);
  font-size: var(--fs-13);
  line-height: 1.35;
  letter-spacing: var(--tr-ui);
}

/* Klar.'s red square (as in the wordmark): stamped in once, with a short settle. */
.swiss__mark {
  flex: none;
  width: 9px;
  height: 9px;
  background: var(--klar-red);
  animation: swiss-stamp var(--dur-4) var(--ease-spring) both;
  animation-delay: calc(var(--i, 0) * var(--stagger) + var(--dur-3));
}
.swiss__shape {
  flex: none;
}
.swiss__name {
  font-weight: 650;
  color: var(--ink);
  white-space: nowrap;
}
.swiss__sep {
  flex: none;
  width: 1px;
  height: 12px;
  background: var(--line-strong);
}
.swiss__sub {
  color: var(--muted);
  font-weight: 500;
}

@keyframes swiss-stamp {
  from {
    opacity: 0;
    transform: scale(0.2) rotate(-45deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .swiss__mark {
    animation: none;
  }
}
@media (forced-colors: active) {
  .swiss {
    border-color: CanvasText;
  }
  .swiss__mark,
  .swiss__sep {
    background: CanvasText;
  }
}
</style>
