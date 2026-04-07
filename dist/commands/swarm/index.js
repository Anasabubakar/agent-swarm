import { spawn } from 'child_process';
import { join } from 'path';
import { getProjectRoot } from '../../bootstrap/state.js';
const swarm = {
    name: 'swarm',
    description: 'Run the multi-agent orchestrator for a complex goal',
    usage: '[goal]',
    isEnabled: () => true,
    isHidden: () => false,
    run: async ({ args, stdout }) => {
        const goal = args.join(' ');
        if (!goal) {
            stdout.write('Please provide a goal for the swarm.\n');
            return;
        }
        const projectRoot = getProjectRoot();
        const orchestratorPath = join(projectRoot, 'orchestrator.py');
        stdout.write(`🚀 Launching Swarm for goal: ${goal}\n`);
        return new Promise((resolve) => {
            const child = spawn('python3', [orchestratorPath, goal], {
                cwd: process.cwd(),
                stdio: 'inherit',
            });
            child.on('exit', (code) => {
                resolve();
            });
        });
    },
};
export default swarm;
