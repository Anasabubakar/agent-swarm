import { getSettings_DEPRECATED } from '../../utils/settings/settings.js';
import { logEvent, } from '../analytics/index.js';
import { getSessionsSinceLastShown, recordTipShown } from './tipHistory.js';
import { getRelevantTips } from './tipRegistry.js';
export function selectTipWithLongestTimeSinceShown(availableTips) {
    if (availableTips.length === 0) {
        return undefined;
    }
    if (availableTips.length === 1) {
        return availableTips[0];
    }
    // Sort tips by sessions since last shown (descending) and take the first one
    // This is the tip that hasn't been shown for the longest time
    const tipsWithSessions = availableTips.map(tip => ({
        tip,
        sessions: getSessionsSinceLastShown(tip.id),
    }));
    tipsWithSessions.sort((a, b) => b.sessions - a.sessions);
    return tipsWithSessions[0]?.tip;
}
export async function getTipToShowOnSpinner(context) {
    // Check if tips are disabled (default to true if not set)
    if (getSettings_DEPRECATED().spinnerTipsEnabled === false) {
        return undefined;
    }
    const tips = await getRelevantTips(context);
    if (tips.length === 0) {
        return undefined;
    }
    return selectTipWithLongestTimeSinceShown(tips);
}
export function recordShownTip(tip) {
    // Record in history
    recordTipShown(tip.id);
    // Log event for analytics
    logEvent('tengu_tip_shown', {
        tipIdLength: tip.id,
        cooldownSessions: tip.cooldownSessions,
    });
}
