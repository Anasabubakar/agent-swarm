import { ColorDiff, ColorFile, getSyntaxTheme as nativeGetSyntaxTheme, } from 'color-diff-napi';
import { isEnvDefinedFalsy } from '../../utils/envUtils.js';
/**
 * Returns a static reason why the color-diff module is unavailable, or null if available.
 * 'env' = disabled via CLAUDE_CODE_SYNTAX_HIGHLIGHT
 *
 * The TS port of color-diff works in all build modes, so the only way to
 * disable it is via the env var.
 */
export function getColorModuleUnavailableReason() {
    if (isEnvDefinedFalsy(process.env.CLAUDE_CODE_SYNTAX_HIGHLIGHT)) {
        return 'env';
    }
    return null;
}
export function expectColorDiff() {
    return getColorModuleUnavailableReason() === null ? ColorDiff : null;
}
export function expectColorFile() {
    return getColorModuleUnavailableReason() === null ? ColorFile : null;
}
export function getSyntaxTheme(themeName) {
    return getColorModuleUnavailableReason() === null
        ? nativeGetSyntaxTheme(themeName)
        : null;
}
