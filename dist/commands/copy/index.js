const copy = {
    type: 'local-jsx',
    name: 'copy',
    description: "Copy Claude's last response to clipboard (or /copy N for the Nth-latest)",
    load: () => import('./copy.js'),
};
export default copy;
