const permissions = {
    type: 'local-jsx',
    name: 'permissions',
    aliases: ['allowed-tools'],
    description: 'Manage allow & deny tool permission rules',
    load: () => import('./permissions.js'),
};
export default permissions;
