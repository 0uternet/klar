/**
 * Minimal HTML tokenizer for evidence excerpts, plus "quoted span" marking.
 * Output is rendered with text interpolation only (never v-html), so page
 * content can never execute in Klar.
 */
export type TokKind = 'text' | 'tag' | 'attr' | 'value' | 'punct' | 'comment'
export interface Tok {
  text: string
  kind: TokKind
}
export interface Segment {
  mark: boolean
  toks: Tok[]
}

export function tokenizeHtml(src: string): Tok[] {
  const out: Tok[] = []
  const push = (text: string, kind: TokKind) => {
    if (!text) return
    const last = out[out.length - 1]
    if (last && last.kind === kind) last.text += text
    else out.push({ text, kind })
  }
  let i = 0
  while (i < src.length) {
    if (src.startsWith('<!--', i)) {
      const end = src.indexOf('-->', i + 4)
      const j = end < 0 ? src.length : end + 3
      push(src.slice(i, j), 'comment')
      i = j
      continue
    }
    if (src[i] === '<' && /[a-zA-Z/!]/.test(src[i + 1] ?? '')) {
      let j = i + 1
      push('<', 'punct')
      if (src[j] === '/' || src[j] === '!') {
        push(src[j]!, 'punct')
        j++
      }
      const name = /^[a-zA-Z][\w:-]*/.exec(src.slice(j))
      if (name) {
        push(name[0], 'tag')
        j += name[0].length
      }
      while (j < src.length && src[j] !== '>') {
        const rest = src.slice(j)
        let m: RegExpExecArray | null
        if ((m = /^\s+/.exec(rest))) push(m[0], 'text')
        else if ((m = /^("[^"]*"?|'[^']*'?)/.exec(rest))) push(m[0], 'value')
        else if ((m = /^[^\s=>/"']+/.exec(rest))) push(m[0], 'attr')
        else {
          m = /^./s.exec(rest)!
          push(m[0], 'punct')
        }
        j += m[0].length
      }
      if (src[j] === '>') {
        push('>', 'punct')
        j++
      }
      i = j
      continue
    }
    const next = src.indexOf('<', i + 1)
    const j = next < 0 ? src.length : next
    push(src.slice(i, j), 'text')
    i = j
  }
  return out
}

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/** Locate the quote in the source: exact first, then whitespace-insensitive. */
export function findQuote(source: string, quote: string): [number, number] | null {
  if (!quote) return null
  const i = source.indexOf(quote)
  if (i >= 0) return [i, i + quote.length]
  const words = quote.trim().split(/\s+/).map(escapeRe)
  if (words.length === 0) return null
  const m = new RegExp(words.join('\\s+')).exec(source)
  return m ? [m.index, m.index + m[0].length] : null
}

/** Split tokens into unmarked / marked / unmarked segments. */
export function segment(toks: Tok[], range: [number, number] | null): Segment[] {
  if (!range) return [{ mark: false, toks }]
  const [start, end] = range
  const before: Tok[] = []
  const inside: Tok[] = []
  const after: Tok[] = []
  let pos = 0
  for (const t of toks) {
    const a = pos
    const b = pos + t.text.length
    pos = b
    const cut = (from: number, to: number) => t.text.slice(Math.max(0, from - a), Math.max(0, to - a))
    if (b <= start) before.push(t)
    else if (a >= end) after.push(t)
    else {
      const pre = cut(a, start)
      const mid = cut(Math.max(a, start), Math.min(b, end))
      const post = cut(end, b)
      if (pre) before.push({ text: pre, kind: t.kind })
      if (mid) inside.push({ text: mid, kind: t.kind })
      if (post) after.push({ text: post, kind: t.kind })
    }
  }
  return [
    { mark: false, toks: before },
    { mark: true, toks: inside },
    { mark: false, toks: after },
  ].filter((s) => s.toks.length > 0)
}
