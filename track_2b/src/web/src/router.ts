import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'

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
  scrollBehavior(to, from, saved) {
    if (saved) return saved
    if (to.hash) return { el: to.hash, top: 80 }
    if (to.path === from.path) return false
    return { top: 0 }
  },
})
