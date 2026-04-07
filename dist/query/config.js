import { getSessionId } from '../bootstrap/state.js';
import { checkStatsigFeatureGate_CACHED_MAY_BE_STALE } from '../services/analytics/growthbook.js';
import { isEnvTruthy } from '../utils/envUtils.js';
export function buildQueryConfig() {
    return {
        sessionId: getSessionId(),
        gates: {
            streamingToolExecution: checkStatsigFeatureGate_CACHED_MAY_BE_STALE('tengu_streaming_tool_execution2'),
            emitToolUseSummaries: isEnvTruthy(process.env.CLAUDE_CODE_EMIT_TOOL_USE_SUMMARIES),
            isAnt: process.env.USER_TYPE === 'ant',
            // Inlined from fastMode.ts to avoid pulling its heavy module graph
            // (axios, settings, auth, model, oauth, config) into test shards that
            // didn't previously load it — changes init order and breaks unrelated tests.
            fastModeEnabled: !isEnvTruthy(process.env.CLAUDE_CODE_DISABLE_FAST_MODE),
        },
    };
}
