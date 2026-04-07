/**
 * Pure TypeScript port of vendor/color-diff-src.
 *
 * The Rust version uses syntect+bat for syntax highlighting and the similar
 * crate for word diffing. This port uses highlight.js (already a dep via
 * cli-highlight) and the diff npm package's diffArrays.
 *
 * API matches vendor/color-diff-src/index.d.ts exactly so callers don't change.
 *
 * Key semantic differences from the native module:
 * - Syntax highlighting uses highlight.js. Scope colors were measured from
 *   syntect's output so most tokens match, but hljs's grammar has gaps:
 *   plain identifiers and operators like `=` `:` aren't scoped, so they
 *   render in default fg instead of white/pink. Output structure (line
 *   numbers, markers, backgrounds, word-diff) is identical.
 * - BAT_THEME env support is a stub: highlight.js has no bat theme set, so
 *   getSyntaxTheme always returns the default for the given Claude theme.
 */
import { diffArrays } from 'diff';
import { basename, extname } from 'path';
let cachedHljs = null;
function hljs() {
    if (cachedHljs)
        return cachedHljs;
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const mod = require('highlight.js');
    // highlight.js uses `export =` (CJS). Under bun/ESM the interop wraps it
    // in .default; under node CJS the module IS the API. Check at runtime.
    cachedHljs = 'default' in mod && mod.default ? mod.default : mod;
    return cachedHljs;
}
import { stringWidth } from '../../ink/stringWidth.js';
import { logError } from '../../utils/log.js';
const RESET = '\x1b[0m';
const DIM = '\x1b[2m';
const UNDIM = '\x1b[22m';
function rgb(r, g, b) {
    return { r, g, b, a: 255 };
}
function ansiIdx(index) {
    return { r: index, g: 0, b: 0, a: 0 };
}
// Sentinel: a=1 means "terminal default" (matches bat convention)
const DEFAULT_BG = { r: 0, g: 0, b: 0, a: 1 };
function detectColorMode(theme) {
    if (theme.includes('ansi'))
        return 'ansi';
    const ct = process.env.COLORTERM ?? '';
    return ct === 'truecolor' || ct === '24bit' ? 'truecolor' : 'color256';
}
// Port of ansi_colours::ansi256_from_rgb — approximates RGB to the xterm-256
// palette (6x6x6 cube + 24 greys). Picks the perceptually closest index by
// comparing cube vs grey-ramp candidates, like the Rust crate.
const CUBE_LEVELS = [0, 95, 135, 175, 215, 255];
function ansi256FromRgb(r, g, b) {
    const q = (c) => c < 48 ? 0 : c < 115 ? 1 : c < 155 ? 2 : c < 195 ? 3 : c < 235 ? 4 : 5;
    const qr = q(r);
    const qg = q(g);
    const qb = q(b);
    const cubeIdx = 16 + 36 * qr + 6 * qg + qb;
    // Grey ramp candidate (232-255, levels 8..238 step 10). Beyond the ramp's
    // range the cube corner is the only option — ansi_colours snaps 248,248,242
    // to 231 (cube white), not 255 (ramp top).
    const grey = Math.round((r + g + b) / 3);
    if (grey < 5)
        return 16;
    if (grey > 244 && qr === qg && qg === qb)
        return cubeIdx;
    const greyLevel = Math.max(0, Math.min(23, Math.round((grey - 8) / 10)));
    const greyIdx = 232 + greyLevel;
    const greyRgb = 8 + greyLevel * 10;
    const cr = CUBE_LEVELS[qr];
    const cg = CUBE_LEVELS[qg];
    const cb = CUBE_LEVELS[qb];
    const dCube = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2;
    const dGrey = (r - greyRgb) ** 2 + (g - greyRgb) ** 2 + (b - greyRgb) ** 2;
    return dGrey < dCube ? greyIdx : cubeIdx;
}
function colorToEscape(c, fg, mode) {
    // alpha=0: palette index encoded in .r (bat's ansi-theme convention)
    if (c.a === 0) {
        const idx = c.r;
        if (idx < 8)
            return `\x1b[${(fg ? 30 : 40) + idx}m`;
        if (idx < 16)
            return `\x1b[${(fg ? 90 : 100) + (idx - 8)}m`;
        return `\x1b[${fg ? 38 : 48};5;${idx}m`;
    }
    // alpha=1: terminal default
    if (c.a === 1)
        return fg ? '\x1b[39m' : '\x1b[49m';
    const codeType = fg ? 38 : 48;
    if (mode === 'truecolor') {
        return `\x1b[${codeType};2;${c.r};${c.g};${c.b}m`;
    }
    return `\x1b[${codeType};5;${ansi256FromRgb(c.r, c.g, c.b)}m`;
}
function asTerminalEscaped(blocks, mode, skipBackground, dim) {
    let out = dim ? RESET + DIM : RESET;
    for (const [style, text] of blocks) {
        out += colorToEscape(style.foreground, true, mode);
        if (!skipBackground) {
            out += colorToEscape(style.background, false, mode);
        }
        out += text;
    }
    return out + RESET;
}
function defaultSyntaxThemeName(themeName) {
    if (themeName.includes('ansi'))
        return 'ansi';
    if (themeName.includes('dark'))
        return 'Monokai Extended';
    return 'GitHub';
}
// highlight.js scope → syntect Monokai Extended foreground (measured from the
// Rust module's output so colors match the original exactly)
const MONOKAI_SCOPES = {
    keyword: rgb(249, 38, 114),
    _storage: rgb(102, 217, 239),
    built_in: rgb(166, 226, 46),
    type: rgb(166, 226, 46),
    literal: rgb(190, 132, 255),
    number: rgb(190, 132, 255),
    string: rgb(230, 219, 116),
    title: rgb(166, 226, 46),
    'title.function': rgb(166, 226, 46),
    'title.class': rgb(166, 226, 46),
    'title.class.inherited': rgb(166, 226, 46),
    params: rgb(253, 151, 31),
    comment: rgb(117, 113, 94),
    meta: rgb(117, 113, 94),
    attr: rgb(166, 226, 46),
    attribute: rgb(166, 226, 46),
    variable: rgb(255, 255, 255),
    'variable.language': rgb(255, 255, 255),
    property: rgb(255, 255, 255),
    operator: rgb(249, 38, 114),
    punctuation: rgb(248, 248, 242),
    symbol: rgb(190, 132, 255),
    regexp: rgb(230, 219, 116),
    subst: rgb(248, 248, 242),
};
// highlight.js scope → syntect GitHub-light foreground (measured from Rust)
const GITHUB_SCOPES = {
    keyword: rgb(167, 29, 93),
    _storage: rgb(167, 29, 93),
    built_in: rgb(0, 134, 179),
    type: rgb(0, 134, 179),
    literal: rgb(0, 134, 179),
    number: rgb(0, 134, 179),
    string: rgb(24, 54, 145),
    title: rgb(121, 93, 163),
    'title.function': rgb(121, 93, 163),
    'title.class': rgb(0, 0, 0),
    'title.class.inherited': rgb(0, 0, 0),
    params: rgb(0, 134, 179),
    comment: rgb(150, 152, 150),
    meta: rgb(150, 152, 150),
    attr: rgb(0, 134, 179),
    attribute: rgb(0, 134, 179),
    variable: rgb(0, 134, 179),
    'variable.language': rgb(0, 134, 179),
    property: rgb(0, 134, 179),
    operator: rgb(167, 29, 93),
    punctuation: rgb(51, 51, 51),
    symbol: rgb(0, 134, 179),
    regexp: rgb(24, 54, 145),
    subst: rgb(51, 51, 51),
};
// Keywords that syntect scopes as storage.type rather than keyword.control.
// highlight.js lumps these under "keyword"; we re-split so const/function/etc.
// get the cyan storage color instead of pink.
const STORAGE_KEYWORDS = new Set([
    'const',
    'let',
    'var',
    'function',
    'class',
    'type',
    'interface',
    'enum',
    'namespace',
    'module',
    'def',
    'fn',
    'func',
    'struct',
    'trait',
    'impl',
]);
const ANSI_SCOPES = {
    keyword: ansiIdx(13),
    _storage: ansiIdx(14),
    built_in: ansiIdx(14),
    type: ansiIdx(14),
    literal: ansiIdx(12),
    number: ansiIdx(12),
    string: ansiIdx(10),
    title: ansiIdx(11),
    'title.function': ansiIdx(11),
    'title.class': ansiIdx(11),
    comment: ansiIdx(8),
    meta: ansiIdx(8),
};
function buildTheme(themeName, mode) {
    const isDark = themeName.includes('dark');
    const isAnsi = themeName.includes('ansi');
    const isDaltonized = themeName.includes('daltonized');
    const tc = mode === 'truecolor';
    if (isAnsi) {
        return {
            addLine: DEFAULT_BG,
            addWord: DEFAULT_BG,
            addDecoration: ansiIdx(10),
            deleteLine: DEFAULT_BG,
            deleteWord: DEFAULT_BG,
            deleteDecoration: ansiIdx(9),
            foreground: ansiIdx(7),
            background: DEFAULT_BG,
            scopes: ANSI_SCOPES,
        };
    }
    if (isDark) {
        const fg = rgb(248, 248, 242);
        const deleteLine = rgb(61, 1, 0);
        const deleteWord = rgb(92, 2, 0);
        const deleteDecoration = rgb(220, 90, 90);
        if (isDaltonized) {
            return {
                addLine: tc ? rgb(0, 27, 41) : ansiIdx(17),
                addWord: tc ? rgb(0, 48, 71) : ansiIdx(24),
                addDecoration: rgb(81, 160, 200),
                deleteLine,
                deleteWord,
                deleteDecoration,
                foreground: fg,
                background: DEFAULT_BG,
                scopes: MONOKAI_SCOPES,
            };
        }
        return {
            addLine: tc ? rgb(2, 40, 0) : ansiIdx(22),
            addWord: tc ? rgb(4, 71, 0) : ansiIdx(28),
            addDecoration: rgb(80, 200, 80),
            deleteLine,
            deleteWord,
            deleteDecoration,
            foreground: fg,
            background: DEFAULT_BG,
            scopes: MONOKAI_SCOPES,
        };
    }
    // light
    const fg = rgb(51, 51, 51);
    const deleteLine = rgb(255, 220, 220);
    const deleteWord = rgb(255, 199, 199);
    const deleteDecoration = rgb(207, 34, 46);
    if (isDaltonized) {
        return {
            addLine: rgb(219, 237, 255),
            addWord: rgb(179, 217, 255),
            addDecoration: rgb(36, 87, 138),
            deleteLine,
            deleteWord,
            deleteDecoration,
            foreground: fg,
            background: DEFAULT_BG,
            scopes: GITHUB_SCOPES,
        };
    }
    return {
        addLine: rgb(220, 255, 220),
        addWord: rgb(178, 255, 178),
        addDecoration: rgb(36, 138, 61),
        deleteLine,
        deleteWord,
        deleteDecoration,
        foreground: fg,
        background: DEFAULT_BG,
        scopes: GITHUB_SCOPES,
    };
}
function defaultStyle(theme) {
    return { foreground: theme.foreground, background: theme.background };
}
function lineBackground(marker, theme) {
    switch (marker) {
        case '+':
            return theme.addLine;
        case '-':
            return theme.deleteLine;
        case ' ':
            return theme.background;
    }
}
function wordBackground(marker, theme) {
    switch (marker) {
        case '+':
            return theme.addWord;
        case '-':
            return theme.deleteWord;
        case ' ':
            return theme.background;
    }
}
function decorationColor(marker, theme) {
    switch (marker) {
        case '+':
            return theme.addDecoration;
        case '-':
            return theme.deleteDecoration;
        case ' ':
            return theme.foreground;
    }
}
// Filename-based and extension-based language detection (approximates bat's
// SyntaxMapping + syntect's find_syntax_by_extension)
const FILENAME_LANGS = {
    Dockerfile: 'dockerfile',
    Makefile: 'makefile',
    Rakefile: 'ruby',
    Gemfile: 'ruby',
    CMakeLists: 'cmake',
};
function detectLanguage(filePath, firstLine) {
    const base = basename(filePath);
    const ext = extname(filePath).slice(1);
    // Filename-based lookup (handles Dockerfile, Makefile, CMakeLists.txt, etc.)
    const stem = base.split('.')[0] ?? '';
    const byName = FILENAME_LANGS[base] ?? FILENAME_LANGS[stem];
    if (byName && hljs().getLanguage(byName))
        return byName;
    if (ext) {
        const lang = hljs().getLanguage(ext);
        if (lang)
            return ext;
    }
    // Shebang / first-line detection (strip UTF-8 BOM)
    if (firstLine) {
        const line = firstLine.startsWith('\ufeff') ? firstLine.slice(1) : firstLine;
        if (line.startsWith('#!')) {
            if (line.includes('bash') || line.includes('/sh'))
                return 'bash';
            if (line.includes('python'))
                return 'python';
            if (line.includes('node'))
                return 'javascript';
            if (line.includes('ruby'))
                return 'ruby';
            if (line.includes('perl'))
                return 'perl';
        }
        if (line.startsWith('<?php'))
            return 'php';
        if (line.startsWith('<?xml'))
            return 'xml';
    }
    return null;
}
function scopeColor(scope, text, theme) {
    if (!scope)
        return theme.foreground;
    if (scope === 'keyword' && STORAGE_KEYWORDS.has(text.trim())) {
        return theme.scopes['_storage'] ?? theme.foreground;
    }
    return (theme.scopes[scope] ??
        theme.scopes[scope.split('.')[0]] ??
        theme.foreground);
}
function flattenHljs(node, theme, parentScope, out) {
    if (typeof node === 'string') {
        const fg = scopeColor(parentScope, node, theme);
        out.push([{ foreground: fg, background: theme.background }, node]);
        return;
    }
    const scope = node.scope ?? node.kind ?? parentScope;
    for (const child of node.children) {
        flattenHljs(child, theme, scope, out);
    }
}
// result.emitter is in the public HighlightResult type, but rootNode is
// internal to TokenTreeEmitter. Type guard validates the shape once so we
// fail loudly (via logError) instead of a silent try/catch swallow — the
// prior `as unknown as` cast hid a version mismatch (_emitter vs emitter,
// scope vs kind) behind a silent gray fallback.
function hasRootNode(emitter) {
    return (typeof emitter === 'object' &&
        emitter !== null &&
        'rootNode' in emitter &&
        typeof emitter.rootNode === 'object' &&
        emitter.rootNode !== null &&
        'children' in emitter.rootNode);
}
let loggedEmitterShapeError = false;
function highlightLine(state, line, theme) {
    // syntect-parity: feed a trailing \n so line comments terminate, then strip
    const code = line + '\n';
    if (!state.lang) {
        return [[defaultStyle(theme), code]];
    }
    let result;
    try {
        result = hljs().highlight(code, {
            language: state.lang,
            ignoreIllegals: true,
        });
    }
    catch {
        // hljs throws on unknown language despite ignoreIllegals
        return [[defaultStyle(theme), code]];
    }
    if (!hasRootNode(result.emitter)) {
        if (!loggedEmitterShapeError) {
            loggedEmitterShapeError = true;
            logError(new Error(`color-diff: hljs emitter shape mismatch (keys: ${Object.keys(result.emitter).join(',')}). Syntax highlighting disabled.`));
        }
        return [[defaultStyle(theme), code]];
    }
    const blocks = [];
    flattenHljs(result.emitter.rootNode, theme, undefined, blocks);
    return blocks;
}
const CHANGE_THRESHOLD = 0.4;
// Tokenize into word runs, whitespace runs, and single punctuation chars —
// matches the Rust tokenize() which mirrors diffWordsWithSpace's splitting.
function tokenize(text) {
    const tokens = [];
    let i = 0;
    while (i < text.length) {
        const ch = text[i];
        if (/[\p{L}\p{N}_]/u.test(ch)) {
            let j = i + 1;
            while (j < text.length && /[\p{L}\p{N}_]/u.test(text[j]))
                j++;
            tokens.push(text.slice(i, j));
            i = j;
        }
        else if (/\s/.test(ch)) {
            let j = i + 1;
            while (j < text.length && /\s/.test(text[j]))
                j++;
            tokens.push(text.slice(i, j));
            i = j;
        }
        else {
            // advance one codepoint (handle surrogate pairs)
            const cp = text.codePointAt(i);
            const len = cp > 0xffff ? 2 : 1;
            tokens.push(text.slice(i, i + len));
            i += len;
        }
    }
    return tokens;
}
function findAdjacentPairs(markers) {
    const pairs = [];
    let i = 0;
    while (i < markers.length) {
        if (markers[i] === '-') {
            const delStart = i;
            let delEnd = i;
            while (delEnd < markers.length && markers[delEnd] === '-')
                delEnd++;
            let addEnd = delEnd;
            while (addEnd < markers.length && markers[addEnd] === '+')
                addEnd++;
            const delCount = delEnd - delStart;
            const addCount = addEnd - delEnd;
            if (delCount > 0 && addCount > 0) {
                const n = Math.min(delCount, addCount);
                for (let k = 0; k < n; k++) {
                    pairs.push([delStart + k, delEnd + k]);
                }
                i = addEnd;
            }
            else {
                i = delEnd;
            }
        }
        else {
            i++;
        }
    }
    return pairs;
}
function wordDiffStrings(oldStr, newStr) {
    const oldTokens = tokenize(oldStr);
    const newTokens = tokenize(newStr);
    const ops = diffArrays(oldTokens, newTokens);
    const totalLen = oldStr.length + newStr.length;
    let changedLen = 0;
    const oldRanges = [];
    const newRanges = [];
    let oldOff = 0;
    let newOff = 0;
    for (const op of ops) {
        const len = op.value.reduce((s, t) => s + t.length, 0);
        if (op.removed) {
            changedLen += len;
            oldRanges.push({ start: oldOff, end: oldOff + len });
            oldOff += len;
        }
        else if (op.added) {
            changedLen += len;
            newRanges.push({ start: newOff, end: newOff + len });
            newOff += len;
        }
        else {
            oldOff += len;
            newOff += len;
        }
    }
    if (totalLen > 0 && changedLen / totalLen > CHANGE_THRESHOLD) {
        return [[], []];
    }
    return [oldRanges, newRanges];
}
function removeNewlines(h) {
    h.lines = h.lines.map(line => line.flatMap(([style, text]) => text
        .split('\n')
        .filter(p => p.length > 0)
        .map((p) => [style, p])));
}
function charWidth(ch) {
    return stringWidth(ch);
}
function wrapText(h, width, theme) {
    const newLines = [];
    for (const line of h.lines) {
        const queue = line.slice();
        let cur = [];
        let curW = 0;
        while (queue.length > 0) {
            const [style, text] = queue.shift();
            const tw = stringWidth(text);
            if (curW + tw <= width) {
                cur.push([style, text]);
                curW += tw;
            }
            else {
                const remaining = width - curW;
                let bytePos = 0;
                let accW = 0;
                // iterate by codepoint
                for (const ch of text) {
                    const cw = charWidth(ch);
                    if (accW + cw > remaining)
                        break;
                    accW += cw;
                    bytePos += ch.length;
                }
                if (bytePos === 0) {
                    if (curW === 0) {
                        // Fresh line and first char still doesn't fit — force one codepoint
                        // to guarantee forward progress (overflows, but prevents infinite loop)
                        const firstCp = text.codePointAt(0);
                        bytePos = firstCp > 0xffff ? 2 : 1;
                    }
                    else {
                        // Line has content and next char doesn't fit — finish this line,
                        // re-queue the whole block for a fresh line
                        newLines.push(cur);
                        queue.unshift([style, text]);
                        cur = [];
                        curW = 0;
                        continue;
                    }
                }
                cur.push([style, text.slice(0, bytePos)]);
                newLines.push(cur);
                queue.unshift([style, text.slice(bytePos)]);
                cur = [];
                curW = 0;
            }
        }
        newLines.push(cur);
    }
    h.lines = newLines;
    // Pad changed lines so background extends to edge
    if (h.marker && h.marker !== ' ') {
        const bg = lineBackground(h.marker, theme);
        const padStyle = { foreground: theme.foreground, background: bg };
        for (const line of h.lines) {
            const curW = line.reduce((s, [, t]) => s + stringWidth(t), 0);
            if (curW < width) {
                line.push([padStyle, ' '.repeat(width - curW)]);
            }
        }
    }
}
function addLineNumber(h, theme, maxDigits, fullDim) {
    const style = {
        foreground: h.marker ? decorationColor(h.marker, theme) : theme.foreground,
        background: h.marker ? lineBackground(h.marker, theme) : theme.background,
    };
    const shouldDim = h.marker === null || h.marker === ' ';
    for (let i = 0; i < h.lines.length; i++) {
        const prefix = i === 0
            ? ` ${String(h.lineNumber).padStart(maxDigits)} `
            : ' '.repeat(maxDigits + 2);
        const wrapped = shouldDim && !fullDim ? `${DIM}${prefix}${UNDIM}` : prefix;
        h.lines[i].unshift([style, wrapped]);
    }
}
function addMarker(h, theme) {
    if (!h.marker)
        return;
    const style = {
        foreground: decorationColor(h.marker, theme),
        background: lineBackground(h.marker, theme),
    };
    for (const line of h.lines) {
        line.unshift([style, h.marker]);
    }
}
function dimContent(h) {
    for (const line of h.lines) {
        if (line.length > 0) {
            line[0][1] = DIM + line[0][1];
            const last = line.length - 1;
            line[last][1] = line[last][1] + UNDIM;
        }
    }
}
function applyBackground(h, theme, ranges) {
    if (!h.marker)
        return;
    const lineBg = lineBackground(h.marker, theme);
    const wordBg = wordBackground(h.marker, theme);
    let rangeIdx = 0;
    let byteOff = 0;
    for (let li = 0; li < h.lines.length; li++) {
        const newLine = [];
        for (const [style, text] of h.lines[li]) {
            const textStart = byteOff;
            const textEnd = byteOff + text.length;
            while (rangeIdx < ranges.length && ranges[rangeIdx].end <= textStart) {
                rangeIdx++;
            }
            if (rangeIdx >= ranges.length) {
                newLine.push([{ ...style, background: lineBg }, text]);
                byteOff = textEnd;
                continue;
            }
            let remaining = text;
            let pos = textStart;
            while (remaining.length > 0 && rangeIdx < ranges.length) {
                const r = ranges[rangeIdx];
                const inRange = pos >= r.start && pos < r.end;
                let next;
                if (inRange) {
                    next = Math.min(r.end, textEnd);
                }
                else if (r.start > pos && r.start < textEnd) {
                    next = r.start;
                }
                else {
                    next = textEnd;
                }
                const segLen = next - pos;
                const seg = remaining.slice(0, segLen);
                newLine.push([{ ...style, background: inRange ? wordBg : lineBg }, seg]);
                remaining = remaining.slice(segLen);
                pos = next;
                if (pos >= r.end)
                    rangeIdx++;
            }
            if (remaining.length > 0) {
                newLine.push([{ ...style, background: lineBg }, remaining]);
            }
            byteOff = textEnd;
        }
        h.lines[li] = newLine;
    }
}
function intoLines(h, dim, skipBg, mode) {
    return h.lines.map(line => asTerminalEscaped(line, mode, skipBg, dim));
}
// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------
function maxLineNumber(hunk) {
    const oldEnd = Math.max(0, hunk.oldStart + hunk.oldLines - 1);
    const newEnd = Math.max(0, hunk.newStart + hunk.newLines - 1);
    return Math.max(oldEnd, newEnd);
}
function parseMarker(s) {
    return s === '+' || s === '-' ? s : ' ';
}
export class ColorDiff {
    hunk;
    filePath;
    firstLine;
    prefixContent;
    constructor(hunk, firstLine, filePath, prefixContent) {
        this.hunk = hunk;
        this.filePath = filePath;
        this.firstLine = firstLine;
        this.prefixContent = prefixContent ?? null;
    }
    render(themeName, width, dim) {
        const mode = detectColorMode(themeName);
        const theme = buildTheme(themeName, mode);
        const lang = detectLanguage(this.filePath, this.firstLine);
        const hlState = { lang, stack: null };
        // Warm highlighter with prefix lines (highlight.js is stateless per call,
        // so this is a no-op for now — preserved for API parity)
        void this.prefixContent;
        const maxDigits = String(maxLineNumber(this.hunk)).length;
        let oldLine = this.hunk.oldStart;
        let newLine = this.hunk.newStart;
        const effectiveWidth = Math.max(1, width - maxDigits - 2 - 1);
        const entries = this.hunk.lines.map(rawLine => {
            const marker = parseMarker(rawLine.slice(0, 1));
            const code = rawLine.slice(1);
            let lineNumber;
            switch (marker) {
                case '+':
                    lineNumber = newLine++;
                    break;
                case '-':
                    lineNumber = oldLine++;
                    break;
                case ' ':
                    lineNumber = newLine;
                    oldLine++;
                    newLine++;
                    break;
            }
            return { lineNumber, marker, code };
        });
        // Word-diff ranges (skip when dim — too loud)
        const ranges = entries.map(() => []);
        if (!dim) {
            const markers = entries.map(e => e.marker);
            for (const [delIdx, addIdx] of findAdjacentPairs(markers)) {
                const [delR, addR] = wordDiffStrings(entries[delIdx].code, entries[addIdx].code);
                ranges[delIdx] = delR;
                ranges[addIdx] = addR;
            }
        }
        // Second pass: highlight + transform pipeline
        const out = [];
        for (let i = 0; i < entries.length; i++) {
            const { lineNumber, marker, code } = entries[i];
            const tokens = marker === '-'
                ? [[defaultStyle(theme), code]]
                : highlightLine(hlState, code, theme);
            const h = { marker, lineNumber, lines: [tokens] };
            removeNewlines(h);
            applyBackground(h, theme, ranges[i]);
            wrapText(h, effectiveWidth, theme);
            if (mode === 'ansi' && marker === '-') {
                dimContent(h);
            }
            addMarker(h, theme);
            addLineNumber(h, theme, maxDigits, dim);
            out.push(...intoLines(h, dim, false, mode));
        }
        return out;
    }
}
export class ColorFile {
    code;
    filePath;
    constructor(code, filePath) {
        this.code = code;
        this.filePath = filePath;
    }
    render(themeName, width, dim) {
        const mode = detectColorMode(themeName);
        const theme = buildTheme(themeName, mode);
        const lines = this.code.split('\n');
        // Rust .lines() drops trailing empty line from trailing \n
        if (lines.length > 0 && lines[lines.length - 1] === '')
            lines.pop();
        const firstLine = lines[0] ?? null;
        const lang = detectLanguage(this.filePath, firstLine);
        const hlState = { lang, stack: null };
        const maxDigits = String(lines.length).length;
        const effectiveWidth = Math.max(1, width - maxDigits - 2);
        const out = [];
        for (let i = 0; i < lines.length; i++) {
            const tokens = highlightLine(hlState, lines[i], theme);
            const h = { marker: null, lineNumber: i + 1, lines: [tokens] };
            removeNewlines(h);
            wrapText(h, effectiveWidth, theme);
            addLineNumber(h, theme, maxDigits, dim);
            out.push(...intoLines(h, dim, true, mode));
        }
        return out;
    }
}
export function getSyntaxTheme(themeName) {
    // highlight.js has no bat theme set, so env vars can't select alternate
    // syntect themes. We still report the env var if set, for diagnostics.
    const envTheme = process.env.CLAUDE_CODE_SYNTAX_HIGHLIGHT ?? process.env.BAT_THEME;
    void envTheme;
    return { theme: defaultSyntaxThemeName(themeName), source: null };
}
// Lazy loader to match vendor/color-diff-src/index.ts API
let cachedModule = null;
export function getNativeModule() {
    if (cachedModule)
        return cachedModule;
    cachedModule = { ColorDiff, ColorFile, getSyntaxTheme };
    return cachedModule;
}
// Exported for testing
export const __test = {
    tokenize,
    findAdjacentPairs,
    wordDiffStrings,
    ansi256FromRgb,
    colorToEscape,
    detectColorMode,
    detectLanguage,
};
