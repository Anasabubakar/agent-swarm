import Fuse from 'fuse.js';
import { basename } from 'path';
import { generateFileSuggestions } from 'src/hooks/fileSuggestions.js';
import { getAgentColor } from 'src/tools/AgentTool/agentColorManager.js';
import { truncateToWidth } from 'src/utils/format.js';
import { logError } from 'src/utils/log.js';
/**
 * Creates a unified suggestion item from a source
 */
function createSuggestionFromSource(source) {
    switch (source.type) {
        case 'file':
            return {
                id: `file-${source.path}`,
                displayText: source.displayText,
                description: source.description,
            };
        case 'mcp_resource':
            return {
                id: `mcp-resource-${source.server}__${source.uri}`,
                displayText: source.displayText,
                description: source.description,
            };
        case 'agent':
            return {
                id: `agent-${source.agentType}`,
                displayText: source.displayText,
                description: source.description,
                color: source.color,
            };
    }
}
const MAX_UNIFIED_SUGGESTIONS = 15;
const DESCRIPTION_MAX_LENGTH = 60;
function truncateDescription(description) {
    return truncateToWidth(description, DESCRIPTION_MAX_LENGTH);
}
function generateAgentSuggestions(agents, query, showOnEmpty = false) {
    if (!query && !showOnEmpty) {
        return [];
    }
    try {
        const agentSources = agents.map(agent => ({
            type: 'agent',
            displayText: `${agent.agentType} (agent)`,
            description: truncateDescription(agent.whenToUse),
            agentType: agent.agentType,
            color: getAgentColor(agent.agentType),
        }));
        if (!query) {
            return agentSources;
        }
        const queryLower = query.toLowerCase();
        return agentSources.filter(agent => agent.agentType.toLowerCase().includes(queryLower) ||
            agent.displayText.toLowerCase().includes(queryLower));
    }
    catch (error) {
        logError(error);
        return [];
    }
}
export async function generateUnifiedSuggestions(query, mcpResources, agents, showOnEmpty = false) {
    if (!query && !showOnEmpty) {
        return [];
    }
    const [fileSuggestions, agentSources] = await Promise.all([
        generateFileSuggestions(query, showOnEmpty),
        Promise.resolve(generateAgentSuggestions(agents, query, showOnEmpty)),
    ]);
    const fileSources = fileSuggestions.map(suggestion => ({
        type: 'file',
        displayText: suggestion.displayText,
        description: suggestion.description,
        path: suggestion.displayText, // Use displayText as path for files
        filename: basename(suggestion.displayText),
        score: suggestion.metadata?.score,
    }));
    const mcpSources = Object.values(mcpResources)
        .flat()
        .map(resource => ({
        type: 'mcp_resource',
        displayText: `${resource.server}:${resource.uri}`,
        description: truncateDescription(resource.description || resource.name || resource.uri),
        server: resource.server,
        uri: resource.uri,
        name: resource.name || resource.uri,
    }));
    if (!query) {
        const allSources = [...fileSources, ...mcpSources, ...agentSources];
        return allSources
            .slice(0, MAX_UNIFIED_SUGGESTIONS)
            .map(createSuggestionFromSource);
    }
    const nonFileSources = [...mcpSources, ...agentSources];
    const scoredResults = [];
    // Add file sources with their nucleo scores (already 0-1, lower is better)
    for (const fileSource of fileSources) {
        scoredResults.push({
            source: fileSource,
            score: fileSource.score ?? 0.5, // Default to middle score if missing
        });
    }
    // Score non-file sources with Fuse.js and add them
    if (nonFileSources.length > 0) {
        const fuse = new Fuse(nonFileSources, {
            includeScore: true,
            threshold: 0.6, // Allow more matches through, we'll sort by score
            keys: [
                { name: 'displayText', weight: 2 },
                { name: 'name', weight: 3 },
                { name: 'server', weight: 1 },
                { name: 'description', weight: 1 },
                { name: 'agentType', weight: 3 },
            ],
        });
        const fuseResults = fuse.search(query, { limit: MAX_UNIFIED_SUGGESTIONS });
        for (const result of fuseResults) {
            scoredResults.push({
                source: result.item,
                score: result.score ?? 0.5,
            });
        }
    }
    // Sort all results by score (lower is better) and return top results
    scoredResults.sort((a, b) => a.score - b.score);
    return scoredResults
        .slice(0, MAX_UNIFIED_SUGGESTIONS)
        .map(r => r.source)
        .map(createSuggestionFromSource);
}
