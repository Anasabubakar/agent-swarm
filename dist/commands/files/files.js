import { relative } from 'path';
import { getCwd } from '../../utils/cwd.js';
import { cacheKeys } from '../../utils/fileStateCache.js';
export async function call(_args, context) {
    const files = context.readFileState ? cacheKeys(context.readFileState) : [];
    if (files.length === 0) {
        return { type: 'text', value: 'No files in context' };
    }
    const fileList = files.map(file => relative(getCwd(), file)).join('\n');
    return { type: 'text', value: `Files in context:\n${fileList}` };
}
