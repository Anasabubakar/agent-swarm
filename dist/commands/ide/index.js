const ide = {
    type: 'local-jsx',
    name: 'ide',
    description: 'Manage IDE integrations and show status',
    argumentHint: '[open]',
    load: () => import('./ide.js'),
};
export default ide;
