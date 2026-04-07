import { env } from '../../utils/env.js';
// Terminals that natively support CSI u / Kitty keyboard protocol
const NATIVE_CSIU_TERMINALS = {
    ghostty: 'Ghostty',
    kitty: 'Kitty',
    'iTerm.app': 'iTerm2',
    WezTerm: 'WezTerm',
};
const terminalSetup = {
    type: 'local-jsx',
    name: 'terminal-setup',
    description: env.terminal === 'Apple_Terminal'
        ? 'Enable Option+Enter key binding for newlines and visual bell'
        : 'Install Shift+Enter key binding for newlines',
    isHidden: env.terminal !== null && env.terminal in NATIVE_CSIU_TERMINALS,
    load: () => import('./terminalSetup.js'),
};
export default terminalSetup;
