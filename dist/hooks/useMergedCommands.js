import uniqBy from 'lodash-es/uniqBy.js';
import { useMemo } from 'react';
export function useMergedCommands(initialCommands, mcpCommands) {
    return useMemo(() => {
        if (mcpCommands.length > 0) {
            return uniqBy([...initialCommands, ...mcpCommands], 'name');
        }
        return initialCommands;
    }, [initialCommands, mcpCommands]);
}
