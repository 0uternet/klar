import type {
  CreateScanRequest,
  CreateScanResponse,
  CriterionInfo,
  ExportFormat,
  Finding,
  Health,
  PatchFindingRequest,
  Scan,
  ScanEventHandlers,
  ScanSummary,
} from '@/types'

/** One interface, two implementations: HTTP (real backend) and mock (fixtures). */
export interface KlarApi {
  readonly kind: 'http' | 'mock'
  health(signal?: AbortSignal): Promise<Health>
  criteria(): Promise<CriterionInfo[]>
  createScan(body: CreateScanRequest): Promise<CreateScanResponse>
  getScan(id: string): Promise<Scan>
  /** GET /api/scans: newest first. */
  listScans(limit?: number): Promise<ScanSummary[]>
  /** Subscribe to live events. Returns an unsubscribe function. */
  subscribe(id: string, handlers: ScanEventHandlers): () => void
  patchFinding(id: string, body: PatchFindingRequest): Promise<Finding>
  /** Triggers a file download of the export. */
  exportScan(scan: Scan, format: ExportFormat): Promise<void>
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}
