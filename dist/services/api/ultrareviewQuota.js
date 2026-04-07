import axios from 'axios';
import { getOauthConfig } from '../../constants/oauth.js';
import { isClaudeAISubscriber } from '../../utils/auth.js';
import { logForDebugging } from '../../utils/debug.js';
import { getOAuthHeaders, prepareApiRequest } from '../../utils/teleport/api.js';
/**
 * Peek the ultrareview quota for display and nudge decisions. Consume
 * happens server-side at session creation. Null when not a subscriber or
 * the endpoint errors.
 */
export async function fetchUltrareviewQuota() {
    if (!isClaudeAISubscriber())
        return null;
    try {
        const { accessToken, orgUUID } = await prepareApiRequest();
        const response = await axios.get(`${getOauthConfig().BASE_API_URL}/v1/ultrareview/quota`, {
            headers: {
                ...getOAuthHeaders(accessToken),
                'x-organization-uuid': orgUUID,
            },
            timeout: 5000,
        });
        return response.data;
    }
    catch (error) {
        logForDebugging(`fetchUltrareviewQuota failed: ${error}`);
        return null;
    }
}
