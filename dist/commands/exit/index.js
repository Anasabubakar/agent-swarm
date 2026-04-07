const exit = {
    type: 'local-jsx',
    name: 'exit',
    aliases: ['quit'],
    description: 'Exit the REPL',
    immediate: true,
    load: () => import('./exit.js'),
};
export default exit;
