import { createRouter, createWebHashHistory, START_LOCATION, type RouteLocationNormalized } from 'vue-router'
import HomeView from './views/HomeView.vue'

/* ---- Scrolling around the page transition ---------------------------------
 * App.vue swaps pages with an out-in transition: the old page fades out first, and only
 * then does the new (often lazy) page mount. So the scroll waits for the swap: the old page
 * never jumps while it fades, and hash targets such as #/about#connect exist when we look.
 */

/** Same key as the <component> in App.vue: a new key means a page swap with a transition. */
const pageKey = (r: RouteLocationNormalized) => `${String(r.name)}:${String(r.params.id ?? '')}`

const frame = () => new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))

function reducedMotion(): boolean {
  return !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

/** Resolves when App.vue reports that the old page has left (or after a safety timeout). */
function pageLeft(): Promise<void> {
  return new Promise((resolve) => {
    const done = () => {
      window.removeEventListener('klar:page-left', done)
      window.clearTimeout(timer)
      resolve()
    }
    const timer = window.setTimeout(done, 600)
    window.addEventListener('klar:page-left', done)
  })
}

/** Waits up to ~1.5 s for a lazy page to render the target. */
async function findTarget(hash: string): Promise<HTMLElement | null> {
  let id = hash.slice(1)
  try {
    id = decodeURIComponent(id)
  } catch {
    /* keep it raw */
  }
  for (let i = 0; i < 90; i++) {
    const el = document.getElementById(id)
    if (el) return el
    await frame()
  }
  return null
}

/** Back/forward: wait up to ~1 s for async content (lists, reports) to make the page tall enough. */
async function roomFor(top: number): Promise<void> {
  for (let i = 0; i < 60; i++) {
    if (document.documentElement.scrollHeight - window.innerHeight >= top) return
    await frame()
  }
}

/** Document position, ignoring transforms (entrance and scroll-reveal animations move elements). */
function documentTop(el: HTMLElement): number {
  let y = 0
  for (let n: HTMLElement | null = el; n; n = n.offsetParent as HTMLElement | null) y += n.offsetTop
  return y
}

/** Room for the sticky header (AppHeader measures it into --header-h), plus a little air. */
function headerOffset(): number {
  const h = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--header-h'))
  return (Number.isFinite(h) ? h : 64) + 16
}

/**
 * Hash history: FastAPI serves the built UI as static files, so deep links
 * (e.g. #/report/abc) work on reload without any server-side fallback route.
 */
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/scan/:id', name: 'scan', component: () => import('./views/ScanView.vue'), props: true },
    { path: '/report/:id', name: 'report', component: () => import('./views/ReportView.vue'), props: true },
    { path: '/human', name: 'human', component: () => import('./views/HumanView.vue') },
    { path: '/about', name: 'about', component: () => import('./views/AboutView.vue') },
    { path: '/:pathMatch(.*)*', name: 'notfound', component: () => import('./views/NotFoundView.vue') },
  ],
  async scrollBehavior(to, from, saved) {
    const first = from === START_LOCATION
    const swap = !first && pageKey(to) !== pageKey(from)
    if (swap) {
      await pageLeft()
      await frame()
    }
    if (saved) {
      await roomFor(saved.top)
      return saved
    }
    if (to.hash) {
      const el = await findTarget(to.hash)
      if (!el) return swap ? { top: 0 } : false
      // A jump within the page glides (unless reduced motion); arriving from elsewhere lands at once.
      const inPage = !first && to.path === from.path
      return { top: Math.max(0, documentTop(el) - headerOffset()), behavior: inPage && !reducedMotion() ? 'smooth' : 'auto' }
    }
    if (to.path === from.path) return false
    return { top: 0 }
  },
})

// The other pages load in the background once the first one is shown, so a tab opens at once.
void router.isReady().then(() => {
  const warm = () => {
    void import('./views/HumanView.vue')
    void import('./views/AboutView.vue')
    void import('./views/ScanView.vue')
    void import('./views/ReportView.vue')
  }
  if (typeof window.requestIdleCallback === 'function') window.requestIdleCallback(warm, { timeout: 3000 })
  else setTimeout(warm, 1500)
})
