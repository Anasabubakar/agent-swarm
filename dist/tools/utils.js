/**
 * Tags user messages with a sourceToolUseID so they stay transient until the tool resolves.
 * This prevents the "is running" message from being duplicated in the UI.
 */
export function tagMessagesWithToolUseID(messages, toolUseID) {
    if (!toolUseID) {
        return messages;
    }
    return messages.map(m => {
        if (m.type === 'user') {
            return { ...m, sourceToolUseID: toolUseID };
        }
        return m;
    });
}
/**
 * Extracts the tool use ID from a parent message for a given tool name.
 */
export function getToolUseIDFromParentMessage(parentMessage, toolName) {
    const toolUseBlock = parentMessage.message.content.find(block => block.type === 'tool_use' && block.name === toolName);
    return toolUseBlock && toolUseBlock.type === 'tool_use'
        ? toolUseBlock.id
        : undefined;
}
