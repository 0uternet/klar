import { ref } from 'vue'
import { useRouter } from 'vue-router'
import type { Scan, UiLang } from '@/types'
import { api } from '@/api'
import { locale } from '@/i18n'
import { lastScanId, prefill } from '@/stores/app'
import { isPasted } from '@/lib/format'

/**
 * The actions behind error states and run notes: run the same address again,
 * go back to the start page with the address (or the HTML field) ready to edit.
 */
export function useRerun() {
  const router = useRouter()
  const rerunning = ref(false)
  const rerunError = ref<string | null>(null)

  async function rerun(scan: Pick<Scan, 'url'> | undefined, lang?: UiLang) {
    if (!scan || isPasted(scan.url)) {
      prefill.value = { mode: 'html' }
      await router.push({ name: 'home' })
      return
    }
    rerunning.value = true
    rerunError.value = null
    try {
      const { id } = await api().createScan({ url: scan.url, ui_lang: lang ?? locale.value })
      lastScanId.value = id
      await router.push({ name: 'scan', params: { id } })
    } catch (e) {
      rerunError.value = e instanceof Error ? e.message : String(e)
    } finally {
      rerunning.value = false
    }
  }

  async function editAddress(scan: Pick<Scan, 'url'> | undefined) {
    prefill.value = scan && !isPasted(scan.url) ? { url: scan.url } : { mode: 'html' }
    await router.push({ name: 'home', query: { focus: '1' } })
  }

  async function pasteHtml() {
    prefill.value = { mode: 'html' }
    await router.push({ name: 'home', query: { focus: '1' } })
  }

  return { rerun, rerunning, rerunError, editAddress, pasteHtml }
}
