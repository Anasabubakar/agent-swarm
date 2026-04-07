import { realpathSync } from 'fs';
import sumBy from 'lodash-es/sumBy.js';
import { cwd } from 'process';
// Indirection for browser-sdk build (package.json "browser" field swaps
// crypto.ts for crypto.browser.ts). Pure leaf re-export of node:crypto —
// zero circular-dep risk. Path-alias import bypasses bootstrap-isolation
// (rule only checks ./ and / prefixes); explicit disable documents intent.
// eslint-disable-next-line custom-rules/bootstrap-isolation
import { randomUUID } from 'src/utils/crypto.js';
import { resetSettingsCache } from 'src/utils/settings/settingsCache.js';
import { createSignal } from 'src/utils/signal.js';
// ALSO HERE - THINK THRICE BEFORE MODIFYING
function getInitialState() {
    // Resolve symlinks in cwd to match behavior of shell.ts setCwd
    // This ensures consistency with how paths are sanitized for session storage
    let resolvedCwd = '';
    if (typeof process !== 'undefined' &&
        typeof process.cwd === 'function' &&
        typeof realpathSync === 'function') {
        const rawCwd = cwd();
        try {
            resolvedCwd = realpathSync(rawCwd).normalize('NFC');
        }
        catch {
            // File Provider EPERM on CloudStorage mounts (lstat per path component).
            resolvedCwd = rawCwd.normalize('NFC');
        }
    }
    const state = {
        originalCwd: resolvedCwd,
        projectRoot: resolvedCwd,
        totalCostUSD: 0,
        totalAPIDuration: 0,
        totalAPIDurationWithoutRetries: 0,
        totalToolDuration: 0,
        turnHookDurationMs: 0,
        turnToolDurationMs: 0,
        turnClassifierDurationMs: 0,
        turnToolCount: 0,
        turnHookCount: 0,
        turnClassifierCount: 0,
        startTime: Date.now(),
        lastInteractionTime: Date.now(),
        totalLinesAdded: 0,
        totalLinesRemoved: 0,
        hasUnknownModelCost: false,
        cwd: resolvedCwd,
        modelUsage: {},
        mainLoopModelOverride: undefined,
        initialMainLoopModel: null,
        modelStrings: null,
        isInteractive: false,
        kairosActive: false,
        strictToolResultPairing: false,
        sdkAgentProgressSummariesEnabled: false,
        userMsgOptIn: false,
        clientType: 'cli',
        sessionSource: undefined,
        questionPreviewFormat: undefined,
        sessionIngressToken: undefined,
        oauthTokenFromFd: undefined,
        apiKeyFromFd: undefined,
        flagSettingsPath: undefined,
        flagSettingsInline: null,
        allowedSettingSources: [
            'userSettings',
            'projectSettings',
            'localSettings',
            'flagSettings',
            'policySettings',
        ],
        // Telemetry state
        meter: null,
        sessionCounter: null,
        locCounter: null,
        prCounter: null,
        commitCounter: null,
        costCounter: null,
        tokenCounter: null,
        codeEditToolDecisionCounter: null,
        activeTimeCounter: null,
        statsStore: null,
        sessionId: randomUUID(),
        parentSessionId: undefined,
        // Logger state
        loggerProvider: null,
        eventLogger: null,
        // Meter provider state
        meterProvider: null,
        tracerProvider: null,
        // Agent color state
        agentColorMap: new Map(),
        agentColorIndex: 0,
        // Last API request for bug reports
        lastAPIRequest: null,
        lastAPIRequestMessages: null,
        // Last auto-mode classifier request(s) for /share transcript
        lastClassifierRequests: null,
        cachedClaudeMdContent: null,
        // In-memory error log for recent errors
        inMemoryErrorLog: [],
        // Session-only plugins from --plugin-dir flag
        inlinePlugins: [],
        // Explicit --chrome / --no-chrome flag value (undefined = not set on CLI)
        chromeFlagOverride: undefined,
        // Use cowork_plugins directory instead of plugins
        useCoworkPlugins: false,
        // Session-only bypass permissions mode flag (not persisted)
        sessionBypassPermissionsMode: false,
        // Scheduled tasks disabled until flag or dialog enables them
        scheduledTasksEnabled: false,
        sessionCronTasks: [],
        sessionCreatedTeams: new Set(),
        // Session-only trust flag (not persisted to disk)
        sessionTrustAccepted: false,
        // Session-only flag to disable session persistence to disk
        sessionPersistenceDisabled: false,
        // Track if user has exited plan mode in this session
        hasExitedPlanMode: false,
        // Track if we need to show the plan mode exit attachment
        needsPlanModeExitAttachment: false,
        // Track if we need to show the auto mode exit attachment
        needsAutoModeExitAttachment: false,
        // Track if LSP plugin recommendation has been shown this session
        lspRecommendationShownThisSession: false,
        // SDK init event state
        initJsonSchema: null,
        registeredHooks: null,
        // Cache for plan slugs
        planSlugCache: new Map(),
        // Track teleported session for reliability logging
        teleportedSessionInfo: null,
        // Track invoked skills for preservation across compaction
        invokedSkills: new Map(),
        // Track slow operations for dev bar display
        slowOperations: [],
        // SDK-provided betas
        sdkBetas: undefined,
        // Main thread agent type
        mainThreadAgentType: undefined,
        // Remote mode
        isRemoteMode: false,
        ...(process.env.USER_TYPE === 'ant'
            ? {
                replBridgeActive: false,
            }
            : {}),
        // Direct connect server URL
        directConnectServerUrl: undefined,
        // System prompt section cache state
        systemPromptSectionCache: new Map(),
        // Last date emitted to the model
        lastEmittedDate: null,
        // Additional directories from --add-dir flag (for CLAUDE.md loading)
        additionalDirectoriesForClaudeMd: [],
        // Channel server allowlist from --channels flag
        allowedChannels: [],
        hasDevChannels: false,
        // Session project dir (null = derive from originalCwd)
        sessionProjectDir: null,
        // Prompt cache 1h allowlist (null = not yet fetched from GrowthBook)
        promptCache1hAllowlist: null,
        // Prompt cache 1h eligibility (null = not yet evaluated)
        promptCache1hEligible: null,
        // Beta header latches (null = not yet triggered)
        afkModeHeaderLatched: null,
        fastModeHeaderLatched: null,
        cacheEditingHeaderLatched: null,
        thinkingClearLatched: null,
        // Current prompt ID
        promptId: null,
        lastMainRequestId: undefined,
        lastApiCompletionTimestamp: null,
        pendingPostCompaction: false,
    };
    return state;
}
// AND ESPECIALLY HERE
const STATE = getInitialState();
export function getSessionId() {
    return STATE.sessionId;
}
export function regenerateSessionId(options = {}) {
    if (options.setCurrentAsParent) {
        STATE.parentSessionId = STATE.sessionId;
    }
    // Drop the outgoing session's plan-slug entry so the Map doesn't
    // accumulate stale keys. Callers that need to carry the slug across
    // (REPL.tsx clearContext) read it before calling clearConversation.
    STATE.planSlugCache.delete(STATE.sessionId);
    // Regenerated sessions live in the current project: reset projectDir to
    // null so getTranscriptPath() derives from originalCwd.
    STATE.sessionId = randomUUID();
    STATE.sessionProjectDir = null;
    return STATE.sessionId;
}
export function getParentSessionId() {
    return STATE.parentSessionId;
}
/**
 * Atomically switch the active session. `sessionId` and `sessionProjectDir`
 * always change together — there is no separate setter for either, so they
 * cannot drift out of sync (CC-34).
 *
 * @param projectDir — directory containing `<sessionId>.jsonl`. Omit (or
 *   pass `null`) for sessions in the current project — the path will derive
 *   from originalCwd at read time. Pass `dirname(transcriptPath)` when the
 *   session lives in a different project directory (git worktrees,
 *   cross-project resume). Every call resets the project dir; it never
 *   carries over from the previous session.
 */
