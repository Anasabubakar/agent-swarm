import { z } from 'zod';
import { logForDebugging } from '../debug.js';
import { lazySchema } from '../lazySchema.js';
import { createSignal } from '../signal.js';
import { jsonParse } from '../slowOperations.js';
const SLACK_SEARCH_TOOL = 'slack_search_channels';
// Plain Map (not LRUCache) — findReusableCacheEntry needs to iterate all
// entries for prefix matching, which LRUCache doesn't expose cleanly.
const cache = new Map();
// Flat set of every channel name ever returned by MCP — used to gate
// highlighting so only confirmed-real channels turn blue in the prompt.
const knownChannels = new Set();
let knownChannelsVersion = 0;
const knownChannelsChanged = createSignal();
export const subscribeKnownChannels = knownChannelsChanged.subscribe;
let inflightQuery = null;
let inflightPromise = null;
function findSlackClient(clients) {
    return clients.find(c => c.type === 'connected' && c.name.includes('slack'));
}
async function fetchChannels(clients, query) {
    const slackClient = findSlackClient(clients);
    if (!slackClient || slackClient.type !== 'connected') {
        return [];
    }
    try {
        const result = await slackClient.client.callTool({
            name: SLACK_SEARCH_TOOL,
            arguments: {
                query,
                limit: 20,
                channel_types: 'public_channel,private_channel',
            },
        }, undefined, { timeout: 5000 });
        const content = result.content;
        if (!Array.isArray(content))
            return [];
        const rawText = content
            .filter((c) => c.type === 'text')
            .map(c => c.text)
            .join('\n');
        return parseChannels(unwrapResults(rawText));
    }
    catch (error) {
        logForDebugging(`Failed to fetch Slack channels: ${error}`);
        return [];
    }
}
// The Slack MCP server wraps its markdown in a JSON envelope:
// {"results":"# Search Results...\nName: #chan\n..."}
const resultsEnvelopeSchema = lazySchema(() => z.object({ results: z.string() }));
function unwrapResults(text) {
    const trimmed = text.trim();
    if (!trimmed.startsWith('{'))
        return text;
    try {
        const parsed = resultsEnvelopeSchema().safeParse(jsonParse(trimmed));
        if (parsed.success)
            return parsed.data.results;
    }
    catch {
        // jsonParse threw — fall through
    }
    return text;
}
// Parse channel names from slack_search_channels text output.
// The Slack MCP server returns markdown with "Name: #channel-name" lines.
function parseChannels(text) {
    const channels = [];
    const seen = new Set();
    for (const line of text.split('\n')) {
        const m = line.match(/^Name:\s*#?([a-z0-9][a-z0-9_-]{0,79})\s*$/);
        if (m && !seen.has(m[1])) {
            seen.add(m[1]);
            channels.push(m[1]);
        }
    }
    return channels;
}
export function hasSlackMcpServer(clients) {
    return findSlackClient(clients) !== undefined;
}
export function getKnownChannelsVersion() {
    return knownChannelsVersion;
}
export function findSlackChannelPositions(text) {
    const positions = [];
    const re = /(^|\s)#([a-z0-9][a-z0-9_-]{0,79})(?=\s|$)/g;
    let m;
    while ((m = re.exec(text)) !== null) {
        if (!knownChannels.has(m[2]))
            continue;
        const start = m.index + m[1].length;
        positions.push({ start, end: start + 1 + m[2].length });
    }
    return positions;
}
// Slack's search tokenizes on hyphens and requires whole-word matches, so
// "claude-code-team-en" returns 0 results. Strip the trailing partial segment
// so the MCP query is "claude-code-team" (complete words only), then filter
// locally. This keeps the query maximally specific (avoiding the 20-result
// cap) while never sending a partial word that kills the search.
function mcpQueryFor(searchToken) {
    const lastSep = Math.max(searchToken.lastIndexOf('-'), searchToken.lastIndexOf('_'));
    return lastSep > 0 ? searchToken.slice(0, lastSep) : searchToken;
}
// Find a cached entry whose key is a prefix of mcpQuery and still has
// matches for searchToken. Lets typing "c"→"cl"→"cla" reuse the "c" cache
// instead of issuing a new MCP call per keystroke.
function findReusableCacheEntry(mcpQuery, searchToken) {
    let best;
    let bestLen = 0;
    for (const [key, channels] of cache) {
        if (mcpQuery.startsWith(key) &&
            key.length > bestLen &&
            channels.some(c => c.startsWith(searchToken))) {
            best = channels;
            bestLen = key.length;
        }
    }
    return best;
}
export async function getSlackChannelSuggestions(clients, searchToken) {
    if (!searchToken)
        return [];
    const mcpQuery = mcpQueryFor(searchToken);
    const lower = searchToken.toLowerCase();
    let channels = cache.get(mcpQuery) ?? findReusableCacheEntry(mcpQuery, lower);
    if (!channels) {
        if (inflightQuery === mcpQuery && inflightPromise) {
            channels = await inflightPromise;
        }
        else {
            inflightQuery = mcpQuery;
            inflightPromise = fetchChannels(clients, mcpQuery);
            channels = await inflightPromise;
            cache.set(mcpQuery, channels);
            const before = knownChannels.size;
            for (const c of channels)
                knownChannels.add(c);
            if (knownChannels.size !== before) {
                knownChannelsVersion++;
                knownChannelsChanged.emit();
            }
            if (cache.size > 50) {
                cache.delete(cache.keys().next().value);
            }
            if (inflightQuery === mcpQuery) {
                inflightQuery = null;
                inflightPromise = null;
            }
        }
    }
    return channels
        .filter(c => c.startsWith(lower))
        .sort()
        .slice(0, 10)
        .map(c => ({
        id: `slack-channel-${c}`,
        displayText: `#${c}`,
    }));
}
export function clearSlackChannelCache() {
    cache.clear();
    knownChannels.clear();
    knownChannelsVersion = 0;
    inflightQuery = null;
    inflightPromise = null;
}
