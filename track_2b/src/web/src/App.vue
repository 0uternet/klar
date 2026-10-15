<script setup lang="ts">
import { useRoute, useRouter, START_LOCATION } from 'vue-router'
import { t } from '@/i18n'
import { health, modalOpen, shortcutsDialogOpen } from '@/stores/app'
import { useShortcuts } from '@/composables/useShortcuts'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import ToastHost from '@/components/ToastHost.vue'
import ShortcutsDialog from '@/components/ShortcutsDialog.vue'
import ErrorState from '@/components/ErrorState.vue'

const route = useRoute()
const router = useRouter()

/** Skip link: hash routing owns location.hash, so move focus programmatically. */
function skipToMain() {
  const main = document.getElementById('main')
  main?.focus()
  main?.scrollIntoView()
}

/**
 * After navigation, move focus to the new page's heading (announced by screen readers).
 * Pages swap with an out-in transition, so the new heading exists only once the new page
 * has entered: `onPageEnter` focuses it. When the page component is reused (same key,
 * no transition), the afterEach hook does it after the next render.
 */
let pending = false

function focusHeading() {
  pending = false
  const h1 = document.querySelector<HTMLElement>('#main h1')
  if (!h1) return
  if (!h1.hasAttribute('tabindex')) h1.setAttribute('tabindex', '-1')
  h1.focus({ preventScroll: true })
}

router.afterEach((to, from, failure) => {
  // Not on first load, not for query or hash changes on the same page.
  if (failure || from === START_LOCATION || to.path === from.path) return
  pending = true
  // Reused component: no enter hook will run. Two frames cover the render.
  requestAnimationFrame(() =>
    requestAnimationFrame(() => {
      if (pending && !document.querySelector('#main .page-leave-active, #main .page-enter-active')) focusHeading()
    }),
  )
})

/**
 * The old page has faded out. Announced so that router.ts can scroll only now, instead of
 * jumping the outgoing page to the top while it fades (see scrollBehavior).
 */
function onPageLeft() {
  window.dispatchEvent(new Event('klar:page-left'))
}

/** On insert, and once more after the enter animation for headings that render a tick late. */
function onPageEnter() {
  if (pending && document.querySelector('#main h1')) focusHeading()
}

useShortcuts({
  '?': (e) => {
    e.preventDefault()
    shortcutsDialogOpen.value = true
  },
  '/': (e) => {
    // Views with their own target (home field, report search) handle '/' first.
    if (route.name === 'home' || route.name === 'report') return
    e.preventDefault()
    void router.push({ name: 'home', query: { focus: '1' } })
  },
})
</script>

<template>
  <a href="#main" class="skip-link" @click.prevent="skipToMain">{{ t('app.skip') }}</a>
  <!-- UX-14: while the finding panel is a modal overlay, everything behind it is inert. -->
  <AppHeader :inert="modalOpen || undefined" />
  <main id="main" tabindex="-1">
    <div v-if="health?.config_error" class="container config-error" :inert="modalOpen || undefined">
      <ErrorState :title="t('config.title')" :body="t('config.body')" :details="health.config_error" role="alert">
        <RouterLink class="btn btn--primary" :to="{ name: 'about', hash: '#connect' }">{{ t('notes.connect') }}</RouterLink>
      </ErrorState>
    </div>
    <!-- Remount when the scan id changes (e.g. "Run the check again" from a scan page). -->
    <RouterView v-slot="{ Component, route: r }">
      <Transition name="page" mode="out-in" @after-leave="onPageLeft" @enter="onPageEnter" @after-enter="onPageEnter">
        <component :is="Component" :key="`${String(r.name)}:${String(r.params.id ?? '')}`" />
      </Transition>
    </RouterView>
  </main>
  <AppFooter :inert="modalOpen || undefined" />
  <ToastHost />
  <ShortcutsDialog />
</template>

<style>
/* Footer stays at the bottom of short pages. */
#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
}
#main {
  display: block;
  flex: 1 0 auto;
}
#main:focus {
  outline: none;
}
.config-error {
  margin-top: var(--s-5);
}
</style>
