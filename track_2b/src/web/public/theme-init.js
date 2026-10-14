// Apply the saved theme and language before first paint (no flash).
// A separate same-origin file so the UI runs under a strict CSP (script-src 'self').
;(function () {
  try {
    var t = localStorage.getItem('klar.theme')
    if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t)
    var l = localStorage.getItem('klar.lang')
    if (l === 'en' || l === 'de' || l === 'fr' || l === 'it') document.documentElement.lang = l
  } catch (e) {}
})()
