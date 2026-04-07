import { getClaudeAiBaseUrl, getRemoteSessionUrl, } from '../constants/product.js';
import { stringWidth } from '../ink/stringWidth.js';
import { formatDuration, truncateToWidth } from '../utils/format.js';
import { getGraphemeSegmenter } from '../utils/intl.js';
/** How long a tool activity line stays visible after last tool_start (ms). */
export const TOOL_DISPLAY_EXPIRY_MS = 30_000;
/** Interval for the shimmer animation tick (ms). */
export const SHIMMER_INTERVAL_MS = 150;
export function timestamp() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    const s = String(now.getSeconds()).padStart(2, '0');
    return `${h}:${m}:${s}`;
}
export { formatDuration, truncateToWidth as truncatePrompt };
/** Abbreviate a tool activity summary for the trail display. */
export function abbreviateActivity(summary) {
    return truncateToWidth(summary, 30);
}
/** Build the connect URL shown when the bridge is idle. */
export function buildBridgeConnectUrl(environmentId, ingressUrl) {
    const baseUrl = getClaudeAiBaseUrl(undefined, ingressUrl);
    return `${baseUrl}/code?bridge=${environmentId}`;
}
/**
 * Build the session URL shown when a session is attached. Delegates to
 * getRemoteSessionUrl for the cse_→session_ prefix translation, then appends
 * the v1-specific ?bridge={environmentId} query.
 */
export function buildBridgeSessionUrl(sessionId, environmentId, ingressUrl) {
    return `${getRemoteSessionUrl(sessionId, ingressUrl)}?bridge=${environmentId}`;
}
/** Compute the glimmer index for a reverse-sweep shimmer animation. */
export function computeGlimmerIndex(tick, messageWidth) {
    const cycleLength = messageWidth + 20;
    return messageWidth + 10 - (tick % cycleLength);
}
/**
 * Split text into three segments by visual column position for shimmer rendering.
 *
 * Uses grapheme segmentation and `stringWidth` so the split is correct for
 * multi-byte characters, emoji, and CJK glyphs.
 *
 * Returns `{ before, shimmer, after }` strings. Both renderers (chalk in
 * bridgeUI.ts and React/Ink in bridge.tsx) apply their own coloring to
 * these segments.
 */
export function computeShimmerSegments(text, glimmerIndex) {
    const messageWidth = stringWidth(text);
    const shimmerStart = glimmerIndex - 1;
    const shimmerEnd = glimmerIndex + 1;
    // When shimmer is offscreen, return all text as "before"
    if (shimmerStart >= messageWidth || shimmerEnd < 0) {
        return { before: text, shimmer: '', after: '' };
    }
    // Split into at most 3 segments by visual column position
    const clampedStart = Math.max(0, shimmerStart);
    let colPos = 0;
    let before = '';
    let shimmer = '';
    let after = '';
    for (const { segment } of getGraphemeSegmenter().segment(text)) {
        const segWidth = stringWidth(segment);
        if (colPos + segWidth <= clampedStart) {
            before += segment;
        }
        else if (colPos > shimmerEnd) {
            after += segment;
        }
        else {
            shimmer += segment;
        }
        colPos += segWidth;
    }
    return { before, shimmer, after };
}
/** Derive a status label and color from the bridge connection state. */
export function getBridgeStatus({ error, connected, sessionActive, reconnecting, }) {
    if (error)
        return { label: 'Remote Control failed', color: 'error' };
    if (reconnecting)
        return { label: 'Remote Control reconnecting', color: 'warning' };
    if (sessionActive || connected)
        return { label: 'Remote Control active', color: 'success' };
    return { label: 'Remote Control connecting\u2026', color: 'warning' };
}
/** Footer text shown when bridge is idle (Ready state). */
export function buildIdleFooterText(url) {
    return `Code everywhere with the Claude app or ${url}`;
}
/** Footer text shown when a session is active (Connected state). */
export function buildActiveFooterText(url) {
    return `Continue coding in the Claude app or ${url}`;
}
/** Footer text shown when the bridge has failed. */
export const FAILED_FOOTER_TEXT = 'Something went wrong, please try again';
/**
 * Wrap text in an OSC 8 terminal hyperlink. Zero visual width for layout purposes.
 * strip-ansi (used by stringWidth) correctly strips these sequences, so
 * countVisualLines in bridgeUI.ts remains accurate.
 */
export function wrapWithOsc8Link(text, url) {
    return `\x1b]8;;${url}\x07${text}\x1b]8;;\x07`;
}
