import { feature } from 'bun:bundle';
import { randomBytes } from 'crypto';
import { unwatchFile, watchFile } from 'fs';
import memoize from 'lodash-es/memoize.js';
import pickBy from 'lodash-es/pickBy.js';
import { basename, dirname, join, resolve } from 'path';
import { getOriginalCwd, getSessionTrustAccepted } from '../bootstrap/state.js';
import { getAutoMemEntrypoint } from '../memdir/paths.js';
import { logEvent } from '../services/analytics/index.js';
import { getCwd } from '../utils/cwd.js';
import { registerCleanup } from './cleanupRegistry.js';
import { logForDebugging } from './debug.js';
import { logForDiagnosticsNoPII } from './diagLogs.js';
import { getGlobalClaudeFile } from './env.js';
import { getClaudeConfigHomeDir, isEnvTruthy } from './envUtils.js';
import { ConfigParseError, getErrnoCode } from './errors.js';
import { writeFileSyncAndFlush_DEPRECATED } from './file.js';
import { getFsImplementation } from './fsOperations.js';
import { findCanonicalGitRoot } from './git.js';
import { safeParseJSON } from './json.js';
import { stripBOM } from './jsonRead.js';
import * as lockfile from './lockfile.js';
import { logError } from './log.js';
import { normalizePathForConfigKey } from './path.js';
import { getEssentialTrafficOnlyReason } from './privacyLevel.js';
import { getManagedFilePath } from './settings/managedPath.js';
/* eslint-disable @typescript-eslint/no-require-imports */
const teamMemPaths = feature('TEAMMEM')
    ? require('../memdir/teamMemPaths.js')
    : null;
const ccrAutoConnect = feature('CCR_AUTO_CONNECT')
    ? require('../bridge/bridgeEnabled.js')
    : null;
import { jsonParse, jsonStringify } from './slowOperations.js';
// Re-entrancy guard: prevents getConfig → logEvent → getGlobalConfig → getConfig
// infinite recursion when the config file is corrupted. logEvent's sampling check
// reads GrowthBook features from the global config, which calls getConfig again.
let insideGetConfig = false;
const DEFAULT_PROJECT_CONFIG = {
    allowedTools: [],
    mcpContextUris: [],
    mcpServers: {},
    enabledMcpjsonServers: [],
    disabledMcpjsonServers: [],
    hasTrustDialogAccepted: false,
    projectOnboardingSeenCount: 0,
    hasClaudeMdExternalIncludesApproved: false,
    hasClaudeMdExternalIncludesWarningShown: false,
};
export { EDITOR_MODES, NOTIFICATION_CHANNELS, } from './configConstants.js';
/**
 * Factory for a fresh default GlobalConfig. Used instead of deep-cloning a
 * shared constant — the nested containers (arrays, records) are all empty, so
 * a factory gives fresh refs at zero clone cost.
 */
function createDefaultGlobalConfig() {
    return {
        numStartups: 0,
        installMethod: undefined,
        autoUpdates: undefined,
        theme: 'dark',
        preferredNotifChannel: 'auto',
        verbose: false,
        editorMode: 'normal',
        autoCompactEnabled: true,
        showTurnDuration: true,
        hasSeenTasksHint: false,
        hasUsedStash: false,
        hasUsedBackgroundTask: false,
        queuedCommandUpHintCount: 0,
        diffTool: 'auto',
        customApiKeyResponses: {
            approved: [],
            rejected: [],
        },
        env: {},
        tipsHistory: {},
        memoryUsageCount: 0,
        promptQueueUseCount: 0,
        btwUseCount: 0,
        todoFeatureEnabled: true,
        showExpandedTodos: false,
        messageIdleNotifThresholdMs: 60000,
        autoConnectIde: false,
        autoInstallIdeExtension: true,
        fileCheckpointingEnabled: true,
        terminalProgressBarEnabled: true,
        cachedStatsigGates: {},
        cachedDynamicConfigs: {},
        cachedGrowthBookFeatures: {},
        respectGitignore: true,
        copyFullResponse: false,
    };
}
export const DEFAULT_GLOBAL_CONFIG = createDefaultGlobalConfig();
export const GLOBAL_CONFIG_KEYS = [
    'apiKeyHelper',
    'installMethod',
    'autoUpdates',
    'autoUpdatesProtectedForNative',
    'theme',
    'verbose',
    'preferredNotifChannel',
    'shiftEnterKeyBindingInstalled',
    'editorMode',
    'hasUsedBackslashReturn',
    'autoCompactEnabled',
    'showTurnDuration',
    'diffTool',
    'env',
    'tipsHistory',
    'todoFeatureEnabled',
    'showExpandedTodos',
    'messageIdleNotifThresholdMs',
    'autoConnectIde',
    'autoInstallIdeExtension',
    'fileCheckpointingEnabled',
    'terminalProgressBarEnabled',
    'showStatusInTerminalTab',
    'taskCompleteNotifEnabled',
    'inputNeededNotifEnabled',
    'agentPushNotifEnabled',
    'respectGitignore',
    'claudeInChromeDefaultEnabled',
    'hasCompletedClaudeInChromeOnboarding',
    'lspRecommendationDisabled',
    'lspRecommendationNeverPlugins',
    'lspRecommendationIgnoredCount',
    'copyFullResponse',
    'copyOnSelect',
    'permissionExplainerEnabled',
    'prStatusFooterEnabled',
    'remoteControlAtStartup',
    'remoteDialogSeen',
];
export function isGlobalConfigKey(key) {
    return GLOBAL_CONFIG_KEYS.includes(key);
}
export const PROJECT_CONFIG_KEYS = [
    'allowedTools',
    'hasTrustDialogAccepted',
    'hasCompletedProjectOnboarding',
];
/**
 * Check if the user has already accepted the trust dialog for the cwd.
 *
 * This function traverses parent directories to check if a parent directory
 * had approval. Accepting trust for a directory implies trust for child
 * directories.
 *
 * @returns Whether the trust dialog has been accepted (i.e. "should not be shown")
 */
