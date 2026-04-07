let builders = null;
export function registerMCPSkillBuilders(b) {
    builders = b;
}
export function getMCPSkillBuilders() {
    if (!builders) {
        throw new Error('MCP skill builders not registered — loadSkillsDir.ts has not been evaluated yet');
    }
    return builders;
}
