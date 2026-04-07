const outputStyle = {
    type: 'local-jsx',
    name: 'output-style',
    description: 'Deprecated: use /config to change output style',
    isHidden: true,
    load: () => import('./output-style.js'),
};
export default outputStyle;
