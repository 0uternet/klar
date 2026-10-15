<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, useId, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Menu, X } from '@lucide/vue'
import { locale, t } from '@/i18n'
import { leaveMock } from '@/api'
import { demo, health, unreachable } from '@/stores/app'
import KlarLogo from './KlarLogo.vue'
import SovereigntyBadge from './SovereigntyBadge.vue'
import LangSwitcher from './LangSwitcher.vue'
import ThemeToggle from './ThemeToggle.vue'
import ShapeIcon from './ShapeIcon.vue'

const links = [
  { to: { name: 'home' }, key: 'nav.check' },
  { to: { name: 'human' }, key: 'nav.human' },
  { to: { name: 'about' }, key: 'nav.about' },
] as const

const route = useRoute()
const root = ref<HTMLElement | null>(null)
const navEl = ref<HTMLElement | null>(null)
const menuButton = ref<HTMLButtonElement | null>(null)

/* ---- Mobile menu sheet ---------------------------------------------------- */

const menuOpen = ref(false)
const sheetId = useId()

function closeMenu(returnFocus = false) {
  if (!menuOpen.value) return
  menuOpen.value = false
  if (returnFocus) menuButton.value?.focus({ preventScroll: true })
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape' && menuOpen.value) {
    e.preventDefault()
    closeMenu(true)
  }
}
watch(menuOpen, (o) => (o ? document.addEventListener('keydown', onKey) : document.removeEventListener('keydown', onKey)))
watch(() => route.fullPath, () => closeMenu())
/** Tabbing out of the sheet (to the page behind the scrim) closes it. */
function onSheetFocusOut(e: FocusEvent) {
  const next = e.relatedTarget as Node | null
  if (next && next !== menuButton.value && !(e.currentTarget as HTMLElement).contains(next)) closeMenu()
}

/* ---- Glass + hairline once the page scrolls under the bar ----------------- */

const scrolled = ref(false)
let raf = 0
function onScroll() {
  if (raf) return
  raf = requestAnimationFrame(() => {
    raf = 0
    scrolled.value = window.scrollY > 4
  })
}

/* ---- Active-page underline that slides between items ---------------------- */

const ink = reactive({ x: 0, w: 0, show: false, slide: false })
function placeInk() {
  const a = navEl.value?.querySelector<HTMLElement>('a[aria-current="page"]')
  if (!a) {
    ink.show = false
    ink.slide = false
    return
  }
  const pad = parseFloat(getComputedStyle(a).paddingLeft) || 0
  // Slide only from one item to another; appear in place otherwise.
  ink.slide = ink.show
  ink.x = a.offsetLeft + pad
  ink.w = Math.max(0, a.offsetWidth - 2 * pad)
  ink.show = true
}
watch([() => route.name, locale], () => nextTick(placeInk), { flush: 'post' })

/* ---- Measured header height: sticky offsets elsewhere use --header-h ------ */

let ro: ResizeObserver | null = null
let wide: MediaQueryList | null = null
const onWide = (e: MediaQueryListEvent) => e.matches && closeMenu()

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
  ro = new ResizeObserver((entries) => {
    for (const e of entries) {
      if (e.target === root.value) {
        document.documentElement.style.setProperty('--header-h', `${Math.round(e.target.getBoundingClientRect().height)}px`)
      } else {
        ink.slide = false
        placeInk()
      }
    }
  })
  if (root.value) ro.observe(root.value)
  if (navEl.value) ro.observe(navEl.value)
  void document.fonts?.ready.then(() => placeInk())
  placeInk()
  wide = window.matchMedia('(min-width: 1024px)')
  wide.addEventListener('change', onWide)
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  document.removeEventListener('keydown', onKey)
  cancelAnimationFrame(raf)
  ro?.disconnect()
  wide?.removeEventListener('change', onWide)
  document.documentElement.style.removeProperty('--header-h')
})
</script>

