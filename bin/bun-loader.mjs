import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const MOCKED_PACKAGES = [
  'bun:bundle',
  'color-diff-napi',
  '@ant/claude-for-chrome-mcp',
  '@ant/computer-use-mcp'
];

export async function resolve(specifier, context, nextResolve) {
  if (MOCKED_PACKAGES.includes(specifier) || specifier.startsWith('@ant/')) {
    return {
      format: 'module',
      shortCircuit: true,
      url: `data:text/javascript,export function feature() { return false; }; export default {};`
    };
  }

  try {
    return await nextResolve(specifier, context);
  } catch (e) {
    if (e.code === 'ERR_MODULE_NOT_FOUND') {
         return {
            format: 'module',
            shortCircuit: true,
            url: `data:text/javascript,export default {};`
        };
    }
    throw e;
  }
}

export async function load(url, context, nextLoad) {
  if (url.endsWith('.md') || url.endsWith('.txt')) {
    const content = await readFile(fileURLToPath(url), 'utf8');
    return {
      format: 'module',
      shortCircuit: true,
      source: `export default ${JSON.stringify(content)};`
    };
  }
  return nextLoad(url, context);
}
