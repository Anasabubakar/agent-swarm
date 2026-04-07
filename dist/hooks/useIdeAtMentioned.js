import { useEffect, useRef } from 'react';
import { logError } from 'src/utils/log.js';
import { z } from 'zod/v4';
import { getConnectedIdeClient } from '../utils/ide.js';
import { lazySchema } from '../utils/lazySchema.js';
const NOTIFICATION_METHOD = 'at_mentioned';
const AtMentionedSchema = lazySchema(() => z.object({
    method: z.literal(NOTIFICATION_METHOD),
    params: z.object({
        filePath: z.string(),
        lineStart: z.number().optional(),
        lineEnd: z.number().optional(),
    }),
}));
/**
 * A hook that tracks IDE at-mention notifications by directly registering
 * with MCP client notification handlers,
 */
export function useIdeAtMentioned(mcpClients, onAtMentioned) {
    const ideClientRef = useRef(undefined);
    useEffect(() => {
        // Find the IDE client from the MCP clients list
        const ideClient = getConnectedIdeClient(mcpClients);
        if (ideClientRef.current !== ideClient) {
            ideClientRef.current = ideClient;
        }
        // If we found a connected IDE client, register our handler
        if (ideClient) {
            ideClient.client.setNotificationHandler(AtMentionedSchema(), notification => {
                if (ideClientRef.current !== ideClient) {
                    return;
                }
                try {
                    const data = notification.params;
                    // Adjust line numbers to be 1-based instead of 0-based
                    const lineStart = data.lineStart !== undefined ? data.lineStart + 1 : undefined;
                    const lineEnd = data.lineEnd !== undefined ? data.lineEnd + 1 : undefined;
                    onAtMentioned({
                        filePath: data.filePath,
                        lineStart: lineStart,
                        lineEnd: lineEnd,
                    });
                }
                catch (error) {
                    logError(error);
                }
            });
        }
        // No cleanup needed as MCP clients manage their own lifecycle
    }, [mcpClients, onAtMentioned]);
}