let _trustAccepted = false;
export function resetTrustDialogAcceptedCacheForTesting() {
    _trustAccepted = false;
}
export function checkHasTrustDialogAccepted() {
    // Trust only transitions false→true during a session (never the reverse),
    // so once true we can latch it. false is not cached — it gets re-checked
    // on every call so that trust dialog acceptance is picked up mid-session.
    // (lodash memoize doesn't fit here because it would also cache false.)
    return (_trustAccepted ||= computeTrustDialogAccepted());
}
function computeTrustDialogAccepted() {
    // Check session-level trust (for home directory case where trust is not persisted)
    // When running from home dir, trust dialog is shown but acceptance is stored
    // in memory only. This allows hooks and other features to work during the session.
    if (getSessionTrustAccepted()) {
        return true;
    }
    const config = getGlobalConfig();
    // Always check where trust would be saved (git root or original cwd)
    // This is the primary location where trust is persisted by saveCurrentProjectConfig
    const projectPath = getProjectPathForConfig();
    const projectConfig = config.projects?.[projectPath];
    if (projectConfig?.hasTrustDialogAccepted) {
        return true;
    }
    // Now check from current working directory and its parents
    // Normalize paths for consistent JSON key lookup
    let currentPath = normalizePathForConfigKey(getCwd());
    // Traverse all parent directories
    while (true) {
        const pathConfig = config.projects?.[currentPath];
        if (pathConfig?.hasTrustDialogAccepted) {
            return true;
        }
        const parentPath = normalizePathForConfigKey(resolve(currentPath, '..'));
        // Stop if we've reached the root (when parent is same as current)
        if (parentPath === currentPath) {
            break;
        }
        currentPath = parentPath;
    }
    return false;
}
/**
 * Check trust for an arbitrary directory (not the session cwd).
 * Walks up from `dir`, returning true if any ancestor has trust persisted.
 * Unlike checkHasTrustDialogAccepted, this does NOT consult session trust or
 * the memoized project path — use when the target dir differs from cwd (e.g.
 * /assistant installing into a user-typed path).
 */
export function isPathTrusted(dir) {
    const config = getGlobalConfig();
    let currentPath = normalizePathForConfigKey(resolve(dir));
    while (true) {
        if (config.projects?.[currentPath]?.hasTrustDialogAccepted)
            return true;
        const parentPath = normalizePathForConfigKey(resolve(currentPath, '..'));
        if (parentPath === currentPath)
            return false;
        currentPath = parentPath;
    }
}
// We have to put this test code here because Jest doesn't support mocking ES modules :O
const TEST_GLOBAL_CONFIG_FOR_TESTING = {
    ...DEFAULT_GLOBAL_CONFIG,
    autoUpdates: false,
};
const TEST_PROJECT_CONFIG_FOR_TESTING = {
    ...DEFAULT_PROJECT_CONFIG,
};
export function isProjectConfigKey(key) {
    return PROJECT_CONFIG_KEYS.includes(key);
}
/**
 * Detect whether writing `fresh` would lose auth/onboarding state that the
 * in-memory cache still has. This happens when `getConfig` hits a corrupted
 * or truncated file mid-write (from another process or a non-atomic fallback)
 * and returns DEFAULT_GLOBAL_CONFIG. Writing that back would permanently
 * wipe auth. See GH #3117.
 */
