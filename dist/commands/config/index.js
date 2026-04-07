const config = {
    aliases: ['settings'],
    type: 'local-jsx',
    name: 'config',
    description: 'Open config panel',
    load: () => import('./config.js'),
};
export default config;