export function switchSession(sessionId, projectDir = null) {
    // Drop the outgoing session's plan-slug entry so the Map stays bounded
    // across repeated /resume. Only the current session's slug is ever read
    // (plans.ts getPlanSlug defaults to getSessionId()).
    STATE.planSlugCache.delete(STATE.sessionId);
    STATE.sessionId = sessionId;
    STATE.sessionProjectDir = projectDir;
    sessionSwitched.emit(sessionId);
}
const sessionSwitched = createSignal();
/**
 * Register a callback that fires when switchSession changes the active
 * sessionId. bootstrap can't import listeners directly (DAG leaf), so
 * callers register themselves. concurrentSessions.ts uses this to keep the
 * PID file's sessionId in sync with --resume.
 */
export const onSessionSwitch = sessionSwitched.subscribe;
/**
 * Project directory the current session's transcript lives in, or `null` if
 * the session was created in the current project (common case — derive from
 * originalCwd). See `switchSession()`.
 */
export function getSessionProjectDir() {
    return STATE.sessionProjectDir;
}
export function getOriginalCwd() {
    return STATE.originalCwd;
}
/**
 * Get the stable project root directory.
 * Unlike getOriginalCwd(), this is never updated by mid-session EnterWorktreeTool
 * (so skills/history stay stable when entering a throwaway worktree).
 * It IS set at startup by --worktree, since that worktree is the session's project.
 * Use for project identity (history, skills, sessions) not file operations.
 */
export function getProjectRoot() {
    return STATE.projectRoot;
}
export function setOriginalCwd(cwd) {
    STATE.originalCwd = cwd.normalize('NFC');
}
/**
 * Only for --worktree startup flag. Mid-session EnterWorktreeTool must NOT
 * call this — skills/history should stay anchored to where the session started.
 */
