let prewarmed = false;
/**
 * Pre-warm the native module by loading it in advance.
 * Call this early to avoid delay on first use.
 */
export function prewarmModifiers() {
    if (prewarmed || process.platform !== 'darwin') {
        return;
    }
    prewarmed = true;
    // Load module in background
    try {
        // eslint-disable-next-line @typescript-eslint/no-require-imports
        const { prewarm } = require('modifiers-napi');
        prewarm();
    }
    catch {
        // Ignore errors during prewarm
    }
}
/**
 * Check if a specific modifier key is currently pressed (synchronous).
 */
export function isModifierPressed(modifier) {
    if (process.platform !== 'darwin') {
        return false;
    }
    // Dynamic import to avoid loading native module at top level
    const { isModifierPressed: nativeIsModifierPressed } = 
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    require('modifiers-napi');
    return nativeIsModifierPressed(modifier);
}
