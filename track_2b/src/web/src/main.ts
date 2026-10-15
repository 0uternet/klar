import { createApp } from 'vue'
import './styles/fonts.css'
import './styles/tokens.css'
import './styles/base.css'
import './styles/motion.css'
import App from './App.vue'
import { router } from './router'
import { ensureBooted } from './stores/app'
import { loadLocale, locale } from './i18n'
import { vReveal } from './lib/motion'

// Decide between the real backend and demo data without blocking first paint.
void ensureBooted()

// Mount once the UI language is loaded (English is built in; DE/FR/IT are small chunks).
void loadLocale(locale.value).finally(() => createApp(App).directive('reveal', vReveal).use(router).mount('#app'))
