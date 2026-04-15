import { register } from 'node:module';
import { fileURLToPath } from 'node:url';

register('./bun-loader.mjs', import.meta.url);