function wouldLoseAuthState(fresh) {
    const cached = globalConfigCache.config;
    if (!cached)
        return false;
    const lostOauth = cached.oauthAccount !== undefined && fresh.oauthAccount === undefined;
    const lostOnboarding = cached.hasCompletedOnboarding === true &&
        fresh.hasCompletedOnboarding !== true;
    return lostOauth || lostOnboarding;
}
export function saveGlobalConfig(updater) {
    if (process.env.NODE_ENV === 'test') {
        const config = updater(TEST_GLOBAL_CONFIG_FOR_TESTING);
        // Skip if no changes (same reference returned)
        if (config === TEST_GLOBAL_CONFIG_FOR_TESTING) {
            return;
        }
        Object.assign(TEST_GLOBAL_CONFIG_FOR_TESTING, config);
        return;
    }
    let written = null;
    try {
        const didWrite = saveConfigWithLock(getGlobalClaudeFile(), createDefaultGlobalConfig, current => {
            const config = updater(current);
            // Skip if no changes (same reference returned)
            if (config === current) {
                return current;
            }
            written = {
                ...config,
                projects: removeProjectHistory(current.projects),
            };
            return written;
        });
        // Only write-through if we actually wrote. If the auth-loss guard
        // tripped (or the updater made no changes), the file is untouched and
        // the cache is still valid -- touching it would corrupt the guard.
        if (didWrite && written) {
            writeThroughGlobalConfigCache(written);
        }
    }
    catch (error) {
        logForDebugging(`Failed to save config with lock: ${error}`, {
            level: 'error',
        });
        // Fall back to non-locked version on error. This fallback is a race
        // window: if another process is mid-write (or the file got truncated),
        // getConfig returns defaults. Refuse to write those over a good cached
        // config to avoid wiping auth. See GH #3117.
        const currentConfig = getConfig(getGlobalClaudeFile(), createDefaultGlobalConfig);
        if (wouldLoseAuthState(currentConfig)) {
            logForDebugging('saveGlobalConfig fallback: re-read config is missing auth that cache has; refusing to write. See GH #3117.', { level: 'error' });
            logEvent('tengu_config_auth_loss_prevented', {});
            return;
        }
        const config = updater(currentConfig);
        // Skip if no changes (same reference returned)
        if (config === currentConfig) {
            return;
        }
        written = {
            ...config,
            projects: removeProjectHistory(currentConfig.projects),
        };
        saveConfig(getGlobalClaudeFile(), written, DEFAULT_GLOBAL_CONFIG);
        writeThroughGlobalConfigCache(written);
    }
}
// Cache for global config
let globalConfigCache = {
    config: null,
    mtime: 0,
};
// Tracking for config file operations (telemetry)
let lastReadFileStats = null;
let configCacheHits = 0;
let configCacheMisses = 0;
// Session-total count of actual disk writes to the global config file.
// Exposed for ant-only dev diagnostics (see inc-4552) so anomalous write
// rates surface in the UI before they corrupt ~/.claude.json.
let globalConfigWriteCount = 0;
export function getGlobalConfigWriteCount() {
    return globalConfigWriteCount;
}
export const CONFIG_WRITE_DISPLAY_THRESHOLD = 20;
function reportConfigCacheStats() {
    const total = configCacheHits + configCacheMisses;
    if (total > 0) {
        logEvent('tengu_config_cache_stats', {
            cache_hits: configCacheHits,
            cache_misses: configCacheMisses,
            hit_rate: configCacheHits / total,
        });
    }
    configCacheHits = 0;
    configCacheMisses = 0;
}
// Register cleanup to report cache stats at session end
// eslint-disable-next-line custom-rules/no-top-level-side-effects
registerCleanup(async () => {
    reportConfigCacheStats();
});
/**
 * Migrates old autoUpdaterStatus to new installMethod and autoUpdates fields
 * @internal
 */
function migrateConfigFields(config) {
    // Already migrated
    if (config.installMethod !== undefined) {
        return config;
    }
    // autoUpdaterStatus is removed from the type but may exist in old configs
    const legacy = config;
    // Determine install method and auto-update preference from old field
    let installMethod = 'unknown';
    let autoUpdates = config.autoUpdates ?? true; // Default to enabled unless explicitly disabled
    switch (legacy.autoUpdaterStatus) {
        case 'migrated':
            installMethod = 'local';
            break;
        case 'installed':
            installMethod = 'native';
            break;
        case 'disabled':
            // When disabled, we don't know the install method
            autoUpdates = false;
            break;
        case 'enabled':
        case 'no_permissions':
        case 'not_configured':
            // These imply global installation
            installMethod = 'global';
            break;
        case undefined:
            // No old status, keep defaults
            break;
    }
    return {
        ...config,
        installMethod,
        autoUpdates,
    };
}
/**
 * Removes history field from projects (migrated to history.jsonl)
 * @internal
 */
