<script setup lang="ts">
import { nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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

/** After navigation, move focus to the new page's heading (announced by screen readers). */
let first = true
watch(
  () => route.path,
  async () => {
    if (first) {
      first = false
      return
    }
    await nextTick()
    await nextTick()
    const h1 = document.querySelector<HTMLElement>('#main h1')
    if (h1) {
      if (!h1.hasAttribute('tabindex')) h1.setAttribute('tabindex', '-1')
      h1.focus({ preventScroll: true })
    }
  },
)

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
      <component :is="Component" :key="`${String(r.name)}:${String(r.params.id ?? '')}`" />
    </RouterView>
  </main>
  <AppFooter :inert="modalOpen || undefined" />
  <ToastHost />
  <ShortcutsDialog />
</template>

<style>
#main {
  display: block;
  min-height: calc(100vh - var(--header-h) - 200px);
}
#main:focus {
  outline: none;
}
.config-error {
  margin-top: var(--s-5);
}
</style>
