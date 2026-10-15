/**
 * Motion helpers (see styles/motion.css). Every helper honours prefers-reduced-motion:
 * with it, content is shown at once and numbers show their final value.
 */
import { onBeforeUnmount, ref, watch, type Directive, type Ref } from 'vue'

export function reducedMotion(): boolean {
  return typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

let io: IntersectionObserver | null = null

function observer(): IntersectionObserver {
  io ??= new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue
        ;(e.target as HTMLElement).dataset.reveal = 'in'
        io?.unobserve(e.target)
      }
    },
    { rootMargin: '0px 0px -8% 0px', threshold: 0.12 },
  )
  return io
}

/**
 * v-reveal: fade and rise into view once, when scrolled into the viewport.
 * `v-reveal="i"` staggers siblings (i × --stagger). Elements already on screen animate at once.
 */
export const vReveal: Directive<HTMLElement, number | undefined> = {
  mounted(el, binding) {
    if (typeof binding.value === 'number') el.style.setProperty('--i', String(binding.value))
    if (reducedMotion() || typeof IntersectionObserver === 'undefined') return
    el.dataset.reveal = 'out'
    if (el.getBoundingClientRect().top < window.innerHeight * 0.92) {
      requestAnimationFrame(() => requestAnimationFrame(() => (el.dataset.reveal = 'in')))
    } else {
      observer().observe(el)
    }
  },
  unmounted(el) {
    io?.unobserve(el)
  },
}

/**
 * A number that counts up to its target (ease-out quart). Render the animated value with
 * aria-hidden="true" next to the final value in .sr-only (or use <CountUp>), so screen readers
 * hear one number, not a stream.
 */
export function useCountUp(target: Ref<number> | (() => number), duration = 900): Ref<number> {
  const shown = ref(0)
  const read = typeof target === 'function' ? target : () => target.value
  let raf = 0
  function run(to: number, from: number) {
    cancelAnimationFrame(raf)
    if (reducedMotion() || duration <= 0 || !Number.isFinite(to)) {
      shown.value = to
      return
    }
    const t0 = performance.now()
    const step = (now: number) => {
      const p = Math.min(1, (now - t0) / duration)
      shown.value = from + (to - from) * (1 - Math.pow(1 - p, 4))
      if (p < 1) raf = requestAnimationFrame(step)
      else shown.value = to
    }
    raf = requestAnimationFrame(step)
  }
  watch(read, (to, from) => run(to ?? 0, from ?? 0), { immediate: true })
  onBeforeUnmount(() => cancelAnimationFrame(raf))
  return shown
}

declare module 'vue' {
  interface GlobalDirectives {
    vReveal: typeof vReveal
  }
}