function removeProjectHistory(projects) {
    if (!projects) {
        return projects;
    }
    const cleanedProjects = {};
    let needsCleaning = false;
    for (const [path, projectConfig] of Object.entries(projects)) {
        // history is removed from the type but may exist in old configs
        const legacy = projectConfig;
        if (legacy.history !== undefined) {
            needsCleaning = true;
            const { history, ...cleanedConfig } = legacy;
            cleanedProjects[path] = cleanedConfig;
        }
        else {
            cleanedProjects[path] = projectConfig;
        }
    }
    return needsCleaning ? cleanedProjects : projects;
}
// fs.watchFile poll interval for detecting writes from other instances (ms)
const CONFIG_FRESHNESS_POLL_MS = 1000;
let freshnessWatcherStarted = false;
// fs.watchFile polls stat on the libuv threadpool and only calls us when mtime
// changed — a stalled stat never blocks the main thread.
function startGlobalConfigFreshnessWatcher() {
    if (freshnessWatcherStarted || process.env.NODE_ENV === 'test')
        return;
    freshnessWatcherStarted = true;
    const file = getGlobalClaudeFile();
    watchFile(file, { interval: CONFIG_FRESHNESS_POLL_MS, persistent: false }, curr => {
        // Our own writes fire this too — the write-through's Date.now()
        // overshoot makes cache.mtime > file mtime, so we skip the re-read.
        // Bun/Node also fire with curr.mtimeMs=0 when the file doesn't exist
        // (initial callback or deletion) — the <= handles that too.
        if (curr.mtimeMs <= globalConfigCache.mtime)
            return;
        void getFsImplementation()
            .readFile(file, { encoding: 'utf-8' })
            .then(content => {
            // A write-through may have advanced the cache while we were reading;
            // don't regress to the stale snapshot watchFile stat'd.
            if (curr.mtimeMs <= globalConfigCache.mtime)
                return;
            const parsed = safeParseJSON(stripBOM(content));
            if (parsed === null || typeof parsed !== 'object')
                return;
            globalConfigCache = {
                config: migrateConfigFields({
                    ...createDefaultGlobalConfig(),
                    ...parsed,
                }),
                mtime: curr.mtimeMs,
            };
            lastReadFileStats = { mtime: curr.mtimeMs, size: curr.size };
        })
            .catch(() => { });
    });
    registerCleanup(async () => {
        unwatchFile(file);
        freshnessWatcherStarted = false;
    });
}
// Write-through: what we just wrote IS the new config. cache.mtime overshoots
// the file's real mtime (Date.now() is recorded after the write) so the
// freshness watcher skips re-reading our own write on its next tick.
function writeThroughGlobalConfigCache(config) {
    globalConfigCache = { config, mtime: Date.now() };
    lastReadFileStats = null;
}
export function getGlobalConfig() {
    if (process.env.NODE_ENV === 'test') {
        return TEST_GLOBAL_CONFIG_FOR_TESTING;
    }
    // Fast path: pure memory read. After startup, this always hits — our own
    // writes go write-through and other instances' writes are picked up by the
    // background freshness watcher (never blocks this path).
    if (globalConfigCache.config) {
        configCacheHits++;
        return globalConfigCache.config;
    }
    // Slow path: startup load. Sync I/O here is acceptable because it runs
    // exactly once, before any UI is rendered. Stat before read so any race
    // self-corrects (old mtime + new content → watcher re-reads next tick).
    configCacheMisses++;
    try {
        let stats = null;
        try {
            stats = getFsImplementation().statSync(getGlobalClaudeFile());
        }
        catch {
            // File doesn't exist
        }
        const config = migrateConfigFields(getConfig(getGlobalClaudeFile(), createDefaultGlobalConfig));
        globalConfigCache = {
            config,
            mtime: stats?.mtimeMs ?? Date.now(),
        };
        lastReadFileStats = stats
            ? { mtime: stats.mtimeMs, size: stats.size }
            : null;
        startGlobalConfigFreshnessWatcher();
        return config;
    }
    catch {
        // If anything goes wrong, fall back to uncached behavior
        return migrateConfigFields(getConfig(getGlobalClaudeFile(), createDefaultGlobalConfig));
    }
}
/**
 * Returns the effective value of remoteControlAtStartup. Precedence:
 *   1. User's explicit config value (always wins — honors opt-out)
 *   2. CCR auto-connect default (ant-only build, GrowthBook-gated)
 *   3. false (Remote Control must be explicitly opted into)
 */
export function getRemoteControlAtStartup() {
    const explicit = getGlobalConfig().remoteControlAtStartup;
    if (explicit !== undefined)
        return explicit;
    if (feature('CCR_AUTO_CONNECT')) {
        if (ccrAutoConnect?.getCcrAutoConnectDefault())
            return true;
    }
    return false;
}
export function getCustomApiKeyStatus(truncatedApiKey) {
    const config = getGlobalConfig();
    if (config.customApiKeyResponses?.approved?.includes(truncatedApiKey)) {
        return 'approved';
    }
    if (config.customApiKeyResponses?.rejected?.includes(truncatedApiKey)) {
        return 'rejected';
    }
    return 'new';
}
function saveConfig(file, config, defaultConfig) {
    // Ensure the directory exists before writing the config file
    const dir = dirname(file);
    const fs = getFsImplementation();
    // mkdirSync is already recursive in FsOperations implementation
    fs.mkdirSync(dir);
    // Filter out any values that match the defaults
    const filteredConfig = pickBy(config, (value, key) => jsonStringify(value) !== jsonStringify(defaultConfig[key]));
    // Write config file with secure permissions - mode only applies to new files
    writeFileSyncAndFlush_DEPRECATED(file, jsonStringify(filteredConfig, null, 2), {
        encoding: 'utf-8',
        mode: 0o600,
    });
    if (file === getGlobalClaudeFile()) {
        globalConfigWriteCount++;
    }
}
/**
 * Returns true if a write was performed; false if the write was skipped
 * (no changes, or auth-loss guard tripped). Callers use this to decide
 * whether to invalidate the cache -- invalidating after a skipped write
 * destroys the good cached state the auth-loss guard depends on.
 */