<template>
  <header ref="root" class="hdr" :data-scrolled="scrolled || menuOpen ? 'true' : undefined" :data-menu="menuOpen ? 'true' : undefined">
    <div class="container hdr__inner">
      <RouterLink :to="{ name: 'home' }" class="hdr__logo" :aria-label="t('app.homeLink')">
        <KlarLogo :size="24" />
      </RouterLink>

      <nav ref="navEl" class="hdr__nav" :aria-label="t('nav.label')">
        <RouterLink v-for="l in links" :key="l.key" :to="l.to" class="hdr__link">{{ t(l.key) }}</RouterLink>
        <span
          class="hdr__ink"
          :class="{ 'hdr__ink--slide': ink.slide }"
          :style="{ transform: `translateX(${ink.x}px) scaleX(${ink.w})`, opacity: ink.show ? 1 : 0 }"
          aria-hidden="true"
        />
      </nav>

      <div class="hdr__right">
        <SovereigntyBadge :health="health" :unreachable="unreachable" />
        <div class="hdr__tools">
          <LangSwitcher />
          <ThemeToggle />
        </div>
        <button
          ref="menuButton"
          type="button"
          class="btn btn--ghost btn--icon hdr__menu"
          :aria-expanded="menuOpen"
          :aria-controls="sheetId"
          :aria-label="menuOpen ? t('nav.closeMenu') : t('nav.menu')"
          @click="menuOpen = !menuOpen"
        >
          <span class="hdr__burger" :class="{ 'hdr__burger--x': menuOpen }" aria-hidden="true">
            <Menu class="hdr__burger-a" :size="20" />
            <X class="hdr__burger-b" :size="20" />
          </span>
        </button>
      </div>
    </div>

    <!-- Mobile menu: drops down from the bar; the scrim closes it. -->
    <Transition name="fade">
      <div v-if="menuOpen" class="hdr__scrim" aria-hidden="true" @click="closeMenu()" />
    </Transition>
    <Transition name="sheet">
      <div v-show="menuOpen" :id="sheetId" class="hdr__sheet" @focusout="onSheetFocusOut">
        <nav class="container hdr__sheet-nav" :aria-label="t('nav.label')">
          <RouterLink v-for="(l, i) in links" :key="l.key" :to="l.to" class="hdr__sheet-link m-rise" :style="{ '--i': i }">{{ t(l.key) }}</RouterLink>
        </nav>
        <div class="container hdr__sheet-tools m-rise" :style="{ '--i': links.length }">
          <LangSwitcher />
          <ThemeToggle />
        </div>
      </div>
    </Transition>

    <!-- On every page while mock-up data is shown (never in production builds). -->
    <div v-if="demo" class="mock-bar" role="note">
      <div class="container mock-bar__inner">
        <ShapeIcon shape="diamond" color="var(--amber)" :size="9" />
        <span class="mock-bar__title">{{ t('mock.banner') }}</span>
        <button type="button" class="mock-bar__leave" @click="leaveMock">{{ t('mock.leave') }}</button>
      </div>
    </div>
  </header>
</template>

<style scoped>
/*
 * The glass lives on ::before, not on the header: a backdrop-filter on the header itself
 * would trap the fixed scrim and panels inside it.
 */
.hdr {
  position: sticky;
  top: 0;
  z-index: 50;
  isolation: isolate;
}
.hdr::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: -1;
  background: var(--bg);
  border-bottom: 1px solid transparent;
  -webkit-backdrop-filter: saturate(1.6) blur(14px);
  backdrop-filter: saturate(1.6) blur(14px);
  transition: background-color var(--dur-3) var(--ease-out), border-color var(--dur-3) var(--ease-out);
}
.hdr[data-scrolled='true']::before {
  background: var(--hdr-glass);
  border-bottom-color: var(--line);
}
.hdr[data-menu='true']::before {
  background: var(--bg);
}
/*
 * The page's scroll-padding (room for this header) would make the browser "scroll into view"
 * every control of the sticky header when it takes focus, jumping the page. A negative
 * margin of the same size cancels that: focusing the header never scrolls.
 */
.hdr :deep(:is(a, button)) {
  scroll-margin-top: calc(-1 * (var(--header-h) + 16px));
}
.hdr__inner {
  display: flex;
  align-items: center;
  gap: var(--s-6);
  height: var(--bar-h);
}
.hdr__logo {
  display: inline-flex;
  align-items: center;
  height: 40px;
  padding: 0 4px;
  margin-left: -4px;
  border-radius: var(--r-sm);
  text-decoration: none;
}

/* Nav: quiet items, one red underline that slides to the active page. */
.hdr__nav {
  position: relative;
  display: flex;
  align-items: center;
  align-self: stretch;
  gap: 2px;
}
.hdr__link {
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 var(--s-3);
  border-radius: var(--r-sm);
  color: var(--muted);
  font-size: var(--fs-14);
  font-weight: 550;
  letter-spacing: var(--tr-ui);
  text-decoration: none;
  white-space: nowrap;
  transition: color var(--dur-1) var(--ease-out), background-color var(--dur-1) var(--ease-out);
}
.hdr__link:hover {
  color: var(--ink);
  background: var(--surface-2);
}
.hdr__link[aria-current='page'] {
  color: var(--ink);
  font-weight: 600;
}
.hdr__ink {
  position: absolute;
  left: 0;
  bottom: -1px;
  width: 1px;
  height: 2px;
  background: var(--klar-red);
  transform-origin: 0 0;
  pointer-events: none;
  transition: opacity var(--dur-2) var(--ease-out);
}
.hdr__ink--slide {
  transition: opacity var(--dur-2) var(--ease-out), transform var(--dur-3) var(--ease-out);
}

