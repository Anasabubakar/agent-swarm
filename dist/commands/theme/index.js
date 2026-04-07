const theme = {
    type: 'local-jsx',
    name: 'theme',
    description: 'Change the theme',
    load: () => import('./theme.js'),
};
export default theme;
