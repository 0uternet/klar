<script setup lang="ts">
import { ref, useId, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Menu, X } from '@lucide/vue'
import { t } from '@/i18n'
import { leaveMock } from '@/api'
import { demo, health, unreachable } from '@/stores/app'
import KlarLogo from './KlarLogo.vue'
import SovereigntyBadge from './SovereigntyBadge.vue'
import LangSwitcher from './LangSwitcher.vue'
import ThemeToggle from './ThemeToggle.vue'
import ShapeIcon from './ShapeIcon.vue'

const menuOpen = ref(false)
const sheetId = useId()
const route = useRoute()
watch(() => route.fullPath, () => (menuOpen.value = false))

const links = [
  { to: { name: 'home' }, key: 'nav.check' },
  { to: { name: 'human' }, key: 'nav.human' },
  { to: { name: 'about' }, key: 'nav.about' },
] as const
</script>

<template>
  <header class="hdr">
    <div class="container hdr__inner">
      <RouterLink :to="{ name: 'home' }" class="hdr__logo" :aria-label="t('app.homeLink')">
        <KlarLogo :size="26" />
      </RouterLink>

      <nav class="hdr__nav" :aria-label="t('nav.label')">
        <RouterLink v-for="l in links" :key="l.key" :to="l.to" class="hdr__link">{{ t(l.key) }}</RouterLink>
      </nav>

      <div class="hdr__right">
        <SovereigntyBadge :health="health" :unreachable="unreachable" />
        <div class="hdr__tools">
          <LangSwitcher />
          <ThemeToggle />
        </div>
        <button
          type="button"
          class="btn btn--ghost btn--icon hdr__menu"
          :aria-expanded="menuOpen"
          :aria-controls="sheetId"
          :aria-label="menuOpen ? t('nav.closeMenu') : t('nav.menu')"
          @click="menuOpen = !menuOpen"
        >
          <component :is="menuOpen ? X : Menu" :size="20" aria-hidden="true" />
        </button>
      </div>
    </div>

    <!-- Persistent on every page while mock-up data is shown (never in production builds). -->
    <div v-if="demo" class="mock-bar" role="note">
      <div class="container mock-bar__inner">
        <ShapeIcon shape="diamond" color="var(--amber)" :size="10" />
        <strong class="mock-bar__title">{{ t('mock.banner') }}</strong>
        <span class="mock-bar__body">{{ t('mock.bannerBody') }}</span>
        <button type="button" class="mock-bar__leave" @click="leaveMock">{{ t('mock.leave') }}</button>
      </div>
    </div>

    <div v-show="menuOpen" :id="sheetId" class="hdr__sheet">
      <nav class="container hdr__sheet-nav" :aria-label="t('nav.label')">
        <RouterLink v-for="l in links" :key="l.key" :to="l.to" class="hdr__sheet-link">{{ t(l.key) }}</RouterLink>
      </nav>
      <div class="container hdr__sheet-tools">
        <LangSwitcher />
        <ThemeToggle />
      </div>
    </div>
  </header>
</template>

<style scoped>
.hdr {
  position: sticky;
  top: 0;
  z-index: 50;
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: saturate(1.4) blur(10px);
  -webkit-backdrop-filter: saturate(1.4) blur(10px);
  border-bottom: 1px solid var(--line);
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
  height: 44px;
  padding: 0 4px;
  margin-left: -4px;
  border-radius: 6px;
  text-decoration: none;
}
.hdr__nav {
  display: flex;
  align-items: center;
  gap: var(--s-1);
}
.hdr__link {
  position: relative;
  display: inline-flex;
  align-items: center;
  height: 40px;
  padding: 0 var(--s-3);
  border-radius: 6px;
  color: var(--muted);
  font-size: var(--fs-14);
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  transition: color var(--dur-1) var(--ease);
}
.hdr__link:hover {
  color: var(--ink);
}
.hdr__link[aria-current='page'] {
  color: var(--ink);
}
.hdr__link[aria-current='page']::after {
  content: '';
  position: absolute;
  left: var(--s-3);
  right: var(--s-3);
  bottom: -12px;
  height: 2px;
  background: var(--klar-red);
}
.hdr__right {
  display: flex;
  align-items: center;
  gap: var(--s-3);
  margin-left: auto;
}
.hdr__tools {
  display: flex;
  align-items: center;
  gap: var(--s-2);
}
.hdr__menu {
  display: none;
}
.mock-bar {
  border-top: 1px solid var(--line);
  background: var(--amber-tint);
  color: var(--ink);
}
.mock-bar__inner {
  display: flex;
  align-items: center;
  gap: 10px;
  height: calc(var(--mock-h) - 1px);
  font-size: var(--fs-14);
  white-space: nowrap;
  overflow: hidden;
}
.mock-bar__title {
  color: var(--amber);
}
.mock-bar__body {
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--ink);
}
.mock-bar__leave {
  margin-left: auto;
  flex: none;
  min-height: 30px;
  padding: 0 10px;
  border: 1px solid var(--amber);
  border-radius: var(--r-pill);
  background: var(--surface);
  color: var(--ink);
  font-size: var(--fs-12);
  font-weight: 700;
}
.hdr__sheet {
  border-top: 1px solid var(--line);
  background: var(--bg);
  padding-bottom: var(--s-4);
}
.hdr__sheet-nav {
  display: flex;
  flex-direction: column;
  padding-top: var(--s-2);
}
.hdr__sheet-link {
  display: flex;
  align-items: center;
  min-height: 48px;
  border-bottom: 1px solid var(--line);
  color: var(--ink);
  font-size: var(--fs-20);
  font-weight: 600;
  text-decoration: none;
}
.hdr__sheet-link[aria-current='page'] {
  box-shadow: inset 3px 0 0 var(--klar-red);
  padding-left: var(--s-3);
}
.hdr__sheet-tools {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: var(--s-4);
}
@media (max-width: 900px) {
  .mock-bar__body {
    display: none;
  }
}
@media (max-width: 640px) {
  .mock-bar__inner {
    flex-wrap: wrap;
    align-content: center;
    row-gap: 6px;
    white-space: normal;
  }
  .mock-bar__leave {
    margin-left: 20px;
  }
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
  .hdr__sheet {
    display: none !important;
  }
}
@media (max-width: 520px) {
  .hdr__inner {
    gap: var(--s-2);
  }
  .hdr__right {
    gap: var(--s-2);
  }
  .hdr__right :deep(.sov__label) {
    display: block;
    max-width: 30vw;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .hdr__right :deep(.sov__pill) {
    padding: 4px 10px;
    gap: 8px;
  }
  /* FE-3: a warning subline ("No recordings found") is cut, not allowed to widen the page (full text in the panel). */
  .hdr__right,
  .hdr__right :deep(.sov),
  .hdr__right :deep(.sov__pill),
  .hdr__right :deep(.sov__text) {
    min-width: 0;
  }
  .hdr__right :deep(.sov__warn) {
    max-width: 30vw;
  }
  .hdr__right :deep(.sov__warn-text) {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
</style>
