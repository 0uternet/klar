/** Unified-diff parsing with intra-line emphasis for paired -/+ lines. */
export type DiffKind = 'add' | 'del' | 'ctx' | 'hunk' | 'file'
export interface DiffPart {
  text: string
  em: boolean
}
export interface DiffLine {
  kind: DiffKind
  text: string
  parts: DiffPart[]
  line?: number
}

function emphasise(a: string, b: string): [DiffPart[], DiffPart[]] {
  let p = 0
  while (p < a.length && p < b.length && a[p] === b[p]) p++
  let s = 0
  while (s < a.length - p && s < b.length - p && a[a.length - 1 - s] === b[b.length - 1 - s]) s++
  const split = (x: string): DiffPart[] =>
    [
      { text: x.slice(0, p), em: false },
      { text: x.slice(p, x.length - s), em: true },
      { text: x.slice(x.length - s), em: false },
    ].filter((part) => part.text.length > 0)
  return [split(a), split(b)]
}

export function parseDiff(diff: string): { file: string | null; lines: DiffLine[] } {
  const raw = diff.replace(/\r\n/g, '\n').split('\n')
  let file: string | null = null
  const lines: DiffLine[] = []
  let oldNo = 0
  let newNo = 0
  for (const l of raw) {
    if (l.startsWith('+++ ')) {
      file = l.slice(4).replace(/^b\//, '')
      continue
    }
    if (l.startsWith('--- ')) continue
    if (l.startsWith('@@')) {
      const m = /@@ -(\d+)(?:,\d+)? \+(\d+)/.exec(l)
      oldNo = m ? Number(m[1]) : 0
      newNo = m ? Number(m[2]) : 0
      lines.push({ kind: 'hunk', text: l, parts: [{ text: l, em: false }], line: newNo })
      continue
    }
    if (l.startsWith('+')) {
      lines.push({ kind: 'add', text: l.slice(1), parts: [{ text: l.slice(1), em: false }], line: newNo++ })
    } else if (l.startsWith('-')) {
      lines.push({ kind: 'del', text: l.slice(1), parts: [{ text: l.slice(1), em: false }], line: oldNo++ })
    } else if (l.length > 0 || lines.length > 0) {
      const text = l.startsWith(' ') ? l.slice(1) : l
      lines.push({ kind: 'ctx', text, parts: [{ text, em: false }], line: newNo++ })
      oldNo++
    }
  }
  // Pair runs of deletions followed by the same number of additions.
  for (let i = 0; i < lines.length; ) {
    if (lines[i]!.kind !== 'del') {
      i++
      continue
    }
    let d = i
    while (d < lines.length && lines[d]!.kind === 'del') d++
    let a = d
    while (a < lines.length && lines[a]!.kind === 'add') a++
    const dels = d - i
    const adds = a - d
    for (let k = 0; k < Math.min(dels, adds); k++) {
      const del = lines[i + k]!
      const add = lines[d + k]!
      const [pd, pa] = emphasise(del.text, add.text)
      // Only emphasise when the lines share a meaningful part.
      if (pd.some((x) => !x.em) || pa.some((x) => !x.em)) {
        del.parts = pd
        add.parts = pa
      }
    }
    i = a
  }
  return { file, lines }
}
