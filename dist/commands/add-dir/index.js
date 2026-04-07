const addDir = {
    type: 'local-jsx',
    name: 'add-dir',
    description: 'Add a new working directory',
    argumentHint: '<path>',
    load: () => import('./add-dir.js'),
};
export default addDir;
