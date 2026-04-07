import { logForDebugging } from '../debug.js';
import { logError } from '../log.js';
export class ClaudeCodeDiagLogger {
    error(message, ..._) {
        logError(new Error(message));
        logForDebugging(`[3P telemetry] OTEL diag error: ${message}`, {
            level: 'error',
        });
    }
    warn(message, ..._) {
        logError(new Error(message));
        logForDebugging(`[3P telemetry] OTEL diag warn: ${message}`, {
            level: 'warn',
        });
    }
    info(_message, ..._args) {
        return;
    }
    debug(_message, ..._args) {
        return;
    }
    verbose(_message, ..._args) {
        return;
    }
}