function saveConfigWithLock(file, createDefault, mergeFn) {
    const defaultConfig = createDefault();
    const dir = dirname(file);
    const fs = getFsImplementation();
    // Ensure directory exists (mkdirSync is already recursive in FsOperations)
    fs.mkdirSync(dir);
    let release;
    try {
        const lockFilePath = `${file}.lock`;
        const startTime = Date.now();
        release = lockfile.lockSync(file, {
            lockfilePath: lockFilePath,
            onCompromised: err => {
                // Default onCompromised throws from a setTimeout callback, which
                // becomes an unhandled exception. Log instead -- the lock being
                // stolen (e.g. after a 10s event-loop stall) is recoverable.
                logForDebugging(`Config lock compromised: ${err}`, { level: 'error' });
            },
        });
        const lockTime = Date.now() - startTime;
        if (lockTime > 100) {
            logForDebugging('Lock acquisition took longer than expected - another Claude instance may be running');
            logEvent('tengu_config_lock_contention', {
                lock_time_ms: lockTime,
            });
        }
        // Check for stale write - file changed since we last read it
        // Only check for global config file since lastReadFileStats tracks that specific file
        if (lastReadFileStats && file === getGlobalClaudeFile()) {
            try {
                const currentStats = fs.statSync(file);
                if (currentStats.mtimeMs !== lastReadFileStats.mtime ||
                    currentStats.size !== lastReadFileStats.size) {
                    logEvent('tengu_config_stale_write', {
                        read_mtime: lastReadFileStats.mtime,
                        write_mtime: currentStats.mtimeMs,
                        read_size: lastReadFileStats.size,
                        write_size: currentStats.size,
                    });
                }
            }
            catch (e) {
                const code = getErrnoCode(e);
                if (code !== 'ENOENT') {
                    throw e;
                }
                // File doesn't exist yet, no stale check needed
            }
        }
        // Re-read the current config to get latest state. If the file is
        // momentarily corrupted (concurrent writes, kill-during-write), this
        // returns defaults -- we must not write those back over good config.
        const currentConfig = getConfig(file, createDefault);
        if (file === getGlobalClaudeFile() && wouldLoseAuthState(currentConfig)) {
            logForDebugging('saveConfigWithLock: re-read config is missing auth that cache has; refusing to write to avoid wiping ~/.claude.json. See GH #3117.', { level: 'error' });
            logEvent('tengu_config_auth_loss_prevented', {});
            return false;
        }
        // Apply the merge function to get the updated config
        const mergedConfig = mergeFn(currentConfig);
        // Skip write if no changes (same reference returned)
        if (mergedConfig === currentConfig) {
            return false;
        }
        // Filter out any values that match the defaults
        const filteredConfig = pickBy(mergedConfig, (value, key) => jsonStringify(value) !== jsonStringify(defaultConfig[key]));
        // Create timestamped backup of existing config before writing
        // We keep multiple backups to prevent data loss if a reset/corrupted config
        // overwrites a good backup. Backups are stored in ~/.claude/backups/ to
        // keep the home directory clean.
        try {
            const fileBase = basename(file);
            const backupDir = getConfigBackupDir();
            // Ensure backup directory exists
            try {
                fs.mkdirSync(backupDir);
            }
            catch (mkdirErr) {
                const mkdirCode = getErrnoCode(mkdirErr);
                if (mkdirCode !== 'EEXIST') {
                    throw mkdirErr;
                }
            }
            // Check existing backups first -- skip creating a new one if a recent
            // backup already exists. During startup, many saveGlobalConfig calls fire
            // within milliseconds of each other; without this check, each call
            // creates a new backup file that accumulates on disk.
            const MIN_BACKUP_INTERVAL_MS = 60_000;
            const existingBackups = fs
                .readdirStringSync(backupDir)
                .filter(f => f.startsWith(`${fileBase}.backup.`))
                .sort()
                .reverse(); // Most recent first (timestamps sort lexicographically)
            const mostRecentBackup = existingBackups[0];
            const mostRecentTimestamp = mostRecentBackup
                ? Number(mostRecentBackup.split('.backup.').pop())
                : 0;
            const shouldCreateBackup = Number.isNaN(mostRecentTimestamp) ||
                Date.now() - mostRecentTimestamp >= MIN_BACKUP_INTERVAL_MS;
            if (shouldCreateBackup) {
                const backupPath = join(backupDir, `${fileBase}.backup.${Date.now()}`);
                fs.copyFileSync(file, backupPath);
            }
            // Clean up old backups, keeping only the 5 most recent
            const MAX_BACKUPS = 5;
            // Re-read if we just created one; otherwise reuse the list
            const backupsForCleanup = shouldCreateBackup
                ? fs
                    .readdirStringSync(backupDir)
                    .filter(f => f.startsWith(`${fileBase}.backup.`))
                    .sort()
                    .reverse()
                : existingBackups;
            for (const oldBackup of backupsForCleanup.slice(MAX_BACKUPS)) {
                try {
                    fs.unlinkSync(join(backupDir, oldBackup));
                }
                catch {
                    // Ignore cleanup errors
                }
            }
        }
        catch (e) {
            const code = getErrnoCode(e);
            if (code !== 'ENOENT') {
                logForDebugging(`Failed to backup config: ${e}`, {
                    level: 'error',
                });
            }
            // No file to backup or backup failed, continue with write
        }
        // Write config file with secure permissions - mode only applies to new files
        writeFileSyncAndFlush_DEPRECATED(file, jsonStringify(filteredConfig, null, 2), {
            encoding: 'utf-8',
            mode: 0o600,
        });
        if (file === getGlobalClaudeFile()) {
            globalConfigWriteCount++;
        }
        return true;
    }
    finally {
        if (release) {
            release();
        }
    }
}
// Flag to track if config reading is allowed
let configReadingAllowed = false;
export function enableConfigs() {
    if (configReadingAllowed) {
        // Ensure this is idempotent
        return;
    }
    const startTime = Date.now();
    logForDiagnosticsNoPII('info', 'enable_configs_started');
    // Any reads to configuration before this flag is set show an console warning
    // to prevent us from adding config reading during module initialization
    configReadingAllowed = true;
    // We only check the global config because currently all the configs share a file
    getConfig(getGlobalClaudeFile(), createDefaultGlobalConfig, true /* throw on invalid */);
    logForDiagnosticsNoPII('info', 'enable_configs_completed', {
        duration_ms: Date.now() - startTime,
    });
}
/**
 * Returns the directory where config backup files are stored.
 * Uses ~/.claude/backups/ to keep the home directory clean.
 */
