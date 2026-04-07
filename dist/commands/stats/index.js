const stats = {
    type: 'local-jsx',
    name: 'stats',
    description: 'Show your Claude Code usage statistics and activity',
    load: () => import('./stats.js'),
};
export default stats;
