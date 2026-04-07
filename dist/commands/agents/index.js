const agents = {
    type: 'local-jsx',
    name: 'agents',
    description: 'Manage agent configurations',
    load: () => import('./agents.js'),
};
export default agents;
