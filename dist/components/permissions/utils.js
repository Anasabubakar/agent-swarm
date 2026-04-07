import { getHostPlatformForAnalytics } from '../../utils/env.js';
import { logUnaryEvent } from '../../utils/unaryLogging.js';
export function logUnaryPermissionEvent(completion_type, { assistantMessage: { message: { id: message_id }, }, }, event, hasFeedback) {
    void logUnaryEvent({
        completion_type,
        event,
        metadata: {
            language_name: 'none',
            message_id,
            platform: getHostPlatformForAnalytics(),
            hasFeedback: hasFeedback ?? false,
        },
    });
}
