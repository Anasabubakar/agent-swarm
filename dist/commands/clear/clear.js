import { clearConversation } from './conversation.js';
export const call = async (_, context) => {
    await clearConversation(context);
    return { type: 'text', value: '' };
};