export function setProjectRoot(cwd) {
    STATE.projectRoot = cwd.normalize('NFC');
}
export function getCwdState() {
    return STATE.cwd;
}
export function setCwdState(cwd) {
    STATE.cwd = cwd.normalize('NFC');
}
export function getDirectConnectServerUrl() {
    return STATE.directConnectServerUrl;
}
export function setDirectConnectServerUrl(url) {
    STATE.directConnectServerUrl = url;
}
export function addToTotalDurationState(duration, durationWithoutRetries) {
    STATE.totalAPIDuration += duration;
    STATE.totalAPIDurationWithoutRetries += durationWithoutRetries;
}
export function resetTotalDurationStateAndCost_FOR_TESTS_ONLY() {
    STATE.totalAPIDuration = 0;
    STATE.totalAPIDurationWithoutRetries = 0;
    STATE.totalCostUSD = 0;
}
export function addToTotalCostState(cost, modelUsage, model) {
    STATE.modelUsage[model] = modelUsage;
    STATE.totalCostUSD += cost;
}
export function getTotalCostUSD() {
    return STATE.totalCostUSD;
}
export function getTotalAPIDuration() {
    return STATE.totalAPIDuration;
}
export function getTotalDuration() {
    return Date.now() - STATE.startTime;
}
export function getTotalAPIDurationWithoutRetries() {
    return STATE.totalAPIDurationWithoutRetries;
}
export function getTotalToolDuration() {
    return STATE.totalToolDuration;
}
export function addToToolDuration(duration) {
    STATE.totalToolDuration += duration;
    STATE.turnToolDurationMs += duration;
    STATE.turnToolCount++;
}
export function getTurnHookDurationMs() {
    return STATE.turnHookDurationMs;
}
export function addToTurnHookDuration(duration) {
    STATE.turnHookDurationMs += duration;
    STATE.turnHookCount++;
}
export function resetTurnHookDuration() {
    STATE.turnHookDurationMs = 0;
    STATE.turnHookCount = 0;
}
export function getTurnHookCount() {
    return STATE.turnHookCount;
}
export function getTurnToolDurationMs() {
    return STATE.turnToolDurationMs;
}
export function resetTurnToolDuration() {
    STATE.turnToolDurationMs = 0;
    STATE.turnToolCount = 0;
}
export function getTurnToolCount() {
    return STATE.turnToolCount;
}
export function getTurnClassifierDurationMs() {
    return STATE.turnClassifierDurationMs;
}
export function addToTurnClassifierDuration(duration) {
    STATE.turnClassifierDurationMs += duration;
    STATE.turnClassifierCount++;
}
export function resetTurnClassifierDuration() {
    STATE.turnClassifierDurationMs = 0;
    STATE.turnClassifierCount = 0;
}
export function getTurnClassifierCount() {
    return STATE.turnClassifierCount;
}
export function getStatsStore() {
    return STATE.statsStore;
}
export function setStatsStore(store) {
    STATE.statsStore = store;
}
/**
 * Marks that an interaction occurred.
 *
 * By default the actual Date.now() call is deferred until the next Ink render
 * frame (via flushInteractionTime()) so we avoid calling Date.now() on every
 * single keypress.
 *
 * Pass `immediate = true` when calling from React useEffect callbacks or
 * other code that runs *after* the Ink render cycle has already flushed.
 * Without it the timestamp stays stale until the next render, which may never
 * come if the user is idle (e.g. permission dialog waiting for input).
 */
let interactionTimeDirty = false;
export function updateLastInteractionTime(immediate) {
    if (immediate) {
        flushInteractionTime_inner();
    }
    else {
        interactionTimeDirty = true;
    }
}
/**
 * If an interaction was recorded since the last flush, update the timestamp
 * now. Called by Ink before each render cycle so we batch many keypresses into
 * a single Date.now() call.
 */
export function flushInteractionTime() {
    if (interactionTimeDirty) {
        flushInteractionTime_inner();
    }
}
function flushInteractionTime_inner() {
    STATE.lastInteractionTime = Date.now();
    interactionTimeDirty = false;
}
export function addToTotalLinesChanged(added, removed) {
    STATE.totalLinesAdded += added;
    STATE.totalLinesRemoved += removed;
}
export function getTotalLinesAdded() {
    return STATE.totalLinesAdded;
}
export function getTotalLinesRemoved() {
    return STATE.totalLinesRemoved;
}
export function getTotalInputTokens() {
    return sumBy(Object.values(STATE.modelUsage), 'inputTokens');
}
export function getTotalOutputTokens() {
    return sumBy(Object.values(STATE.modelUsage), 'outputTokens');
}
export function getTotalCacheReadInputTokens() {
    return sumBy(Object.values(STATE.modelUsage), 'cacheReadInputTokens');
}
export function getTotalCacheCreationInputTokens() {
    return sumBy(Object.values(STATE.modelUsage), 'cacheCreationInputTokens');
}
export function getTotalWebSearchRequests() {
    return sumBy(Object.values(STATE.modelUsage), 'webSearchRequests');
}
let outputTokensAtTurnStart = 0;
let currentTurnTokenBudget = null;
export function getTurnOutputTokens() {
    return getTotalOutputTokens() - outputTokensAtTurnStart;
}
export function getCurrentTurnTokenBudget() {
    return currentTurnTokenBudget;
}
let budgetContinuationCount = 0;
export function snapshotOutputTokensForTurn(budget) {
    outputTokensAtTurnStart = getTotalOutputTokens();
    currentTurnTokenBudget = budget;
    budgetContinuationCount = 0;
}
export function getBudgetContinuationCount() {
    return budgetContinuationCount;
}
export function incrementBudgetContinuationCount() {
    budgetContinuationCount++;
}
export function setHasUnknownModelCost() {
    STATE.hasUnknownModelCost = true;
}
export function hasUnknownModelCost() {
    return STATE.hasUnknownModelCost;
}
export function getLastMainRequestId() {
    return STATE.lastMainRequestId;
}
export function setLastMainRequestId(requestId) {
    STATE.lastMainRequestId = requestId;
}
export function getLastApiCompletionTimestamp() {
    return STATE.lastApiCompletionTimestamp;
}
export function setLastApiCompletionTimestamp(timestamp) {
    STATE.lastApiCompletionTimestamp = timestamp;
}
/** Mark that a compaction just occurred. The next API success event will
 *  include isPostCompaction=true, then the flag auto-resets. */
