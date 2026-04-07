import { isClaudeAISubscriber } from '../../utils/auth.js';
const cost = {
    type: 'local',
    name: 'cost',
    description: 'Show the total cost and duration of the current session',
    get isHidden() {
        // Keep visible for Ants even if they're subscribers (they see cost breakdowns)
        if (process.env.USER_TYPE === 'ant') {
            return false;
        }
        return isClaudeAISubscriber();
    },
    supportsNonInteractive: true,
    load: () => import('./cost.js'),
};
export default cost;