function getConfigBackupDir() {
    return join(getClaudeConfigHomeDir(), 'backups');
}
/**
 * Find the most recent backup file for a given config file.
 * Checks ~/.claude/backups/ first, then falls back to the legacy location
 * (next to the config file) for backwards compatibility.
 * Returns the full path to the most recent backup, or null if none exist.
 */
function findMostRecentBackup(file) {
    const fs = getFsImplementation();
    const fileBase = basename(file);
    const backupDir = getConfigBackupDir();
    // Check the new backup directory first
    try {
        const backups = fs
            .readdirStringSync(backupDir)
            .filter(f => f.startsWith(`${fileBase}.backup.`))
            .sort();
        const mostRecent = backups.at(-1); // Timestamps sort lexicographically
        if (mostRecent) {
            return join(backupDir, mostRecent);
        }
    }
    catch {
        // Backup dir doesn't exist yet
    }
    // Fall back to legacy location (next to the config file)
    const fileDir = dirname(file);
    try {
        const backups = fs
            .readdirStringSync(fileDir)
            .filter(f => f.startsWith(`${fileBase}.backup.`))
            .sort();
        const mostRecent = backups.at(-1); // Timestamps sort lexicographically
        if (mostRecent) {
            return join(fileDir, mostRecent);
        }
        // Check for legacy backup file (no timestamp)
        const legacyBackup = `${file}.backup`;
        try {
            fs.statSync(legacyBackup);
            return legacyBackup;
        }
        catch {
            // Legacy backup doesn't exist
        }
    }
    catch {
        // Ignore errors reading directory
    }
    return null;
}
function getConfig(file, createDefault, throwOnInvalid) {
    // Log a warning if config is accessed before it's allowed
    if (!configReadingAllowed && process.env.NODE_ENV !== 'test') {
        throw new Error('Config accessed before allowed.');
    }
    const fs = getFsImplementation();
    try {
        const fileContent = fs.readFileSync(file, {
            encoding: 'utf-8',
        });
        try {
            // Strip BOM before parsing - PowerShell 5.x adds BOM to UTF-8 files
            const parsedConfig = jsonParse(stripBOM(fileContent));
            return {
                ...createDefault(),
                ...parsedConfig,
            };
        }
        catch (error) {
            // Throw a ConfigParseError with the file path and default config
            const errorMessage = error instanceof Error ? error.message : String(error);
            throw new ConfigParseError(errorMessage, file, createDefault());
        }
    }
    catch (error) {
        // Handle file not found - check for backup and return default
        const errCode = getErrnoCode(error);
        if (errCode === 'ENOENT') {
            const backupPath = findMostRecentBackup(file);
            if (backupPath) {
                process.stderr.write(`\nClaude configuration file not found at: ${file}\n` +
                    `A backup file exists at: ${backupPath}\n` +
                    `You can manually restore it by running: cp "${backupPath}" "${file}"\n\n`);
            }
            return createDefault();
        }
        // Re-throw ConfigParseError if throwOnInvalid is true
        if (error instanceof ConfigParseError && throwOnInvalid) {
            throw error;
        }
        // Log config parse errors so users know what happened
        if (error instanceof ConfigParseError) {
            logForDebugging(`Config file corrupted, resetting to defaults: ${error.message}`, { level: 'error' });
            // Guard: logEvent → shouldSampleEvent → getGlobalConfig → getConfig
            // causes infinite recursion when the config file is corrupted, because
            // the sampling check reads a GrowthBook feature from global config.
            // Only log analytics on the outermost call.
            if (!insideGetConfig) {
                insideGetConfig = true;
                try {
                    // Log the error for monitoring
                    logError(error);
                    // Log analytics event for config corruption
                    let hasBackup = false;
                    try {
                        fs.statSync(`${file}.backup`);
                        hasBackup = true;
                    }
                    catch {
                        // No backup
                    }
                    logEvent('tengu_config_parse_error', {
                        has_backup: hasBackup,
                    });
                }
                finally {
                    insideGetConfig = false;
                }
            }
            process.stderr.write(`\nClaude configuration file at ${file} is corrupted: ${error.message}\n`);
            // Try to backup the corrupted config file (only if not already backed up)
            const fileBase = basename(file);
            const corruptedBackupDir = getConfigBackupDir();
            // Ensure backup directory exists
            try {
                fs.mkdirSync(corruptedBackupDir);
            }
            catch (mkdirErr) {
                const mkdirCode = getErrnoCode(mkdirErr);
                if (mkdirCode !== 'EEXIST') {
                    throw mkdirErr;
                }
            }
            const existingCorruptedBackups = fs
                .readdirStringSync(corruptedBackupDir)
                .filter(f => f.startsWith(`${fileBase}.corrupted.`));
            let corruptedBackupPath;
            let alreadyBackedUp = false;
            // Check if current corrupted content matches any existing backup
            const currentContent = fs.readFileSync(file, { encoding: 'utf-8' });
            for (const backup of existingCorruptedBackups) {
                try {
                    const backupContent = fs.readFileSync(join(corruptedBackupDir, backup), { encoding: 'utf-8' });
                    if (currentContent === backupContent) {
                        alreadyBackedUp = true;
                        break;
                    }
                }
                catch {
                    // Ignore read errors on backups
                }
            }
            if (!alreadyBackedUp) {
                corruptedBackupPath = join(corruptedBackupDir, `${fileBase}.corrupted.${Date.now()}`);
                try {
                    fs.copyFileSync(file, corruptedBackupPath);
                    logForDebugging(`Corrupted config backed up to: ${corruptedBackupPath}`, {
                        level: 'error',
                    });
                }
                catch {
                    // Ignore backup errors
                }
            }
            // Notify user about corrupted config and available backup
            const backupPath = findMostRecentBackup(file);
            if (corruptedBackupPath) {
                process.stderr.write(`The corrupted file has been backed up to: ${corruptedBackupPath}\n`);
            }
            else if (alreadyBackedUp) {
                process.stderr.write(`The corrupted file has already been backed up.\n`);
            }
            if (backupPath) {
                process.stderr.write(`A backup file exists at: ${backupPath}\n` +
                    `You can manually restore it by running: cp "${backupPath}" "${file}"\n\n`);
            }
            else {
                process.stderr.write(`\n`);
            }
        }
        return createDefault();
    }
}
// Memoized function to get the project path for config lookup
export const getProjectPathForConfig = memoize(() => {
    const originalCwd = getOriginalCwd();
    const gitRoot = findCanonicalGitRoot(originalCwd);
    if (gitRoot) {
        // Normalize for consistent JSON keys (forward slashes on all platforms)
        // This ensures paths like C:\Users\... and C:/Users/... map to the same key
        return normalizePathForConfigKey(gitRoot);
    }
    // Not in a git repo
    return normalizePathForConfigKey(resolve(originalCwd));
});
export function getCurrentProjectConfig() {
    if (process.env.NODE_ENV === 'test') {
        return TEST_PROJECT_CONFIG_FOR_TESTING;
    }
    const absolutePath = getProjectPathForConfig();
    const config = getGlobalConfig();
    if (!config.projects) {
        return DEFAULT_PROJECT_CONFIG;
    }
    const projectConfig = config.projects[absolutePath] ?? DEFAULT_PROJECT_CONFIG;
    // Not sure how this became a string
    // TODO: Fix upstream
    if (typeof projectConfig.allowedTools === 'string') {
        projectConfig.allowedTools =
            safeParseJSON(projectConfig.allowedTools) ?? [];
    }
    return projectConfig;
}
export function saveCurrentProjectConfig(updater) {
    if (process.env.NODE_ENV === 'test') {
        const config = updater(TEST_PROJECT_CONFIG_FOR_TESTING);
        // Skip if no changes (same reference returned)
        if (config === TEST_PROJECT_CONFIG_FOR_TESTING) {
            return;
        }
        Object.assign(TEST_PROJECT_CONFIG_FOR_TESTING, config);
        return;
    }
    const absolutePath = getProjectPathForConfig();
    let written = null;
    try {
        const didWrite = saveConfigWithLock(getGlobalClaudeFile(), createDefaultGlobalConfig, current => {
            const currentProjectConfig = current.projects?.[absolutePath] ?? DEFAULT_PROJECT_CONFIG;
            const newProjectConfig = updater(currentProjectConfig);
            // Skip if no changes (same reference returned)
            if (newProjectConfig === currentProjectConfig) {
                return current;
            }
            written = {
                ...current,
                projects: {
                    ...current.projects,
                    [absolutePath]: newProjectConfig,
                },
            };
            return written;
        });
        if (didWrite && written) {
            writeThroughGlobalConfigCache(written);
        }
    }
    catch (error) {
        logForDebugging(`Failed to save config with lock: ${error}`, {
            level: 'error',
        });
        // Same race window as saveGlobalConfig's fallback -- refuse to write
        // defaults over good cached config. See GH #3117.
        const config = getConfig(getGlobalClaudeFile(), createDefaultGlobalConfig);
        if (wouldLoseAuthState(config)) {
            logForDebugging('saveCurrentProjectConfig fallback: re-read config is missing auth that cache has; refusing to write. See GH #3117.', { level: 'error' });
            logEvent('tengu_config_auth_loss_prevented', {});
            return;
        }
        const currentProjectConfig = config.projects?.[absolutePath] ?? DEFAULT_PROJECT_CONFIG;
        const newProjectConfig = updater(currentProjectConfig);
        // Skip if no changes (same reference returned)
        if (newProjectConfig === currentProjectConfig) {
            return;
        }
        written = {
            ...config,
            projects: {
                ...config.projects,
                [absolutePath]: newProjectConfig,
            },
        };
        saveConfig(getGlobalClaudeFile(), written, DEFAULT_GLOBAL_CONFIG);
        writeThroughGlobalConfigCache(written);
    }
}
export function isAutoUpdaterDisabled() {
    return getAutoUpdaterDisabledReason() !== null;
}
/**
 * Returns true if plugin autoupdate should be skipped.
 * This checks if the auto-updater is disabled AND the FORCE_AUTOUPDATE_PLUGINS
 * env var is not set to 'true'. The env var allows forcing plugin autoupdate
 * even when the auto-updater is otherwise disabled.
 */
