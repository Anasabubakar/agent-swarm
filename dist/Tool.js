export const getEmptyToolPermissionContext = () => ({
    mode: 'default',
    additionalWorkingDirectories: new Map(),
    alwaysAllowRules: {},
    alwaysDenyRules: {},
    alwaysAskRules: {},
    isBypassPermissionsModeAvailable: false,
});
export function filterToolProgressMessages(progressMessagesForMessage) {
    return progressMessagesForMessage.filter((msg) => msg.data?.type !== 'hook_progress');
}
/**
 * Checks if a tool matches the given name (primary name or alias).
 */
export function toolMatchesName(tool, name) {
    return tool.name === name || (tool.aliases?.includes(name) ?? false);
}
/**
 * Finds a tool by name or alias from a list of tools.
 */
export function findToolByName(tools, name) {
    return tools.find(t => toolMatchesName(t, name));
}
/**
 * Build a complete `Tool` from a partial definition, filling in safe defaults
 * for the commonly-stubbed methods. All tool exports should go through this so
 * that defaults live in one place and callers never need `?.() ?? default`.
 *
 * Defaults (fail-closed where it matters):
 * - `isEnabled` → `true`
 * - `isConcurrencySafe` → `false` (assume not safe)
 * - `isReadOnly` → `false` (assume writes)
 * - `isDestructive` → `false`
 * - `checkPermissions` → `{ behavior: 'allow', updatedInput }` (defer to general permission system)
 * - `toAutoClassifierInput` → `''` (skip classifier — security-relevant tools must override)
 * - `userFacingName` → `name`
 */
const TOOL_DEFAULTS = {
    isEnabled: () => true,
    isConcurrencySafe: (_input) => false,
    isReadOnly: (_input) => false,
    isDestructive: (_input) => false,
    checkPermissions: (input, _ctx) => Promise.resolve({ behavior: 'allow', updatedInput: input }),
    toAutoClassifierInput: (_input) => '',
    userFacingName: (_input) => '',
};
export function buildTool(def) {
    // The runtime spread is straightforward; the `as` bridges the gap between
    // the structural-any constraint and the precise BuiltTool<D> return. The
    // type semantics are proven by the 0-error typecheck across all 60+ tools.
    return {
        ...TOOL_DEFAULTS,
        userFacingName: () => def.name,
        ...def,
    };
}
