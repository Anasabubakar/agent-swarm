import axios from 'axios';
import { debugBody, extractErrorDetail } from './debugUtils.js';
import { BRIDGE_LOGIN_INSTRUCTION, } from './types.js';
const BETA_HEADER = 'environments-2025-11-01';
/** Allowlist pattern for server-provided IDs used in URL path segments. */
const SAFE_ID_PATTERN = /^[a-zA-Z0-9_-]+$/;
/**
 * Validate that a server-provided ID is safe to interpolate into a URL path.
 * Prevents path traversal (e.g. `../../admin`) and injection via IDs that
 * contain slashes, dots, or other special characters.
 */
export function validateBridgeId(id, label) {
    if (!id || !SAFE_ID_PATTERN.test(id)) {
        throw new Error(`Invalid ${label}: contains unsafe characters`);
    }
    return id;
}
/** Fatal bridge errors that should not be retried (e.g. auth failures). */
export class BridgeFatalError extends Error {
    status;
    /** Server-provided error type, e.g. "environment_expired". */
    errorType;
    constructor(message, status, errorType) {
        super(message);
        this.name = 'BridgeFatalError';
        this.status = status;
        this.errorType = errorType;
    }
}
export function createBridgeApiClient(deps) {
    function debug(msg) {
        deps.onDebug?.(msg);
    }
    let consecutiveEmptyPolls = 0;
    const EMPTY_POLL_LOG_INTERVAL = 100;
    function getHeaders(accessToken) {
        const headers = {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01',
            'anthropic-beta': BETA_HEADER,
            'x-environment-runner-version': deps.runnerVersion,
        };
        const deviceToken = deps.getTrustedDeviceToken?.();
        if (deviceToken) {
            headers['X-Trusted-Device-Token'] = deviceToken;
        }
        return headers;
    }
    function resolveAuth() {
        const accessToken = deps.getAccessToken();
        if (!accessToken) {
            throw new Error(BRIDGE_LOGIN_INSTRUCTION);
        }
        return accessToken;
    }
    /**
     * Execute an OAuth-authenticated request with a single retry on 401.
     * On 401, attempts token refresh via handleOAuth401Error (same pattern as
     * withRetry.ts for v1/messages). If refresh succeeds, retries the request
     * once with the new token. If refresh fails or the retry also returns 401,
     * the 401 response is returned for handleErrorStatus to throw BridgeFatalError.
     */
    async function withOAuthRetry(fn, context) {
        const accessToken = resolveAuth();
        const response = await fn(accessToken);
        if (response.status !== 401) {
            return response;
        }
        if (!deps.onAuth401) {
            debug(`[bridge:api] ${context}: 401 received, no refresh handler`);
            return response;
        }
        // Attempt token refresh — matches the pattern in withRetry.ts
        debug(`[bridge:api] ${context}: 401 received, attempting token refresh`);
        const refreshed = await deps.onAuth401(accessToken);
        if (refreshed) {
            debug(`[bridge:api] ${context}: Token refreshed, retrying request`);
            const newToken = resolveAuth();
            const retryResponse = await fn(newToken);
            if (retryResponse.status !== 401) {
                return retryResponse;
            }
            debug(`[bridge:api] ${context}: Retry after refresh also got 401`);
        }
        else {
            debug(`[bridge:api] ${context}: Token refresh failed`);
        }
        // Refresh failed — return 401 for handleErrorStatus to throw
        return response;
    }
    return {
        async registerBridgeEnvironment(config) {
            debug(`[bridge:api] POST /v1/environments/bridge bridgeId=${config.bridgeId}`);
            const response = await withOAuthRetry((token) => axios.post(`${deps.baseUrl}/v1/environments/bridge`, {
                machine_name: config.machineName,
                directory: config.dir,
                branch: config.branch,
                git_repo_url: config.gitRepoUrl,
                // Advertise session capacity so claude.ai/code can show
                // "2/4 sessions" badges and only block the picker when
                // actually at capacity. Backends that don't yet accept
                // this field will silently ignore it.
                max_sessions: config.maxSessions,
                // worker_type lets claude.ai filter environments by origin
                // (e.g. assistant picker only shows assistant-mode workers).
                // Desktop cowork app sends "cowork"; we send a distinct value.
                metadata: { worker_type: config.workerType },
                // Idempotent re-registration: if we have a backend-issued
                // environment_id from a prior session (--session-id resume),
                // send it back so the backend reattaches instead of creating
                // a new env. The backend may still hand back a fresh ID if
                // the old one expired — callers must compare the response.
                ...(config.reuseEnvironmentId && {
                    environment_id: config.reuseEnvironmentId,
                }),
            }, {
                headers: getHeaders(token),
                timeout: 15_000,
                validateStatus: status => status < 500,
            }), 'Registration');
            handleErrorStatus(response.status, response.data, 'Registration');
            debug(`[bridge:api] POST /v1/environments/bridge -> ${response.status} environment_id=${response.data.environment_id}`);
            debug(`[bridge:api] >>> ${debugBody({ machine_name: config.machineName, directory: config.dir, branch: config.branch, git_repo_url: config.gitRepoUrl, max_sessions: config.maxSessions, metadata: { worker_type: config.workerType } })}`);
            debug(`[bridge:api] <<< ${debugBody(response.data)}`);
            return response.data;
        },
        async pollForWork(environmentId, environmentSecret, signal, reclaimOlderThanMs) {
            validateBridgeId(environmentId, 'environmentId');
            // Save and reset so errors break the "consecutive empty" streak.
            // Restored below when the response is truly empty.
            const prevEmptyPolls = consecutiveEmptyPolls;
            consecutiveEmptyPolls = 0;
            const response = await axios.get(`${deps.baseUrl}/v1/environments/${environmentId}/work/poll`, {
                headers: getHeaders(environmentSecret),
                params: reclaimOlderThanMs !== undefined
                    ? { reclaim_older_than_ms: reclaimOlderThanMs }
                    : undefined,
                timeout: 10_000,
                signal,
                validateStatus: status => status < 500,
            });
            handleErrorStatus(response.status, response.data, 'Poll');
            // Empty body or null = no work available
            if (!response.data) {
                consecutiveEmptyPolls = prevEmptyPolls + 1;
                if (consecutiveEmptyPolls === 1 ||
                    consecutiveEmptyPolls % EMPTY_POLL_LOG_INTERVAL === 0) {
                    debug(`[bridge:api] GET .../work/poll -> ${response.status} (no work, ${consecutiveEmptyPolls} consecutive empty polls)`);
                }
                return null;
            }
            debug(`[bridge:api] GET .../work/poll -> ${response.status} workId=${response.data.id} type=${response.data.data?.type}${response.data.data?.id ? ` sessionId=${response.data.data.id}` : ''}`);
            debug(`[bridge:api] <<< ${debugBody(response.data)}`);
            return response.data;
        },
        async acknowledgeWork(environmentId, workId, sessionToken) {
            validateBridgeId(environmentId, 'environmentId');
            validateBridgeId(workId, 'workId');
            debug(`[bridge:api] POST .../work/${workId}/ack`);
            const response = await axios.post(`${deps.baseUrl}/v1/environments/${environmentId}/work/${workId}/ack`, {}, {
                headers: getHeaders(sessionToken),
                timeout: 10_000,
                validateStatus: s => s < 500,
            });
            handleErrorStatus(response.status, response.data, 'Acknowledge');
            debug(`[bridge:api] POST .../work/${workId}/ack -> ${response.status}`);
        },
        async stopWork(environmentId, workId, force) {
            validateBridgeId(environmentId, 'environmentId');
            validateBridgeId(workId, 'workId');
            debug(`[bridge:api] POST .../work/${workId}/stop force=${force}`);
            const response = await withOAuthRetry((token) => axios.post(`${deps.baseUrl}/v1/environments/${environmentId}/work/${workId}/stop`, { force }, {
                headers: getHeaders(token),
                timeout: 10_000,
                validateStatus: s => s < 500,
            }), 'StopWork');
            handleErrorStatus(response.status, response.data, 'StopWork');
            debug(`[bridge:api] POST .../work/${workId}/stop -> ${response.status}`);
        },
        async deregisterEnvironment(environmentId) {
            validateBridgeId(environmentId, 'environmentId');
            debug(`[bridge:api] DELETE /v1/environments/bridge/${environmentId}`);
            const response = await withOAuthRetry((token) => axios.delete(`${deps.baseUrl}/v1/environments/bridge/${environmentId}`, {
                headers: getHeaders(token),
                timeout: 10_000,
                validateStatus: s => s < 500,
            }), 'Deregister');
            handleErrorStatus(response.status, response.data, 'Deregister');
            debug(`[bridge:api] DELETE /v1/environments/bridge/${environmentId} -> ${response.status}`);
        },
        async archiveSession(sessionId) {
            validateBridgeId(sessionId, 'sessionId');
            debug(`[bridge:api] POST /v1/sessions/${sessionId}/archive`);
            const response = await withOAuthRetry((token) => axios.post(`${deps.baseUrl}/v1/sessions/${sessionId}/archive`, {}, {
                headers: getHeaders(token),
                timeout: 10_000,
                validateStatus: s => s < 500,
            }), 'ArchiveSession');
            // 409 = already archived (idempotent, not an error)
            if (response.status === 409) {
                debug(`[bridge:api] POST /v1/sessions/${sessionId}/archive -> 409 (already archived)`);
                return;
            }
            handleErrorStatus(response.status, response.data, 'ArchiveSession');
            debug(`[bridge:api] POST /v1/sessions/${sessionId}/archive -> ${response.status}`);
        },
        async reconnectSession(environmentId, sessionId) {
            validateBridgeId(environmentId, 'environmentId');
            validateBridgeId(sessionId, 'sessionId');
            debug(`[bridge:api] POST /v1/environments/${environmentId}/bridge/reconnect session_id=${sessionId}`);
            const response = await withOAuthRetry((token) => axios.post(`${deps.baseUrl}/v1/environments/${environmentId}/bridge/reconnect`, { session_id: sessionId }, {
                headers: getHeaders(token),
                timeout: 10_000,
                validateStatus: s => s < 500,
            }), 'ReconnectSession');
            handleErrorStatus(response.status, response.data, 'ReconnectSession');
            debug(`[bridge:api] POST .../bridge/reconnect -> ${response.status}`);
        },
        async heartbeatWork(environmentId, workId, sessionToken) {
            validateBridgeId(environmentId, 'environmentId');
            validateBridgeId(workId, 'workId');
            debug(`[bridge:api] POST .../work/${workId}/heartbeat`);
            const response = await axios.post(`${deps.baseUrl}/v1/environments/${environmentId}/work/${workId}/heartbeat`, {}, {
                headers: getHeaders(sessionToken),
                timeout: 10_000,
                validateStatus: s => s < 500,
            });
            handleErrorStatus(response.status, response.data, 'Heartbeat');
            debug(`[bridge:api] POST .../work/${workId}/heartbeat -> ${response.status} lease_extended=${response.data.lease_extended} state=${response.data.state}`);
            return response.data;
        },
        async sendPermissionResponseEvent(sessionId, event, sessionToken) {
            validateBridgeId(sessionId, 'sessionId');
            debug(`[bridge:api] POST /v1/sessions/${sessionId}/events type=${event.type}`);
            const response = await axios.post(`${deps.baseUrl}/v1/sessions/${sessionId}/events`, { events: [event] }, {
                headers: getHeaders(sessionToken),
                timeout: 10_000,
                validateStatus: s => s < 500,
            });
            handleErrorStatus(response.status, response.data, 'SendPermissionResponseEvent');
            debug(`[bridge:api] POST /v1/sessions/${sessionId}/events -> ${response.status}`);
            debug(`[bridge:api] >>> ${debugBody({ events: [event] })}`);
            debug(`[bridge:api] <<< ${debugBody(response.data)}`);
        },
    };
}
function handleErrorStatus(status, data, context) {
    if (status === 200 || status === 204) {
        return;
    }
    const detail = extractErrorDetail(data);
    const errorType = extractErrorTypeFromData(data);
    switch (status) {
        case 401:
            throw new BridgeFatalError(`${context}: Authentication failed (401)${detail ? `: ${detail}` : ''}. ${BRIDGE_LOGIN_INSTRUCTION}`, 401, errorType);
        case 403:
            throw new BridgeFatalError(isExpiredErrorType(errorType)
                ? 'Remote Control session has expired. Please restart with `claude remote-control` or /remote-control.'
                : `${context}: Access denied (403)${detail ? `: ${detail}` : ''}. Check your organization permissions.`, 403, errorType);
        case 404:
            throw new BridgeFatalError(detail ??
                `${context}: Not found (404). Remote Control may not be available for this organization.`, 404, errorType);
        case 410:
            throw new BridgeFatalError(detail ??
                'Remote Control session has expired. Please restart with `claude remote-control` or /remote-control.', 410, errorType ?? 'environment_expired');
        case 429:
            throw new Error(`${context}: Rate limited (429). Polling too frequently.`);
        default:
            throw new Error(`${context}: Failed with status ${status}${detail ? `: ${detail}` : ''}`);
    }
}
/** Check whether an error type string indicates a session/environment expiry. */
export function isExpiredErrorType(errorType) {
    if (!errorType) {
        return false;
    }
    return errorType.includes('expired') || errorType.includes('lifetime');
}
/**
 * Check whether a BridgeFatalError is a suppressible 403 permission error.
 * These are 403 errors for scopes like 'external_poll_sessions' or operations
 * like StopWork that fail because the user's role lacks 'environments:manage'.
 * They don't affect core functionality and shouldn't be shown to users.
 */
export function isSuppressible403(err) {
    if (err.status !== 403) {
        return false;
    }
    return (err.message.includes('external_poll_sessions') ||
        err.message.includes('environments:manage'));
}
function extractErrorTypeFromData(data) {
    if (data && typeof data === 'object') {
        if ('error' in data &&
            data.error &&
            typeof data.error === 'object' &&
            'type' in data.error &&
            typeof data.error.type === 'string') {
            return data.error.type;
        }
    }
    return undefined;
}
