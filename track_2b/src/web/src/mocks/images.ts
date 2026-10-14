/**
 * Screenshot crops for the mock scan, drawn as inline SVG (no network, no binaries).
 * They imitate what the backend's Playwright crops of the demo site look like.
 */

function uri(svg: string): string {
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg.replace(/\s+/g, ' ').trim())}`
}

const FONT = 'font-family="Arial, Helvetica, sans-serif"'

const bars = [
  { y: '2021', v: 4.1 },
  { y: '2022', v: 4.4 },
  { y: '2023', v: 4.6 },
  { y: '2024', v: 5.0 },
  { y: '2025', v: 5.3 },
]
const base = 310
const scale = 200 / 6

export const CHART = uri(`
<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360" ${FONT}>
  <rect width="640" height="360" fill="#ffffff"/>
  <text x="32" y="42" font-size="20" font-weight="700" fill="#1d3557">Steuerertrag natürliche Personen</text>
  <text x="32" y="66" font-size="14" fill="#5b6475">in Mio. Franken, 2021–2025</text>
  ${[0, 2, 4, 6]
    .map(
      (g) => `<line x1="60" x2="610" y1="${base - g * scale}" y2="${base - g * scale}" stroke="#e3e6ec"/>
      <text x="50" y="${base - g * scale + 5}" font-size="12" fill="#5b6475" text-anchor="end">${g}</text>`,
    )
    .join('')}
  ${bars
    .map((b, i) => {
      const x = 92 + i * 104
      const h = b.v * scale
      const fill = i === bars.length - 1 ? '#1d3557' : '#3f7cc1'
      return `<rect x="${x}" y="${base - h}" width="64" height="${h}" fill="${fill}" rx="2"/>
      <text x="${x + 32}" y="${base - h - 8}" font-size="13" font-weight="700" fill="#1d3557" text-anchor="middle">${String(b.v).replace('.', ',')}</text>
      <text x="${x + 32}" y="${base + 22}" font-size="13" fill="#5b6475" text-anchor="middle">${b.y}</text>`
    })
    .join('')}
</svg>`)

export const BANNER = uri(`
<svg xmlns="http://www.w3.org/2000/svg" width="640" height="160" viewBox="0 0 640 160" ${FONT}>
  <defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#0f5257"/><stop offset="1" stop-color="#1d6f6a"/></linearGradient></defs>
  <rect width="640" height="160" fill="url(#g)"/>
  <circle cx="72" cy="80" r="34" fill="none" stroke="#e8f3ef" stroke-width="4"/>
  <path d="M72 58 V80 L88 90" fill="none" stroke="#e8f3ef" stroke-width="4" stroke-linecap="round"/>
  <text x="130" y="58" font-size="22" font-weight="700" fill="#ffffff">Öffnungszeiten Gemeindeverwaltung</text>
  <text x="130" y="94" font-size="17" fill="#e8f3ef">Montag–Freitag   08.00–11.30 Uhr</text>
  <text x="130" y="122" font-size="17" fill="#e8f3ef">Donnerstag       14.00–18.30 Uhr</text>
</svg>`)

export const TOWN_HALL = uri(`
<svg xmlns="http://www.w3.org/2000/svg" width="480" height="300" viewBox="0 0 480 300">
  <defs><linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#cfe0f1"/><stop offset="1" stop-color="#eef4f9"/></linearGradient></defs>
  <rect width="480" height="300" fill="url(#s)"/>
  <rect y="240" width="480" height="60" fill="#c9d6b8"/>
  <rect x="120" y="130" width="240" height="115" fill="#f2e7d3"/>
  <polygon points="108,132 240,78 372,132" fill="#9c4a3a"/>
  <rect x="214" y="40" width="52" height="96" fill="#efe2cb"/>
  <polygon points="208,44 240,12 272,44" fill="#7f3a2d"/>
  <circle cx="240" cy="70" r="15" fill="#ffffff" stroke="#3b3b3b" stroke-width="2"/>
  <path d="M240 60 V70 L247 74" stroke="#3b3b3b" stroke-width="2" fill="none"/>
  ${[0, 1, 2, 3, 4, 5]
    .map((i) => `<rect x="${140 + i * 36}" y="152" width="20" height="28" fill="#6b8bb0"/><rect x="${140 + i * 36}" y="196" width="20" height="28" fill="#6b8bb0"/>`)
    .join('')}
  <rect x="226" y="200" width="28" height="45" fill="#7a5a3a"/>
  <rect x="402" y="190" width="10" height="55" fill="#6b4f33"/>
  <circle cx="407" cy="165" r="42" fill="#4f7a3a"/>
  <circle cx="385" cy="185" r="26" fill="#5c8a45"/>
