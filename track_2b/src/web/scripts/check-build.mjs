// Checks the production build (../klar/api/static) and the sources:
//  - no CDN, web-font or analytics URL in the built assets (network discipline);
//  - no mock-up data in the production build (MOCK_SENTINEL absent);
//  - no inline <script> in index.html (CSP script-src 'self');
//  - no v-html in the sources (page content is always rendered as text);
//  - no banned conformance words in UI strings, and no guide that claims what Klar. does.
// Usage: node scripts/check-build.mjs [buildDir]
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '..')
const build = path.resolve(root, process.argv[2] ?? '../klar/api/static')

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const p = path.join(dir, e.name)
    return e.isDirectory() ? walk(p) : [p]
  })
}

const errors = []
if (!fs.existsSync(path.join(build, 'index.html'))) {
  console.error(`No build found in ${build}. Run "npm run build" first.`)
  process.exit(1)
}

const forbidden = /googleapis|gstatic|cdn\.|unpkg|jsdelivr|plausible|analytics|MOCK_SENTINEL/
for (const file of walk(build)) {
  if (!/\.(js|css|html|json|svg|txt)$/.test(file)) continue
  const text = fs.readFileSync(file, 'utf8')
  const m = text.match(forbidden)
  if (m) errors.push(`${path.relative(build, file)}: forbidden string "${m[0]}"`)
}

const index = fs.readFileSync(path.join(build, 'index.html'), 'utf8')
for (const tag of index.match(/<script\b[^>]*>[\s\S]*?<\/script>/g) ?? []) {
  if (!/\bsrc=/.test(tag)) errors.push('index.html: inline <script> (breaks CSP script-src \'self\')')
}

for (const file of walk(path.join(root, 'src'))) {
  if (file.endsWith('.vue') && /\bv-html\b/.test(fs.readFileSync(file, 'utf8').replace(/<!--[\s\S]*?-->/g, ''))) {
    errors.push(`${path.relative(root, file)}: v-html`)
  }
}

// UX-36: no conformance claims in any UI string (all locales) or human-check guide.
const banned = /compliant|certified|score|100 ?%/i
for (const file of [...walk(path.join(root, 'src/i18n')).filter((f) => /\/(en|de|fr|it)\.ts$/.test(f.replace(/\\/g, '/'))), path.join(root, 'src/data/human-guides.ts')]) {
  const lines = fs.readFileSync(file, 'utf8').split('\n')
  lines.forEach((l, i) => {
    const m = l.match(banned)
    if (m) errors.push(`${path.relative(root, file)}:${i + 1}: banned word "${m[0]}"`)
  })
}
// UX-7: a guide never states what Klar. does.
{
  const file = path.join(root, 'src/data/human-guides.ts')
  fs.readFileSync(file, 'utf8')
    .split('\n')
    .forEach((l, i) => {
      if (/why: '[^']*Klar/.test(l)) errors.push(`${path.relative(root, file)}:${i + 1}: a guide states what Klar. does`)
    })
}

if (errors.length) {
  console.error('check-build: FAILED')
  for (const e of errors) console.error(`  - ${e}`)
  process.exit(1)
}
console.log(`check-build: OK (${build})`)
