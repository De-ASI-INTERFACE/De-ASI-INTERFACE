import axios, { AxiosError } from 'axios';
import type { ExternalIssuePayload, SyncConfig } from './types';
const RETRYABLE = new Set([429,500,502,503,504]);
const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));
const isRetryable = (e: unknown) => e instanceof AxiosError && (e.response ? RETRYABLE.has(e.response.status) : true);
export async function syncIssueToTracker(payload: ExternalIssuePayload, config: SyncConfig): Promise<void> {
  for (let i = 0; i <= config.maxRetries; i++) {
    try { await axios.post(config.trackerUrl, payload, { headers: { 'X-Api-Key': config.trackerToken, 'Content-Type': 'application/json' }, timeout: config.timeoutMs, validateStatus: (s) => s >= 200 && s < 300 }); return; }
    catch (e) { if (!isRetryable(e) || i === config.maxRetries) throw e; await sleep(config.retryDelayMs * 2 ** i); }
  }
}
