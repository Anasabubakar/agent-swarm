import { getGlobalConfig, saveGlobalConfig } from '../../utils/config.js';
export function recordTipShown(tipId) {
    const numStartups = getGlobalConfig().numStartups;
    saveGlobalConfig(c => {
        const history = c.tipsHistory ?? {};
        if (history[tipId] === numStartups)
            return c;
        return { ...c, tipsHistory: { ...history, [tipId]: numStartups } };
    });
}
export function getSessionsSinceLastShown(tipId) {
    const config = getGlobalConfig();
    const lastShown = config.tipsHistory?.[tipId];
    if (!lastShown)
        return Infinity;
    return config.numStartups - lastShown;
}
