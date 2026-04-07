const heapDump = {
    type: 'local',
    name: 'heapdump',
    description: 'Dump the JS heap to ~/Desktop',
    isHidden: true,
    supportsNonInteractive: true,
    load: () => import('./heapdump.js'),
};
export default heapDump;
