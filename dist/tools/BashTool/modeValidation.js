import { splitCommand_DEPRECATED } from '../../utils/bash/commands.js';
const ACCEPT_EDITS_ALLOWED_COMMANDS = [
    'mkdir',
    'touch',
    'rm',
    'rmdir',
    'mv',
    'cp',
    'sed',
];
function isFilesystemCommand(command) {
    return ACCEPT_EDITS_ALLOWED_COMMANDS.includes(command);
}
function validateCommandForMode(cmd, toolPermissionContext) {
    const trimmedCmd = cmd.trim();
    const [baseCmd] = trimmedCmd.split(/\s+/);
    if (!baseCmd) {
        return {
            behavior: 'passthrough',
            message: 'Base command not found',
        };
    }
    // In Accept Edits mode, auto-allow filesystem operations
    if (toolPermissionContext.mode === 'acceptEdits' &&
        isFilesystemCommand(baseCmd)) {
        return {
            behavior: 'allow',
            updatedInput: { command: cmd },
            decisionReason: {
                type: 'mode',
                mode: 'acceptEdits',
            },
        };
    }
    return {
        behavior: 'passthrough',
        message: `No mode-specific handling for '${baseCmd}' in ${toolPermissionContext.mode} mode`,
    };
}
/**
 * Checks if commands should be handled differently based on the current permission mode
 *
 * This is the main entry point for mode-based permission logic.
 * Currently handles Accept Edits mode for filesystem commands,
 * but designed to be extended for other modes.
 *
 * @param input - The bash command input
 * @param toolPermissionContext - Context containing mode and permissions
 * @returns
 * - 'allow' if the current mode permits auto-approval
 * - 'ask' if the command needs approval in current mode
 * - 'passthrough' if no mode-specific handling applies
 */
export function checkPermissionMode(input, toolPermissionContext) {
    // Skip if in bypass mode (handled elsewhere)
    if (toolPermissionContext.mode === 'bypassPermissions') {
        return {
            behavior: 'passthrough',
            message: 'Bypass mode is handled in main permission flow',
        };
    }
    // Skip if in dontAsk mode (handled in main permission flow)
    if (toolPermissionContext.mode === 'dontAsk') {
        return {
            behavior: 'passthrough',
            message: 'DontAsk mode is handled in main permission flow',
        };
    }
    const commands = splitCommand_DEPRECATED(input.command);
    // Check each subcommand
    for (const cmd of commands) {
        const result = validateCommandForMode(cmd, toolPermissionContext);
        // If any command triggers mode-specific behavior, return that result
        if (result.behavior !== 'passthrough') {
            return result;
        }
    }
    // No mode-specific handling needed
    return {
        behavior: 'passthrough',
        message: 'No mode-specific validation required',
    };
}
export function getAutoAllowedCommands(mode) {
    return mode === 'acceptEdits' ? ACCEPT_EDITS_ALLOWED_COMMANDS : [];
}
