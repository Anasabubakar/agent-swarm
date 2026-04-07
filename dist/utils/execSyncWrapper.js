import { execSync as nodeExecSync, } from 'child_process';
import { slowLogging } from './slowOperations.js';
export function execSync_DEPRECATED(command, options) {
    using _ = slowLogging `execSync: ${command.slice(0, 100)}`;
    return nodeExecSync(command, options);
}
