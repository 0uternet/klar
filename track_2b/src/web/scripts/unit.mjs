// Runs scripts/unit.test.ts: bundles it with esbuild (shipped with Vite) and executes it in Node.
// Usage: node scripts/unit.mjs
import { build } from 'esbuild'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import fs from 'node:fs'
import os from 'node:os'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '..')
const outfile = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'klar-unit-')), 'unit.mjs')

await build({
  entryPoints: [path.join(here, 'unit.test.ts')],
  bundle: true,
  platform: 'node',
  format: 'esm',
  target: 'node20',
  outfile,
  alias: { '@': path.join(root, 'src') },
  define: { __KLAR_MOCKS__: 'false', 'import.meta.env.DEV': 'false', 'import.meta.env.VITE_DEMO_URL': 'undefined', 'import.meta.env.VITE_API_BASE': 'undefined' },
  logLevel: 'warning',
})

// Minimal browser globals used at module load (storage and location are optional in the code).
globalThis.location ??= { origin: 'http://localhost', hostname: 'localhost', search: '', hash: '' }
await import(pathToFileURL(outfile).href)
