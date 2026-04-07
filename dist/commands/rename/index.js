const rename = {
    type: 'local-jsx',
    name: 'rename',
    description: 'Rename the current conversation',
    immediate: true,
    argumentHint: '[name]',
    load: () => import('./rename.js'),
};
export default rename;
