const hooks = {
    type: 'local-jsx',
    name: 'hooks',
    description: 'View hook configurations for tool events',
    immediate: true,
    load: () => import('./hooks.js'),
};
export default hooks;
