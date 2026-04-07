import { getIsNonInteractiveSession } from '../../bootstrap/state.js';
export const context = {
    name: 'context',
    description: 'Visualize current context usage as a colored grid',
    isEnabled: () => !getIsNonInteractiveSession(),
    type: 'local-jsx',
    load: () => import('./context.js'),
};
export const contextNonInteractive = {
    type: 'local',
    name: 'context',
    supportsNonInteractive: true,
    description: 'Show current context usage',
    get isHidden() {
        return !getIsNonInteractiveSession();
    },
    isEnabled() {
        return getIsNonInteractiveSession();
    },
    load: () => import('./context-noninteractive.js'),
};