export function markPostCompaction() {
    STATE.pendingPostCompaction = true;
}
/** Consume the post-compaction flag. Returns true once after compaction,
 *  then returns false until the next compaction. */
export function consumePostCompaction() {
    const was = STATE.pendingPostCompaction;
    STATE.pendingPostCompaction = false;
    return was;
}
export function getLastInteractionTime() {
    return STATE.lastInteractionTime;
}
// Scroll drain suspension — background intervals check this before doing work
// so they don't compete with scroll frames for the event loop. Set by
// ScrollBox scrollBy/scrollTo, cleared SCROLL_DRAIN_IDLE_MS after the last
// scroll event. Module-scope (not in STATE) — ephemeral hot-path flag, no
// test-reset needed since the debounce timer self-clears.
let scrollDraining = false;
let scrollDrainTimer;
const SCROLL_DRAIN_IDLE_MS = 150;
/** Mark that a scroll event just happened. Background intervals gate on
 *  getIsScrollDraining() and skip their work until the debounce clears. */
export function markScrollActivity() {
    scrollDraining = true;
    if (scrollDrainTimer)
        clearTimeout(scrollDrainTimer);
    scrollDrainTimer = setTimeout(() => {
        scrollDraining = false;
        scrollDrainTimer = undefined;
    }, SCROLL_DRAIN_IDLE_MS);
    scrollDrainTimer.unref?.();
}
/** True while scroll is actively draining (within 150ms of last event).
 *  Intervals should early-return when this is set — the work picks up next
 *  tick after scroll settles. */
export function getIsScrollDraining() {
    return scrollDraining;
}
/** Await this before expensive one-shot work (network, subprocess) that could
 *  coincide with scroll. Resolves immediately if not scrolling; otherwise
 *  polls at the idle interval until the flag clears. */
export async function waitForScrollIdle() {
    while (scrollDraining) {
        // bootstrap-isolation forbids importing sleep() from src/utils/
        // eslint-disable-next-line no-restricted-syntax
        await new Promise(r => setTimeout(r, SCROLL_DRAIN_IDLE_MS).unref?.());
    }
}
export function getModelUsage() {
    return STATE.modelUsage;
}
export function getUsageForModel(model) {
    return STATE.modelUsage[model];
}
/**
 * Gets the model override set from the --model CLI flag or after the user
 * updates their configured model.
 */
export function getMainLoopModelOverride() {
    return STATE.mainLoopModelOverride;
}
export function getInitialMainLoopModel() {
    return STATE.initialMainLoopModel;
}
export function setMainLoopModelOverride(model) {
    STATE.mainLoopModelOverride = model;
}
export function setInitialMainLoopModel(model) {
    STATE.initialMainLoopModel = model;
}
export function getSdkBetas() {
    return STATE.sdkBetas;
}
export function setSdkBetas(betas) {
    STATE.sdkBetas = betas;
}
export function resetCostState() {
    STATE.totalCostUSD = 0;
    STATE.totalAPIDuration = 0;
    STATE.totalAPIDurationWithoutRetries = 0;
    STATE.totalToolDuration = 0;
    STATE.startTime = Date.now();
    STATE.totalLinesAdded = 0;
    STATE.totalLinesRemoved = 0;
    STATE.hasUnknownModelCost = false;
    STATE.modelUsage = {};
    STATE.promptId = null;
}
/**
 * Sets cost state values for session restore.
 * Called by restoreCostStateForSession in cost-tracker.ts.
 */
