// Dogfooding: run axe-core (WCAG 2.0/2.1/2.2 A + AA) on Klar.'s own pages, in light
// and dark, EN and DE. Needs a running Klar. server and a Chromium.
//   KLAR_URL     base URL of the UI (default http://localhost:8080/)
//   KLAR_CHROME  path to a Chrome/Chromium executable (optional; otherwise the
//                Playwright-managed Chromium from `npx playwright install chromium`)
// Usage: npm run a11y
import fs from 'node:fs'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
let chromium
try {
  ;({ chromium } = require('playwright-core'))
} catch {
  console.error('a11y: install the dev dependencies first (npm ci).')
  process.exit(2)
}
const AXE = fs.readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8')
const base = (process.env.KLAR_URL ?? 'http://localhost:8080/').replace(/\/?$/, '/')

const browser = await chromium.launch({ headless: true, executablePath: process.env.KLAR_CHROME || undefined })
const routes = ['#/', '#/human', '#/about']

// A finished scan, if the server has one, adds the report view.
try {
  const res = await fetch(`${base}api/scans?limit=1`)
  const list = res.ok ? await res.json() : []
  const id = Array.isArray(list) && list[0] && (list[0].id ?? list[0].scan_id)
  if (id) routes.push(`#/report/${id}`)
} catch {
  /* server without scans */
}

let failures = 0
for (const colorScheme of ['light', 'dark']) {
  for (const lang of ['en', 'de']) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme })
    await ctx.addInitScript((l) => localStorage.setItem('klar.lang', l), lang)
    const page = await ctx.newPage()
    for (const route of routes) {
      await page.goto(base + route)
      await page.waitForTimeout(800)
      await page.addScriptTag({ content: AXE })
      const violations = await page.evaluate(async () => {
        // eslint-disable-next-line no-undef
        const r = await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] } })
        return r.violations.map((v) => `${v.id} (${v.impact}) x${v.nodes.length}: ${v.nodes[0]?.target.join(' ')}`)
      })
      const tag = `${colorScheme}/${lang} ${route}`
      if (violations.length) {
        failures += violations.length
        console.error(`✗ ${tag}`)
        for (const v of violations) console.error(`    ${v}`)
      } else console.log(`✓ ${tag}`)
    }
    await ctx.close()
  }
}
await browser.close()
if (failures) {
  console.error(`a11y: ${failures} violation(s)`)
  process.exit(1)
}
console.log('a11y: OK')
