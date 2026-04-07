import { randomUUID } from 'crypto';
import { queryModelWithoutStreaming } from '../../services/api/claude.js';
import { createAbortController } from '../../utils/abortController.js';
import { logError } from '../../utils/log.js';
import { toError } from '../errors.js';
import { extractTextContent } from '../messages.js';
import { asSystemPrompt } from '../systemPromptType.js';
export function createApiQueryHook(config) {
    return async (context) => {
        try {
            const shouldRun = await config.shouldRun(context);
            if (!shouldRun) {
                return;
            }
            const uuid = randomUUID();
            // Build messages using the config's buildMessages function
            const messages = config.buildMessages(context);
            context.queryMessageCount = messages.length;
            // Use config's system prompt if provided, otherwise use context's
            const systemPrompt = config.systemPrompt
                ? asSystemPrompt([config.systemPrompt])
                : context.systemPrompt;
            // Use config's tools preference (defaults to true = use context tools)
            const useTools = config.useTools ?? true;
            const tools = useTools ? context.toolUseContext.options.tools : [];
            // Get model (lazy loaded)
            const model = config.getModel(context);
            // Make API call
            const response = await queryModelWithoutStreaming({
                messages,
                systemPrompt,
                thinkingConfig: { type: 'disabled' },
                tools,
                signal: createAbortController().signal,
                options: {
                    getToolPermissionContext: async () => {
                        const appState = context.toolUseContext.getAppState();
                        return appState.toolPermissionContext;
                    },
                    model,
                    toolChoice: undefined,
                    isNonInteractiveSession: context.toolUseContext.options.isNonInteractiveSession,
                    hasAppendSystemPrompt: !!context.toolUseContext.options.appendSystemPrompt,
                    temperatureOverride: 0,
                    agents: context.toolUseContext.options.agentDefinitions.activeAgents,
                    querySource: config.name,
                    mcpTools: [],
                    agentId: context.toolUseContext.agentId,
                },
            });
            // Parse response
            const content = extractTextContent(response.message.content).trim();
            try {
                const result = config.parseResponse(content, context);
                config.logResult({
                    type: 'success',
                    queryName: config.name,
                    result,
                    messageId: response.message.id,
                    model,
                    uuid,
                }, context);
            }
            catch (error) {
                config.logResult({
                    type: 'error',
                    queryName: config.name,
                    error: error,
                    uuid,
                }, context);
            }
        }
        catch (error) {
            logError(toError(error));
        }
    };
}