export function setCostStateForRestore({ totalCostUSD, totalAPIDuration, totalAPIDurationWithoutRetries, totalToolDuration, totalLinesAdded, totalLinesRemoved, lastDuration, modelUsage, }) {
    STATE.totalCostUSD = totalCostUSD;
    STATE.totalAPIDuration = totalAPIDuration;
    STATE.totalAPIDurationWithoutRetries = totalAPIDurationWithoutRetries;
    STATE.totalToolDuration = totalToolDuration;
    STATE.totalLinesAdded = totalLinesAdded;
    STATE.totalLinesRemoved = totalLinesRemoved;
    // Restore per-model usage breakdown
    if (modelUsage) {
        STATE.modelUsage = modelUsage;
    }
    // Adjust startTime to make wall duration accumulate
    if (lastDuration) {
        STATE.startTime = Date.now() - lastDuration;
    }
}
// Only used in tests
export function resetStateForTests() {
    if (process.env.NODE_ENV !== 'test') {
        throw new Error('resetStateForTests can only be called in tests');
    }
    Object.entries(getInitialState()).forEach(([key, value]) => {
        STATE[key] = value;
    });
    outputTokensAtTurnStart = 0;
    currentTurnTokenBudget = null;
    budgetContinuationCount = 0;
    sessionSwitched.clear();
}
// You shouldn't use this directly. See src/utils/model/modelStrings.ts::getModelStrings()
export function getModelStrings() {
    return STATE.modelStrings;
}
// You shouldn't use this directly. See src/utils/model/modelStrings.ts
export function setModelStrings(modelStrings) {
    STATE.modelStrings = modelStrings;
}
// Test utility function to reset model strings for re-initialization.
// Separate from setModelStrings because we only want to accept 'null' in tests.
export function resetModelStringsForTestingOnly() {
    STATE.modelStrings = null;
}
export function setMeter(meter, createCounter) {
    STATE.meter = meter;
    // Initialize all counters using the provided factory
    STATE.sessionCounter = createCounter('claude_code.session.count', {
        description: 'Count of CLI sessions started',
    });
    STATE.locCounter = createCounter('claude_code.lines_of_code.count', {
        description: "Count of lines of code modified, with the 'type' attribute indicating whether lines were added or removed",
    });
    STATE.prCounter = createCounter('claude_code.pull_request.count', {
        description: 'Number of pull requests created',
    });
    STATE.commitCounter = createCounter('claude_code.commit.count', {
        description: 'Number of git commits created',
    });
    STATE.costCounter = createCounter('claude_code.cost.usage', {
        description: 'Cost of the Claude Code session',
        unit: 'USD',
    });
    STATE.tokenCounter = createCounter('claude_code.token.usage', {
        description: 'Number of tokens used',
        unit: 'tokens',
    });
    STATE.codeEditToolDecisionCounter = createCounter('claude_code.code_edit_tool.decision', {
        description: 'Count of code editing tool permission decisions (accept/reject) for Edit, Write, and NotebookEdit tools',
    });
    STATE.activeTimeCounter = createCounter('claude_code.active_time.total', {
        description: 'Total active time in seconds',
        unit: 's',
    });
}
export function getMeter() {
    return STATE.meter;
}
export function getSessionCounter() {
    return STATE.sessionCounter;
}
export function getLocCounter() {
    return STATE.locCounter;
}
export function getPrCounter() {
    return STATE.prCounter;
}
export function getCommitCounter() {
    return STATE.commitCounter;
}
export function getCostCounter() {
    return STATE.costCounter;
}
export function getTokenCounter() {
    return STATE.tokenCounter;
}
export function getCodeEditToolDecisionCounter() {
    return STATE.codeEditToolDecisionCounter;
}
export function getActiveTimeCounter() {
    return STATE.activeTimeCounter;
}
export function getLoggerProvider() {
    return STATE.loggerProvider;
}
export function setLoggerProvider(provider) {
    STATE.loggerProvider = provider;
}
export function getEventLogger() {
    return STATE.eventLogger;
}
export function setEventLogger(logger) {
    STATE.eventLogger = logger;
}
export function getMeterProvider() {
    return STATE.meterProvider;
}
export function setMeterProvider(provider) {
    STATE.meterProvider = provider;
}
export function getTracerProvider() {
    return STATE.tracerProvider;
}
export function setTracerProvider(provider) {
    STATE.tracerProvider = provider;
}
export function getIsNonInteractiveSession() {
    return !STATE.isInteractive;
}
export function getIsInteractive() {
    return STATE.isInteractive;
}
export function setIsInteractive(value) {
    STATE.isInteractive = value;
}
export function getClientType() {
    return STATE.clientType;
}
export function setClientType(type) {
    STATE.clientType = type;
}
export function getSdkAgentProgressSummariesEnabled() {
    return STATE.sdkAgentProgressSummariesEnabled;
}
export function setSdkAgentProgressSummariesEnabled(value) {
    STATE.sdkAgentProgressSummariesEnabled = value;
}
export function getKairosActive() {
    return STATE.kairosActive;
}
export function setKairosActive(value) {
    STATE.kairosActive = value;
}
export function getStrictToolResultPairing() {
    return STATE.strictToolResultPairing;
}
export function setStrictToolResultPairing(value) {
    STATE.strictToolResultPairing = value;
}
// Field name 'userMsgOptIn' avoids excluded-string substrings ('BriefTool',
// 'SendUserMessage' — case-insensitive). All callers are inside feature()
// guards so these accessors don't need their own (matches getKairosActive).
export function getUserMsgOptIn() {
    return STATE.userMsgOptIn;
}
export function setUserMsgOptIn(value) {
    STATE.userMsgOptIn = value;
}
export function getSessionSource() {
    return STATE.sessionSource;
}
export function setSessionSource(source) {
    STATE.sessionSource = source;
}
export function getQuestionPreviewFormat() {
    return STATE.questionPreviewFormat;
}
export function setQuestionPreviewFormat(format) {
    STATE.questionPreviewFormat = format;
}
export function getAgentColorMap() {
    return STATE.agentColorMap;
}
export function getFlagSettingsPath() {
    return STATE.flagSettingsPath;
}
export function setFlagSettingsPath(path) {
    STATE.flagSettingsPath = path;
}
export function getFlagSettingsInline() {
    return STATE.flagSettingsInline;
}
export function setFlagSettingsInline(settings) {
    STATE.flagSettingsInline = settings;
}
export function getSessionIngressToken() {
    return STATE.sessionIngressToken;
}
export function setSessionIngressToken(token) {
    STATE.sessionIngressToken = token;
}
export function getOauthTokenFromFd() {
    return STATE.oauthTokenFromFd;
}
export function setOauthTokenFromFd(token) {
    STATE.oauthTokenFromFd = token;
}
export function getApiKeyFromFd() {
    return STATE.apiKeyFromFd;
}
export function setApiKeyFromFd(key) {
    STATE.apiKeyFromFd = key;
}
export function setLastAPIRequest(params) {
    STATE.lastAPIRequest = params;
}
export function getLastAPIRequest() {
    return STATE.lastAPIRequest;
}
export function setLastAPIRequestMessages(messages) {
    STATE.lastAPIRequestMessages = messages;
}
export function getLastAPIRequestMessages() {
    return STATE.lastAPIRequestMessages;
}
export function setLastClassifierRequests(requests) {
    STATE.lastClassifierRequests = requests;
}
export function getLastClassifierRequests() {
    return STATE.lastClassifierRequests;
}
export function setCachedClaudeMdContent(content) {
    STATE.cachedClaudeMdContent = content;
}
export function getCachedClaudeMdContent() {
    return STATE.cachedClaudeMdContent;
}
export function addToInMemoryErrorLog(errorInfo) {
    const MAX_IN_MEMORY_ERRORS = 100;
    if (STATE.inMemoryErrorLog.length >= MAX_IN_MEMORY_ERRORS) {
        STATE.inMemoryErrorLog.shift(); // Remove oldest error
    }
    STATE.inMemoryErrorLog.push(errorInfo);
}
export function getAllowedSettingSources() {
    return STATE.allowedSettingSources;
}
export function setAllowedSettingSources(sources) {
    STATE.allowedSettingSources = sources;
}
export function preferThirdPartyAuthentication() {
    // IDE extension should behave as 1P for authentication reasons.
    return getIsNonInteractiveSession() && STATE.clientType !== 'claude-vscode';
}
export function setInlinePlugins(plugins) {
    STATE.inlinePlugins = plugins;
}
export function getInlinePlugins() {
    return STATE.inlinePlugins;
}
export function setChromeFlagOverride(value) {
    STATE.chromeFlagOverride = value;
}
export function getChromeFlagOverride() {
    return STATE.chromeFlagOverride;
}
export function setUseCoworkPlugins(value) {
    STATE.useCoworkPlugins = value;
    resetSettingsCache();
}
export function getUseCoworkPlugins() {
    return STATE.useCoworkPlugins;
}
export function setSessionBypassPermissionsMode(enabled) {
    STATE.sessionBypassPermissionsMode = enabled;
}
export function getSessionBypassPermissionsMode() {
    return STATE.sessionBypassPermissionsMode;
}
export function setScheduledTasksEnabled(enabled) {
    STATE.scheduledTasksEnabled = enabled;
}
export function getScheduledTasksEnabled() {
    return STATE.scheduledTasksEnabled;
}
export function getSessionCronTasks() {
    return STATE.sessionCronTasks;
}
export function addSessionCronTask(task) {
    STATE.sessionCronTasks.push(task);
}
/**
 * Returns the number of tasks actually removed. Callers use this to skip
 * downstream work (e.g. the disk read in removeCronTasks) when all ids
 * were accounted for here.
 */
