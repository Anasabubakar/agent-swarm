import { performHeapDump } from '../../utils/heapDumpService.js';
export async function call() {
    const result = await performHeapDump();
    if (!result.success) {
        return {
            type: 'text',
            value: `Failed to create heap dump: ${result.error}`,
        };
    }
    return {
        type: 'text',
        value: `${result.heapPath}\n${result.diagPath}`,
    };
}
