// Contract check: src/types.ts must mirror the backend models (klar/models.py).
// The backend's tests/test_contract.py writes, from the real Pydantic models:
//   tests/fixtures/contract/schema/<name>.schema.json   JSON Schemas
//   tests/fixtures/contract/<name>.json                 deterministic example payloads
// This script
//   1. compares property names: a schema property missing in TypeScript fails, and a
//      required TypeScript field missing in the schema fails ("?" fields are UI-only);
//   2. type-checks every example payload against the TypeScript types with tsc.
// CONTRACT_STRICT=1 (CI) makes missing fixtures fail as well.
// Usage: node scripts/contract.mjs [fixturesDir]
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '..')
const dir = path.resolve(root, process.argv[2] ?? '../../tests/fixtures/contract')
const typesFile = path.join(root, 'src/types.ts')
const types = fs.readFileSync(typesFile, 'utf8')
const strict = process.env.CONTRACT_STRICT === '1'

const schemaDir = fs.existsSync(path.join(dir, 'schema')) ? path.join(dir, 'schema') : dir
const schemaFiles = fs.existsSync(schemaDir) ? fs.readdirSync(schemaDir).filter((f) => f.endsWith('.json')) : []
if (!schemaFiles.length) {
  const msg = `contract: no fixtures at ${dir} (the backend contract test writes them).`
  if (strict) {
    console.error(`${msg} CONTRACT_STRICT=1, so this fails.`)
    process.exit(1)
  }
  console.warn(`${msg} Nothing to compare.`)
  process.exit(0)
}

/** Field names of `export interface Name { ... }` (top level only), with optionality. */
function tsFields(name) {
  const m = types.match(new RegExp(`export interface ${name}\\s*\\{([\\s\\S]*?)\\n\\}`))
  if (!m) return null
  const fields = new Map()
  for (const line of m[1].split('\n')) {
    const f = line.match(/^ {2}([a-zA-Z_][\w]*)(\??):/)
    if (f) fields.set(f[1], f[2] === '?')
  }
  return fields
}

// Pydantic model name → TypeScript interface (same name when not listed).
const MAP = { Criterion: 'CriterionInfo', ScanRequest: 'CreateScanRequest', ScanCreated: 'CreateScanResponse', FindingPatch: 'PatchFindingRequest' }

const errors = []
let compared = 0
for (const file of schemaFiles) {
  const schema = JSON.parse(fs.readFileSync(path.join(schemaDir, file), 'utf8'))
  if (!schema.properties) continue
  const title = schema.title ?? path.basename(file).replace(/\.schema\.json$|\.json$/, '')
  const tsName = MAP[title] ?? title
  const ts = tsFields(tsName)
  if (!ts) {
    errors.push(`${file}: no interface "${tsName}" in src/types.ts`)
    continue
  }
  compared++
  const props = Object.keys(schema.properties)
  for (const p of props) if (!ts.has(p)) errors.push(`${tsName}: schema property "${p}" missing in TypeScript`)
  for (const [f, optional] of ts) if (!optional && !props.includes(f)) errors.push(`${tsName}: required TypeScript field "${f}" not in schema`)
}

// 2. Type-check the example payloads.
const EXAMPLES = {
  'health.json': 'Health',
  'scan.json': 'Scan',
  'finding.json': 'Finding',
  'progress_step.json': 'ProgressStep',
  'stats.json': 'ScanStats',
  'criteria.json': 'CriterionInfo[]',
  'criterion_info.json': null, // a schema copy, not an example
}
const examples = Object.entries(EXAMPLES).filter(([f, t]) => t && fs.existsSync(path.join(dir, f)))
if (examples.length) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'klar-contract-'))
  const rel = path.relative(tmp, typesFile).replace(/\\/g, '/').replace(/\.ts$/, '')
  const names = [...new Set(examples.map(([, t]) => t.replace('[]', '')))]
  const lines = [
    `import type { ${names.join(', ')} } from '${rel.startsWith('.') ? rel : `./${rel}`}'`,
    // A generic check keeps literal types and allows extra keys (the server may send more).
    'const check = <T,>() => <U extends T>(u: U): U => u',
  ]
  for (const [file, type] of examples) {
    const json = fs.readFileSync(path.join(dir, file), 'utf8')
    lines.push(`// ${file}`, `check<${type}>()(${json.trim()})`)
  }
  const entry = path.join(tmp, 'contract-examples.ts')
  fs.writeFileSync(entry, lines.join('\n') + '\n')
  const tsc = path.join(root, 'node_modules/typescript/bin/tsc')
  try {
    execFileSync(process.execPath, [tsc, '--noEmit', '--strict', '--target', 'es2022', '--module', 'esnext', '--moduleResolution', 'bundler', '--skipLibCheck', entry], {
      stdio: 'pipe',
    })
    console.log(`contract: ${examples.length} example payload(s) type-check against src/types.ts`)
  } catch (e) {
    const out = `${e.stdout ?? ''}${e.stderr ?? ''}`.trim()
    errors.push(`example payloads do not type-check:\n${out.split('\n').slice(0, 30).join('\n')}`)
  }
}

if (errors.length) {
  console.error('contract: FAILED')
  for (const e of errors) console.error(`  - ${e}`)
  process.exit(1)
}
console.log(`contract: OK (${compared} schema(s) compared)`)
