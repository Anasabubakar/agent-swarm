// Constants for timeout values
const DEFAULT_TIMEOUT_MS = 120_000; // 2 minutes
const MAX_TIMEOUT_MS = 600_000; // 10 minutes
/**
 * Get the default timeout for bash operations in milliseconds
 * Checks BASH_DEFAULT_TIMEOUT_MS environment variable or returns 2 minutes default
 * @param env Environment variables to check (defaults to process.env for production use)
 */
export function getDefaultBashTimeoutMs(env = process.env) {
    const envValue = env.BASH_DEFAULT_TIMEOUT_MS;
    if (envValue) {
        const parsed = parseInt(envValue, 10);
        if (!isNaN(parsed) && parsed > 0) {
            return parsed;
        }
    }
    return DEFAULT_TIMEOUT_MS;
}
/**
 * Get the maximum timeout for bash operations in milliseconds
 * Checks BASH_MAX_TIMEOUT_MS environment variable or returns 10 minutes default
 * @param env Environment variables to check (defaults to process.env for production use)
 */
export function getMaxBashTimeoutMs(env = process.env) {
    const envValue = env.BASH_MAX_TIMEOUT_MS;
    if (envValue) {
        const parsed = parseInt(envValue, 10);
        if (!isNaN(parsed) && parsed > 0) {
            // Ensure max is at least as large as default
            return Math.max(parsed, getDefaultBashTimeoutMs(env));
        }
    }
    // Always ensure max is at least as large as default
    return Math.max(MAX_TIMEOUT_MS, getDefaultBashTimeoutMs(env));
}