export function removeSessionCronTasks(ids) {
    if (ids.length === 0)
        return 0;
    const idSet = new Set(ids);
    const remaining = STATE.sessionCronTasks.filter(t => !idSet.has(t.id));
    const removed = STATE.sessionCronTasks.length - remaining.length;
    if (removed === 0)
        return 0;
    STATE.sessionCronTasks = remaining;
    return removed;
}
export function setSessionTrustAccepted(accepted) {
    STATE.sessionTrustAccepted = accepted;
}
export function getSessionTrustAccepted() {
    return STATE.sessionTrustAccepted;
}
export function setSessionPersistenceDisabled(disabled) {
    STATE.sessionPersistenceDisabled = disabled;
}
export function isSessionPersistenceDisabled() {
    return STATE.sessionPersistenceDisabled;
}
export function hasExitedPlanModeInSession() {
    return STATE.hasExitedPlanMode;
}
export function setHasExitedPlanMode(value) {
    STATE.hasExitedPlanMode = value;
}
export function needsPlanModeExitAttachment() {
    return STATE.needsPlanModeExitAttachment;
}
export function setNeedsPlanModeExitAttachment(value) {
    STATE.needsPlanModeExitAttachment = value;
}
export function handlePlanModeTransition(fromMode, toMode) {
    // If switching TO plan mode, clear any pending exit attachment
    // This prevents sending both plan_mode and plan_mode_exit when user toggles quickly
    if (toMode === 'plan' && fromMode !== 'plan') {
        STATE.needsPlanModeExitAttachment = false;
    }
    // If switching out of plan mode, trigger the plan_mode_exit attachment
    if (fromMode === 'plan' && toMode !== 'plan') {
        STATE.needsPlanModeExitAttachment = true;
    }
}
export function needsAutoModeExitAttachment() {
    return STATE.needsAutoModeExitAttachment;
}
export function setNeedsAutoModeExitAttachment(value) {
    STATE.needsAutoModeExitAttachment = value;
}
export function handleAutoModeTransition(fromMode, toMode) {
    // Auto↔plan transitions are handled by prepareContextForPlanMode (auto may
    // stay active through plan if opted in) and ExitPlanMode (restores mode).
    // Skip both directions so this function only handles direct auto transitions.
    if ((fromMode === 'auto' && toMode === 'plan') ||
        (fromMode === 'plan' && toMode === 'auto')) {
        return;
    }
    const fromIsAuto = fromMode === 'auto';
    const toIsAuto = toMode === 'auto';
    // If switching TO auto mode, clear any pending exit attachment
    // This prevents sending both auto_mode and auto_mode_exit when user toggles quickly
    if (toIsAuto && !fromIsAuto) {
        STATE.needsAutoModeExitAttachment = false;
    }
    // If switching out of auto mode, trigger the auto_mode_exit attachment
    if (fromIsAuto && !toIsAuto) {
        STATE.needsAutoModeExitAttachment = true;
    }
}
// LSP plugin recommendation session tracking
export function hasShownLspRecommendationThisSession() {
    return STATE.lspRecommendationShownThisSession;
}
export function setLspRecommendationShownThisSession(value) {
    STATE.lspRecommendationShownThisSession = value;
}
// SDK init event state
export function setInitJsonSchema(schema) {
    STATE.initJsonSchema = schema;
}
export function getInitJsonSchema() {
    return STATE.initJsonSchema;
}
export function registerHookCallbacks(hooks) {
    if (!STATE.registeredHooks) {
        STATE.registeredHooks = {};
    }
    // `registerHookCallbacks` may be called multiple times, so we need to merge (not overwrite)
    for (const [event, matchers] of Object.entries(hooks)) {
        const eventKey = event;
        if (!STATE.registeredHooks[eventKey]) {
            STATE.registeredHooks[eventKey] = [];
        }
        STATE.registeredHooks[eventKey].push(...matchers);
    }
}
export function getRegisteredHooks() {
    return STATE.registeredHooks;
}
export function clearRegisteredHooks() {
    STATE.registeredHooks = null;
}
export function clearRegisteredPluginHooks() {
    if (!STATE.registeredHooks) {
        return;
    }
    const filtered = {};
    for (const [event, matchers] of Object.entries(STATE.registeredHooks)) {
        // Keep only callback hooks (those without pluginRoot)
        const callbackHooks = matchers.filter(m => !('pluginRoot' in m));
        if (callbackHooks.length > 0) {
            filtered[event] = callbackHooks;
        }
    }
    STATE.registeredHooks = Object.keys(filtered).length > 0 ? filtered : null;
}
export function resetSdkInitState() {
    STATE.initJsonSchema = null;
    STATE.registeredHooks = null;
}
export function getPlanSlugCache() {
    return STATE.planSlugCache;
}
export function getSessionCreatedTeams() {
    return STATE.sessionCreatedTeams;
}
// Teleported session tracking for reliability logging
export function setTeleportedSessionInfo(info) {
    STATE.teleportedSessionInfo = {
        isTeleported: true,
        hasLoggedFirstMessage: false,
        sessionId: info.sessionId,
    };
}
export function getTeleportedSessionInfo() {
    return STATE.teleportedSessionInfo;
}
export function markFirstTeleportMessageLogged() {
    if (STATE.teleportedSessionInfo) {
        STATE.teleportedSessionInfo.hasLoggedFirstMessage = true;
    }
}
export function addInvokedSkill(skillName, skillPath, content, agentId = null) {
    const key = `${agentId ?? ''}:${skillName}`;
    STATE.invokedSkills.set(key, {
        skillName,
        skillPath,
        content,
        invokedAt: Date.now(),
        agentId,
    });
}
export function getInvokedSkills() {
    return STATE.invokedSkills;
}
export function getInvokedSkillsForAgent(agentId) {
    const normalizedId = agentId ?? null;
    const filtered = new Map();
    for (const [key, skill] of STATE.invokedSkills) {
        if (skill.agentId === normalizedId) {
            filtered.set(key, skill);
        }
    }
    return filtered;
}
export function clearInvokedSkills(preservedAgentIds) {
    if (!preservedAgentIds || preservedAgentIds.size === 0) {
        STATE.invokedSkills.clear();
        return;
    }
    for (const [key, skill] of STATE.invokedSkills) {
        if (skill.agentId === null || !preservedAgentIds.has(skill.agentId)) {
            STATE.invokedSkills.delete(key);
        }
    }
}
export function clearInvokedSkillsForAgent(agentId) {
    for (const [key, skill] of STATE.invokedSkills) {
        if (skill.agentId === agentId) {
            STATE.invokedSkills.delete(key);
        }
    }
}
// Slow operations tracking for dev bar
const MAX_SLOW_OPERATIONS = 10;
const SLOW_OPERATION_TTL_MS = 10000;
export function addSlowOperation(operation, durationMs) {
    if (process.env.USER_TYPE !== 'ant')
        return;
    // Skip tracking for editor sessions (user editing a prompt file in $EDITOR)
    // These are intentionally slow since the user is drafting text
    if (operation.includes('exec') && operation.includes('claude-prompt-')) {
        return;
    }
    const now = Date.now();
    // Remove stale operations
    STATE.slowOperations = STATE.slowOperations.filter(op => now - op.timestamp < SLOW_OPERATION_TTL_MS);
    // Add new operation
    STATE.slowOperations.push({ operation, durationMs, timestamp: now });
    // Keep only the most recent operations
    if (STATE.slowOperations.length > MAX_SLOW_OPERATIONS) {
        STATE.slowOperations = STATE.slowOperations.slice(-MAX_SLOW_OPERATIONS);
    }
}
const EMPTY_SLOW_OPERATIONS = [];
export function getSlowOperations() {
    // Most common case: nothing tracked. Return a stable reference so the
    // caller's setState() can bail via Object.is instead of re-rendering at 2fps.
    if (STATE.slowOperations.length === 0) {
        return EMPTY_SLOW_OPERATIONS;
    }
    const now = Date.now();
    // Only allocate a new array when something actually expired; otherwise keep
    // the reference stable across polls while ops are still fresh.
    if (STATE.slowOperations.some(op => now - op.timestamp >= SLOW_OPERATION_TTL_MS)) {
        STATE.slowOperations = STATE.slowOperations.filter(op => now - op.timestamp < SLOW_OPERATION_TTL_MS);
        if (STATE.slowOperations.length === 0) {
            return EMPTY_SLOW_OPERATIONS;
        }
    }
    // Safe to return directly: addSlowOperation() reassigns STATE.slowOperations
    // before pushing, so the array held in React state is never mutated.
    return STATE.slowOperations;
}
export function getMainThreadAgentType() {
    return STATE.mainThreadAgentType;
}
export function setMainThreadAgentType(agentType) {
    STATE.mainThreadAgentType = agentType;
}
export function getIsRemoteMode() {
    return STATE.isRemoteMode;
}
export function setIsRemoteMode(value) {
    STATE.isRemoteMode = value;
}
// System prompt section accessors
export function getSystemPromptSectionCache() {
    return STATE.systemPromptSectionCache;
}
export function setSystemPromptSectionCacheEntry(name, value) {
    STATE.systemPromptSectionCache.set(name, value);
}
export function clearSystemPromptSectionState() {
    STATE.systemPromptSectionCache.clear();
}
// Last emitted date accessors (for detecting midnight date changes)
export function getLastEmittedDate() {
    return STATE.lastEmittedDate;
}
export function setLastEmittedDate(date) {
    STATE.lastEmittedDate = date;
}
export function getAdditionalDirectoriesForClaudeMd() {
    return STATE.additionalDirectoriesForClaudeMd;
}
export function setAdditionalDirectoriesForClaudeMd(directories) {
    STATE.additionalDirectoriesForClaudeMd = directories;
}
export function getAllowedChannels() {
    return STATE.allowedChannels;
}
export function setAllowedChannels(entries) {
    STATE.allowedChannels = entries;
}
export function getHasDevChannels() {
    return STATE.hasDevChannels;
}
export function setHasDevChannels(value) {
    STATE.hasDevChannels = value;
}
export function getPromptCache1hAllowlist() {
    return STATE.promptCache1hAllowlist;
}
export function setPromptCache1hAllowlist(allowlist) {
    STATE.promptCache1hAllowlist = allowlist;
}
export function getPromptCache1hEligible() {
    return STATE.promptCache1hEligible;
}
export function setPromptCache1hEligible(eligible) {
    STATE.promptCache1hEligible = eligible;
}
export function getAfkModeHeaderLatched() {
    return STATE.afkModeHeaderLatched;
}
export function setAfkModeHeaderLatched(v) {
    STATE.afkModeHeaderLatched = v;
}
export function getFastModeHeaderLatched() {
    return STATE.fastModeHeaderLatched;
}
export function setFastModeHeaderLatched(v) {
    STATE.fastModeHeaderLatched = v;
}
export function getCacheEditingHeaderLatched() {
    return STATE.cacheEditingHeaderLatched;
}
export function setCacheEditingHeaderLatched(v) {
    STATE.cacheEditingHeaderLatched = v;
}
export function getThinkingClearLatched() {
    return STATE.thinkingClearLatched;
}
export function setThinkingClearLatched(v) {
    STATE.thinkingClearLatched = v;
}
/**
 * Reset beta header latches to null. Called on /clear and /compact so a
 * fresh conversation gets fresh header evaluation.
 */
export function clearBetaHeaderLatches() {
    STATE.afkModeHeaderLatched = null;
    STATE.fastModeHeaderLatched = null;
    STATE.cacheEditingHeaderLatched = null;
    STATE.thinkingClearLatched = null;
}
export function getPromptId() {
    return STATE.promptId;
}
export function setPromptId(id) {
    STATE.promptId = id;
}