</svg>`)

export const LOGO = uri(`
<svg xmlns="http://www.w3.org/2000/svg" width="320" height="96" viewBox="0 0 320 96" ${FONT}>
  <rect width="320" height="96" fill="#ffffff"/>
  <circle cx="48" cy="48" r="30" fill="#1d3557"/>
  <path d="M33 62 V36 L48 52 L63 36 V62" fill="none" stroke="#ffffff" stroke-width="5" stroke-linejoin="round"/>
  <text x="92" y="44" font-size="15" fill="#5b6475">Gemeinde</text>
  <text x="92" y="68" font-size="24" font-weight="700" fill="#1d3557">Musterwil</text>
</svg>`)

export const FORM_BUTTONS = uri(`
<svg xmlns="http://www.w3.org/2000/svg" width="640" height="230" viewBox="0 0 640 230" ${FONT}>
  <rect width="640" height="230" fill="#ffffff"/>
  <text x="24" y="34" font-size="15" fill="#333333">Klicken Sie auf den grünen Knopf rechts, um das Formular abzusenden.</text>
  <text x="24" y="70" font-size="13" font-weight="700" fill="#333333">Feld 3</text>
  <rect x="24" y="80" width="592" height="76" fill="#ffffff" stroke="#b9bec7" rx="3"/>
  <rect x="24" y="176" width="140" height="38" rx="4" fill="#e9ebef"/>
  <text x="94" y="200" font-size="14" fill="#333333" text-anchor="middle">Zurücksetzen</text>
  <rect x="456" y="176" width="160" height="38" rx="4" fill="#2e8b57"/>
  <text x="536" y="200" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">Anfrage senden</text>
</svg>`)

export const FORM_ERROR = uri(`
<svg xmlns="http://www.w3.org/2000/svg" width="640" height="200" viewBox="0 0 640 200" ${FONT}>
  <rect width="640" height="200" fill="#ffffff"/>
  <rect x="24" y="18" width="592" height="36" fill="#fdecec"/>
  <text x="40" y="42" font-size="15" font-weight="700" fill="#c40000">Fehler</text>
  <text x="24" y="86" font-size="13" font-weight="700" fill="#333333">Name</text>
  <rect x="24" y="94" width="280" height="34" fill="#ffffff" stroke="#b9bec7" rx="3"/>
  <text x="36" y="116" font-size="14" fill="#333333">Anna Muster</text>
  <text x="336" y="86" font-size="13" font-weight="700" fill="#333333">E-Mail</text>
  <rect x="336" y="94" width="280" height="34" fill="#ffffff" stroke="#b9bec7" rx="3"/>
  <text x="348" y="116" font-size="14" fill="#333333">anna.muster.musterwil.ch</text>
  <rect x="456" y="148" width="160" height="38" rx="4" fill="#2e8b57"/>
  <text x="536" y="172" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">Anfrage senden</text>
</svg>`)

export const ARROW_LINK = uri(`
<svg xmlns="http://www.w3.org/2000/svg" width="360" height="80" viewBox="0 0 360 80" ${FONT}>
  <rect width="360" height="80" fill="#ffffff"/>
  <rect x="20" y="16" width="256" height="48" rx="24" fill="#1d3557"/>
  <text x="48" y="46" font-size="16" font-weight="700" fill="#ffffff">Zum Online-Schalter</text>
  <path d="M232 40 H256 M246 30 L256 40 L246 50" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>`)
