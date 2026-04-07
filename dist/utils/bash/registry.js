import { memoizeWithLRU } from '../memoize.js';
import specs from './specs/index.js';
export async function loadFigSpec(command) {
    if (!command || command.includes('/') || command.includes('\\'))
        return null;
    if (command.includes('..'))
        return null;
    if (command.startsWith('-') && command !== '-')
        return null;
    try {
        const module = await import(`@withfig/autocomplete/build/${command}.js`);
        return module.default || module;
    }
    catch {
        return null;
    }
}
export const getCommandSpec = memoizeWithLRU(async (command) => {
    const spec = specs.find(s => s.name === command) ||
        (await loadFigSpec(command)) ||
        null;
    return spec;
}, (command) => command);
