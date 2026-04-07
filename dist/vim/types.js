/**
 * Vim Mode State Machine Types
 *
 * This file defines the complete state machine for vim input handling.
 * The types ARE the documentation - reading them tells you how the system works.
 *
 * State Diagram:
 * ```
 *                              VimState
 *   ┌──────────────────────────────┬──────────────────────────────────────┐
 *   │  INSERT                      │  NORMAL                              │
 *   │  (tracks insertedText)       │  (CommandState machine)              │
 *   │                              │                                      │
 *   │                              │  idle ──┬─[d/c/y]──► operator        │
 *   │                              │         ├─[1-9]────► count           │
 *   │                              │         ├─[fFtT]───► find            │
 *   │                              │         ├─[g]──────► g               │
 *   │                              │         ├─[r]──────► replace         │
 *   │                              │         └─[><]─────► indent          │
 *   │                              │                                      │
 *   │                              │  operator ─┬─[motion]──► execute     │
 *   │                              │            ├─[0-9]────► operatorCount│
 *   │                              │            ├─[ia]─────► operatorTextObj
 *   │                              │            └─[fFtT]───► operatorFind │
 *   └──────────────────────────────┴──────────────────────────────────────┘
 * ```
 */
// ============================================================================
// Key Groups - Named constants, no magic strings
// ============================================================================
export const OPERATORS = {
    d: 'delete',
    c: 'change',
    y: 'yank',
};
export function isOperatorKey(key) {
    return key in OPERATORS;
}
export const SIMPLE_MOTIONS = new Set([
    'h',
    'l',
    'j',
    'k', // Basic movement
    'w',
    'b',
    'e',
    'W',
    'B',
    'E', // Word motions
    '0',
    '^',
    '$', // Line positions
]);
export const FIND_KEYS = new Set(['f', 'F', 't', 'T']);
export const TEXT_OBJ_SCOPES = {
    i: 'inner',
    a: 'around',
};
export function isTextObjScopeKey(key) {
    return key in TEXT_OBJ_SCOPES;
}
export const TEXT_OBJ_TYPES = new Set([
    'w',
    'W', // Word/WORD
    '"',
    "'",
    '`', // Quotes
    '(',
    ')',
    'b', // Parens
    '[',
    ']', // Brackets
    '{',
    '}',
    'B', // Braces
    '<',
    '>', // Angle brackets
]);
export const MAX_VIM_COUNT = 10000;
// ============================================================================
// State Factories
// ============================================================================
export function createInitialVimState() {
    return { mode: 'INSERT', insertedText: '' };
}
export function createInitialPersistentState() {
    return {
        lastChange: null,
        lastFind: null,
        register: '',
        registerIsLinewise: false,
    };
}
