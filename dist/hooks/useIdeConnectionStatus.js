import { useMemo } from 'react';
export function useIdeConnectionStatus(mcpClients) {
    return useMemo(() => {
        const ideClient = mcpClients?.find(client => client.name === 'ide');
        if (!ideClient) {
            return { status: null, ideName: null };
        }
        // Extract IDE name from config if available
        const config = ideClient.config;
        const ideName = config.type === 'sse-ide' || config.type === 'ws-ide'
            ? config.ideName
            : null;
        if (ideClient.type === 'connected') {
            return { status: 'connected', ideName };
        }
        if (ideClient.type === 'pending') {
            return { status: 'pending', ideName };
        }
        return { status: 'disconnected', ideName };
    }, [mcpClients]);
}
