import { openBrowser } from '../../utils/browser.js';
export async function call() {
    const url = 'https://www.stickermule.com/claudecode';
    const success = await openBrowser(url);
    if (success) {
        return { type: 'text', value: 'Opening sticker page in browser…' };
    }
    else {
        return {
            type: 'text',
            value: `Failed to open browser. Visit: ${url}`,
        };
    }
}