.hdr__right {
  display: flex;
  align-items: center;
  gap: var(--s-2);
  margin-left: auto;
  min-width: 0;
}
.hdr__tools {
  display: flex;
  align-items: center;
  gap: var(--s-1);
  padding-left: var(--s-2);
}
.hdr__menu {
  --btn-h: 40px;
  display: none;
}
/* Menu ⇄ close: the two glyphs cross-fade with a quarter turn. */
.hdr__burger {
  display: grid;
}
.hdr__burger > * {
  grid-area: 1 / 1;
  transition: opacity var(--dur-2) var(--ease-out), transform var(--dur-3) var(--ease-out);
}
.hdr__burger-b,
.hdr__burger--x .hdr__burger-a {
  opacity: 0;
  transform: rotate(-90deg) scale(0.7);
}
.hdr__burger--x .hdr__burger-b {
  opacity: 1;
  transform: none;
}

/* ---- Mobile sheet ---- */
.hdr__scrim {
  position: fixed;
  inset: 0;
  z-index: -2;
  background: var(--scrim);
}
.hdr__sheet {
  position: absolute;
  top: var(--bar-h);
  left: 0;
  right: 0;
  background: var(--bg);
  border-bottom: 1px solid var(--line);
  box-shadow: var(--shadow-overlay);
  padding-bottom: var(--s-5);
  max-height: calc(100dvh - var(--bar-h));
  overflow-y: auto;
}
.hdr__sheet-nav {
  display: flex;
  flex-direction: column;
  padding-top: var(--s-2);
}
.hdr__sheet-link {
  display: flex;
  align-items: center;
  min-height: 56px;
  border-bottom: 1px solid var(--line);
  color: var(--ink);
  font-size: var(--fs-24);
  font-weight: 650;
  letter-spacing: var(--tr-h2);
  text-decoration: none;
}
.hdr__sheet-link[aria-current='page']::after {
  content: '';
  width: 7px;
  height: 7px;
  margin-left: var(--s-3);
  background: var(--klar-red);
}
.hdr__sheet-tools {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: var(--s-5);
}
.sheet-enter-active {
  transition: opacity var(--dur-3) var(--ease-out), transform var(--dur-3) var(--ease-out);
}
.sheet-leave-active {
  transition: opacity var(--dur-1) var(--ease-in-out), transform var(--dur-1) var(--ease-in-out);
}
.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ---- Mock-up banner ---- */
.mock-bar {
  background: var(--amber-tint);
  border-top: 1px solid color-mix(in srgb, var(--amber) 22%, transparent);
  color: var(--ink);
}
.mock-bar__inner {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: calc(var(--mock-h) - 1px);
  padding-block: 4px;
  font-size: var(--fs-13);
}
.mock-bar__title {
  font-weight: 600;
  min-width: 0;
}
.mock-bar__leave {
  margin-left: auto;
  flex: none;
  min-height: 28px;
  padding: 0 10px;
  border: 0;
  border-radius: var(--r-sm);
  background: transparent;
  color: var(--ink);
  font-size: var(--fs-13);
  font-weight: 600;
  text-decoration: underline;
  text-decoration-color: color-mix(in srgb, currentColor 45%, transparent);
  text-underline-offset: 0.2em;
  transition: background-color var(--dur-1) var(--ease-out);
}
.mock-bar__leave:hover {
  background: color-mix(in srgb, var(--amber) 14%, transparent);
  text-decoration-color: currentColor;
}

@media (max-width: 1023px) {
  .hdr__nav,
  .hdr__tools {
    display: none;
  }
  .hdr__menu {
    display: inline-flex;
  }
}
@media (min-width: 1024px) {
  .hdr__sheet,
  .hdr__scrim {
    display: none !important;
  }
}
@media (max-width: 520px) {
  .hdr__inner {
    gap: var(--s-3);
  }
  .mock-bar__leave {
    margin-right: -10px;
  }
}
@media (forced-colors: active) {
  .hdr::before {
    border-bottom-color: CanvasText;
  }
  .hdr__ink {
    background: Highlight;
  }
  .hdr__link[aria-current='page'] {
    text-decoration: underline;
  }
}
</style>
