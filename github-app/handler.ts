import { Probot } from 'probot';
import type { ExternalIssuePayload } from './types';
import { loadSyncConfig } from './config';
import { buildDedupeKey, claimDelivery, finaliseDelivery } from './dedupe';
import { syncIssueToTracker } from './sync';
export default (app: Probot) => {
  const config = loadSyncConfig();
  app.on('issues.opened', async (ctx) => {
    const issue = ctx.payload.issue; const repo = ctx.payload.repository;
    const key = buildDedupeKey((ctx as any).id ?? issue.node_id);
    if (!claimDelivery(key)) { ctx.log.info({ key }, 'Duplicate ignored'); return; }
    const payload: ExternalIssuePayload = { title: issue.title, body: issue.body ?? '', githubUrl: issue.html_url, issueNumber: issue.number, repoFullName: repo.full_name, deliveryKey: key };
    try { await syncIssueToTracker(payload, config); finaliseDelivery(key, 'completed'); ctx.log.info({ key }, 'Synced'); }
    catch (e) { finaliseDelivery(key, 'failed'); ctx.log.error({ key, e }, 'Sync failed'); throw e; }
  });
};
