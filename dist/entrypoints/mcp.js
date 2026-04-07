import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema, } from '@modelcontextprotocol/sdk/types.js';
import { getDefaultAppState } from 'src/state/AppStateStore.js';
import review from '../commands/review.js';
import { findToolByName, getEmptyToolPermissionContext, } from '../Tool.js';
import { getTools } from '../tools.js';
import { createAbortController } from '../utils/abortController.js';
import { createFileStateCacheWithSizeLimit } from '../utils/fileStateCache.js';
import { logError } from '../utils/log.js';
import { createAssistantMessage } from '../utils/messages.js';
import { getMainLoopModel } from '../utils/model/model.js';
import { hasPermissionsToUseTool } from '../utils/permissions/permissions.js';
import { setCwd } from '../utils/Shell.js';
import { jsonStringify } from '../utils/slowOperations.js';
import { getErrorParts } from '../utils/toolErrors.js';
import { zodToJsonSchema } from '../utils/zodToJsonSchema.js';
const MCP_COMMANDS = [review];
export async function startMCPServer(cwd, debug, verbose) {
    // Use size-limited LRU cache for readFileState to prevent unbounded memory growth
    // 100 files and 25MB limit should be sufficient for MCP server operations
    const READ_FILE_STATE_CACHE_SIZE = 100;
    const readFileStateCache = createFileStateCacheWithSizeLimit(READ_FILE_STATE_CACHE_SIZE);
    setCwd(cwd);
    const server = new Server({
        name: 'claude/tengu',
        version: MACRO.VERSION,
    }, {
        capabilities: {
            tools: {},
        },
    });
    server.setRequestHandler(ListToolsRequestSchema, async () => {
        // TODO: Also re-expose any MCP tools
        const toolPermissionContext = getEmptyToolPermissionContext();
        const tools = getTools(toolPermissionContext);
        return {
            tools: await Promise.all(tools.map(async (tool) => {
                let outputSchema;
                if (tool.outputSchema) {
                    const convertedSchema = zodToJsonSchema(tool.outputSchema);
                    // MCP SDK requires outputSchema to have type: "object" at root level
                    // Skip schemas with anyOf/oneOf at root (from z.union, z.discriminatedUnion, etc.)
                    // See: https://github.com/anthropics/claude-code/issues/8014
                    if (typeof convertedSchema === 'object' &&
                        convertedSchema !== null &&
                        'type' in convertedSchema &&
                        convertedSchema.type === 'object') {
                        outputSchema = convertedSchema;
                    }
                }
                return {
                    ...tool,
                    description: await tool.prompt({
                        getToolPermissionContext: async () => toolPermissionContext,
                        tools,
                        agents: [],
                    }),
                    inputSchema: zodToJsonSchema(tool.inputSchema),
                    outputSchema,
                };
            })),
        };
    });
    server.setRequestHandler(CallToolRequestSchema, async ({ params: { name, arguments: args } }) => {
        const toolPermissionContext = getEmptyToolPermissionContext();
        // TODO: Also re-expose any MCP tools
        const tools = getTools(toolPermissionContext);
        const tool = findToolByName(tools, name);
        if (!tool) {
            throw new Error(`Tool ${name} not found`);
        }
        // Assume MCP servers do not read messages separately from the tool
        // call arguments.
        const toolUseContext = {
            abortController: createAbortController(),
            options: {
                commands: MCP_COMMANDS,
                tools,
                mainLoopModel: getMainLoopModel(),
                thinkingConfig: { type: 'disabled' },
                mcpClients: [],
                mcpResources: {},
                isNonInteractiveSession: true,
                debug,
                verbose,
                agentDefinitions: { activeAgents: [], allAgents: [] },
            },
            getAppState: () => getDefaultAppState(),
            setAppState: () => { },
            messages: [],
            readFileState: readFileStateCache,
            setInProgressToolUseIDs: () => { },
            setResponseLength: () => { },
            updateFileHistoryState: () => { },
            updateAttributionState: () => { },
        };
        // TODO: validate input types with zod
        try {
            if (!tool.isEnabled()) {
                throw new Error(`Tool ${name} is not enabled`);
            }
            const validationResult = await tool.validateInput?.(args ?? {}, toolUseContext);
            if (validationResult && !validationResult.result) {
                throw new Error(`Tool ${name} input is invalid: ${validationResult.message}`);
            }
            const finalResult = await tool.call((args ?? {}), toolUseContext, hasPermissionsToUseTool, createAssistantMessage({
                content: [],
            }));
            return {
                content: [
                    {
                        type: 'text',
                        text: typeof finalResult === 'string'
                            ? finalResult
                            : jsonStringify(finalResult.data),
                    },
                ],
            };
        }
        catch (error) {
            logError(error);
            const parts = error instanceof Error ? getErrorParts(error) : [String(error)];
            const errorText = parts.filter(Boolean).join('\n').trim() || 'Error';
            return {
                isError: true,
                content: [
                    {
                        type: 'text',
                        text: errorText,
                    },
                ],
            };
        }
    });
    async function runServer() {
        const transport = new StdioServerTransport();
        await server.connect(transport);
    }
    return await runServer();
}