export function shouldSkipPluginAutoupdate() {
    return (isAutoUpdaterDisabled() &&
        !isEnvTruthy(process.env.FORCE_AUTOUPDATE_PLUGINS));
}
export function formatAutoUpdaterDisabledReason(reason) {
    switch (reason.type) {
        case 'development':
            return 'development build';
        case 'env':
            return `${reason.envVar} set`;
        case 'config':
            return 'config';
    }
}
export function getAutoUpdaterDisabledReason() {
    if (process.env.NODE_ENV === 'development') {
        return { type: 'development' };
    }
    if (isEnvTruthy(process.env.DISABLE_AUTOUPDATER)) {
        return { type: 'env', envVar: 'DISABLE_AUTOUPDATER' };
    }
    const essentialTrafficEnvVar = getEssentialTrafficOnlyReason();
    if (essentialTrafficEnvVar) {
        return { type: 'env', envVar: essentialTrafficEnvVar };
    }
    const config = getGlobalConfig();
    if (config.autoUpdates === false &&
        (config.installMethod !== 'native' ||
            config.autoUpdatesProtectedForNative !== true)) {
        return { type: 'config' };
    }
    return null;
}
export function getOrCreateUserID() {
    const config = getGlobalConfig();
    if (config.userID) {
        return config.userID;
    }
    const userID = randomBytes(32).toString('hex');
    saveGlobalConfig(current => ({ ...current, userID }));
    return userID;
}
export function recordFirstStartTime() {
    const config = getGlobalConfig();
    if (!config.firstStartTime) {
        const firstStartTime = new Date().toISOString();
        saveGlobalConfig(current => ({
            ...current,
            firstStartTime: current.firstStartTime ?? firstStartTime,
        }));
    }
}
export function getMemoryPath(memoryType) {
    const cwd = getOriginalCwd();
    switch (memoryType) {
        case 'User':
            return join(getClaudeConfigHomeDir(), 'CLAUDE.md');
        case 'Local':
            return join(cwd, 'CLAUDE.local.md');
        case 'Project':
            return join(cwd, 'CLAUDE.md');
        case 'Managed':
            return join(getManagedFilePath(), 'CLAUDE.md');
        case 'AutoMem':
            return getAutoMemEntrypoint();
    }
    // TeamMem is only a valid MemoryType when feature('TEAMMEM') is true
    if (feature('TEAMMEM')) {
        return teamMemPaths.getTeamMemEntrypoint();
    }
    return ''; // unreachable in external builds where TeamMem is not in MemoryType
}
export function getManagedClaudeRulesDir() {
    return join(getManagedFilePath(), '.claude', 'rules');
}
export function getUserClaudeRulesDir() {
    return join(getClaudeConfigHomeDir(), 'rules');
}
// Exported for testing only
export const _getConfigForTesting = getConfig;
export const _wouldLoseAuthStateForTesting = wouldLoseAuthState;
export function _setGlobalConfigCacheForTesting(config) {
    globalConfigCache.config = config;
    globalConfigCache.mtime = config ? Date.now() : 0;
}
