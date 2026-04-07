import uniqBy from 'lodash-es/uniqBy.js';
import { useMemo } from 'react';
export function mergeClients(initialClients, mcpClients) {
    if (initialClients && mcpClients && mcpClients.length > 0) {
        return uniqBy([...initialClients, ...mcpClients], 'name');
    }
    return initialClients || [];
}
export function useMergedClients(initialClients, mcpClients) {
    return useMemo(() => mergeClients(initialClients, mcpClients), [initialClients, mcpClients]);
}
