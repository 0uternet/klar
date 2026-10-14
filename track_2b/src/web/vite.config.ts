import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// The Klar. API (FastAPI) runs on :8080 in development and serves the built UI
// from src/klar/api/static in production: one container, one port.
const API_TARGET = process.env.KLAR_API ?? 'http://localhost:8080'

const proxy = {
  '/api': { target: API_TARGET, changeOrigin: true },
}

export default defineConfig(({ mode }) => {
  // Mock-up data is compiled in only for the dev server and `--mode demo` builds.
  // Production builds (`npm run build`) contain no mock module at all.
  const mocks = mode === 'development' || mode === 'demo'
  return {
    plugins: [vue()],
    // Relative asset URLs: the UI works wherever FastAPI mounts it.
    base: './',
    define: {
      __KLAR_MOCKS__: JSON.stringify(mocks),
    },
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    build: {
      // The labelled demo build never lands in the backend's static folder.
      outDir: mode === 'demo' ? 'dist-demo' : '../klar/api/static',
      emptyOutDir: true,
      target: 'es2022',
      cssCodeSplit: true,
      reportCompressedSize: true,
      chunkSizeWarningLimit: 300,
    },
    server: { port: 5173, proxy },
    preview: { port: 4173, proxy },
  }
})
