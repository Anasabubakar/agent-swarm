const stickers = {
    type: 'local',
    name: 'stickers',
    description: 'Order Claude Code stickers',
    supportsNonInteractive: false,
    load: () => import('./stickers.js'),
};
export default stickers;
