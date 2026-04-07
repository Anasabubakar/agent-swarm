// biome-ignore-all assist/source/organizeImports: ANT-ONLY import markers must not be reordered
import { z } from 'zod/v4';
import { lazySchema } from '../utils/lazySchema.js';
import { HOOK_EVENTS, } from 'src/entrypoints/agentSdkTypes.js';
import { permissionBehaviorSchema } from 'src/utils/permissions/PermissionRule.js';
import { permissionUpdateSchema } from 'src/utils/permissions/PermissionUpdateSchema.js';
export function isHookEvent(value) {
    return HOOK_EVENTS.includes(value);
}
// Prompt elicitation protocol types. The `prompt` key acts as discriminator
// (mirroring the {async:true} pattern), with the id as its value.
export const promptRequestSchema = lazySchema(() => z.object({
    prompt: z.string(), // request id
    message: z.string(),
    options: z.array(z.object({
        key: z.string(),
        label: z.string(),
        description: z.string().optional(),
    })),
}));
// Sync hook response schema
export const syncHookResponseSchema = lazySchema(() => z.object({
    continue: z
        .boolean()
        .describe('Whether Claude should continue after hook (default: true)')
        .optional(),
    suppressOutput: z
        .boolean()
        .describe('Hide stdout from transcript (default: false)')
        .optional(),
    stopReason: z
        .string()
        .describe('Message shown when continue is false')
        .optional(),
    decision: z.enum(['approve', 'block']).optional(),
    reason: z.string().describe('Explanation for the decision').optional(),
    systemMessage: z
        .string()
        .describe('Warning message shown to the user')
        .optional(),
    hookSpecificOutput: z
        .union([
        z.object({
            hookEventName: z.literal('PreToolUse'),
            permissionDecision: permissionBehaviorSchema().optional(),
            permissionDecisionReason: z.string().optional(),
            updatedInput: z.record(z.string(), z.unknown()).optional(),
            additionalContext: z.string().optional(),
        }),
        z.object({
            hookEventName: z.literal('UserPromptSubmit'),
            additionalContext: z.string().optional(),
        }),
        z.object({
            hookEventName: z.literal('SessionStart'),
            additionalContext: z.string().optional(),
            initialUserMessage: z.string().optional(),
            watchPaths: z
                .array(z.string())
                .describe('Absolute paths to watch for FileChanged hooks')
                .optional(),
        }),
        z.object({
            hookEventName: z.literal('Setup'),
            additionalContext: z.string().optional(),
        }),
        z.object({
            hookEventName: z.literal('SubagentStart'),
            additionalContext: z.string().optional(),
        }),
        z.object({
            hookEventName: z.literal('PostToolUse'),
            additionalContext: z.string().optional(),
            updatedMCPToolOutput: z
                .unknown()
                .describe('Updates the output for MCP tools')
                .optional(),
        }),
        z.object({
            hookEventName: z.literal('PostToolUseFailure'),
            additionalContext: z.string().optional(),
        }),
        z.object({
            hookEventName: z.literal('PermissionDenied'),
            retry: z.boolean().optional(),
        }),
        z.object({
            hookEventName: z.literal('Notification'),
            additionalContext: z.string().optional(),
        }),
        z.object({
            hookEventName: z.literal('PermissionRequest'),
            decision: z.union([
                z.object({
                    behavior: z.literal('allow'),
                    updatedInput: z.record(z.string(), z.unknown()).optional(),
                    updatedPermissions: z.array(permissionUpdateSchema()).optional(),
                }),
                z.object({
                    behavior: z.literal('deny'),
                    message: z.string().optional(),
                    interrupt: z.boolean().optional(),
                }),
            ]),
        }),
        z.object({
            hookEventName: z.literal('Elicitation'),
            action: z.enum(['accept', 'decline', 'cancel']).optional(),
            content: z.record(z.string(), z.unknown()).optional(),
        }),
        z.object({
            hookEventName: z.literal('ElicitationResult'),
            action: z.enum(['accept', 'decline', 'cancel']).optional(),
            content: z.record(z.string(), z.unknown()).optional(),
        }),
        z.object({
            hookEventName: z.literal('CwdChanged'),
            watchPaths: z
                .array(z.string())
                .describe('Absolute paths to watch for FileChanged hooks')
                .optional(),
        }),
        z.object({
            hookEventName: z.literal('FileChanged'),
            watchPaths: z
                .array(z.string())
                .describe('Absolute paths to watch for FileChanged hooks')
                .optional(),
        }),
        z.object({
            hookEventName: z.literal('WorktreeCreate'),
            worktreePath: z.string(),
        }),
    ])
        .optional(),
}));
// Zod schema for hook JSON output validation
export const hookJSONOutputSchema = lazySchema(() => {
    // Async hook response schema
    const asyncHookResponseSchema = z.object({
        async: z.literal(true),
        asyncTimeout: z.number().optional(),
    });
    return z.union([asyncHookResponseSchema, syncHookResponseSchema()]);
});
// Type guard function to check if response is sync
export function isSyncHookJSONOutput(json) {
    return !('async' in json && json.async === true);
}
// Type guard function to check if response is async
export function isAsyncHookJSONOutput(json) {
    return 'async' in json && json.async === true;
}
