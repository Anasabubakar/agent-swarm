const command = {
    name: 'vim',
    description: 'Toggle between Vim and Normal editing modes',
    supportsNonInteractive: false,
    type: 'local',
    load: () => import('./vim.js'),
};
export default command;
