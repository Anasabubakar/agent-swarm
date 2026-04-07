const files = {
    type: 'local',
    name: 'files',
    description: 'List all files currently in context',
    isEnabled: () => process.env.USER_TYPE === 'ant',
    supportsNonInteractive: true,
    load: () => import('./files.js'),
};
export default files;
