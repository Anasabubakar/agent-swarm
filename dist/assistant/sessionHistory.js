import axios from 'axios';
import { getOauthConfig } from '../constants/oauth.js';
import { logForDebugging } from '../utils/debug.js';
import { getOAuthHeaders, prepareApiRequest } from '../utils/teleport/api.js';
export const HISTORY_PAGE_SIZE = 100;
/** Prepare auth + headers + base URL once, reuse across pages. */
export async function createHistoryAuthCtx(sessionId) {
    const { accessToken, orgUUID } = await prepareApiRequest();
    return {
        baseUrl: `${getOauthConfig().BASE_API_URL}/v1/sessions/${sessionId}/events`,
        headers: {
            ...getOAuthHeaders(accessToken),
            'anthropic-beta': 'ccr-byoc-2025-07-29',
            'x-organization-uuid': orgUUID,
        },
    };
}
async function fetchPage(ctx, params, label) {
    const resp = await axios
        .get(ctx.baseUrl, {
        headers: ctx.headers,
        params,
        timeout: 15000,
        validateStatus: () => true,
    })
        .catch(() => null);
    if (!resp || resp.status !== 200) {
        logForDebugging(`[${label}] HTTP ${resp?.status ?? 'error'}`);
        return null;
    }
    return {
        events: Array.isArray(resp.data.data) ? resp.data.data : [],
        firstId: resp.data.first_id,
        hasMore: resp.data.has_more,
    };
}
/**
 * Newest page: last `limit` events, chronological, via anchor_to_latest.
 * has_more=true means older events exist.
 */
export async function fetchLatestEvents(ctx, limit = HISTORY_PAGE_SIZE) {
    return fetchPage(ctx, { limit, anchor_to_latest: true }, 'fetchLatestEvents');
}
/** Older page: events immediately before `beforeId` cursor. */
export async function fetchOlderEvents(ctx, beforeId, limit = HISTORY_PAGE_SIZE) {
    return fetchPage(ctx, { limit, before_id: beforeId }, 'fetchOlderEvents');
}
