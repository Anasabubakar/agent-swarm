/**
 * Parse `@agent-name message` syntax for direct team member messaging.
 */
export function parseDirectMemberMessage(input) {
    const match = input.match(/^@([\w-]+)\s+(.+)$/s);
    if (!match)
        return null;
    const [, recipientName, message] = match;
    if (!recipientName || !message)
        return null;
    const trimmedMessage = message.trim();
    if (!trimmedMessage)
        return null;
    return { recipientName, message: trimmedMessage };
}
/**
 * Send a direct message to a team member, bypassing the model.
 */
export async function sendDirectMemberMessage(recipientName, message, teamContext, writeToMailbox) {
    if (!teamContext || !writeToMailbox) {
        return { success: false, error: 'no_team_context' };
    }
    // Find team member by name
    const member = Object.values(teamContext.teammates ?? {}).find(t => t.name === recipientName);
    if (!member) {
        return { success: false, error: 'unknown_recipient', recipientName };
    }
    await writeToMailbox(recipientName, {
        from: 'user',
        text: message,
        timestamp: new Date().toISOString(),
    }, teamContext.teamName);
    return { success: true, recipientName };
}
