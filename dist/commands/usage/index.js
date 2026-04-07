export default {
    type: 'local-jsx',
    name: 'usage',
    description: 'Show plan usage limits',
    availability: ['claude-ai'],
    load: () => import('./usage.js'),
};
