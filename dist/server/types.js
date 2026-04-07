import { z } from 'zod/v4';
import { lazySchema } from '../utils/lazySchema.js';
export const connectResponseSchema = lazySchema(() => z.object({
    session_id: z.string(),
    ws_url: z.string(),
    work_dir: z.string().optional(),
}));
