/**
 * Selectors for deriving computed state from AppState.
 * Keep selectors pure and simple - just data extraction, no side effects.
 */
import { isInProcessTeammateTask } from '../tasks/InProcessTeammateTask/types.js';
/**
 * Get the currently viewed teammate task, if any.
 * Returns undefined if:
 * - No teammate is being viewed (viewingAgentTaskId is undefined)
 * - The task ID doesn't exist in tasks
 * - The task is not an in-process teammate task
 */
export function getViewedTeammateTask(appState) {
    const { viewingAgentTaskId, tasks } = appState;
    // Not viewing any teammate
    if (!viewingAgentTaskId) {
        return undefined;
    }
    // Look up the task
    const task = tasks[viewingAgentTaskId];
    if (!task) {
        return undefined;
    }
    // Verify it's an in-process teammate task
    if (!isInProcessTeammateTask(task)) {
        return undefined;
    }
    return task;
}
/**
 * Determine where user input should be routed.
 * Returns:
 * - { type: 'leader' } when not viewing a teammate (input goes to leader)
 * - { type: 'viewed', task } when viewing an agent (input goes to that agent)
 *
 * Used by input routing logic to direct user messages to the correct agent.
 */
export function getActiveAgentForInput(appState) {
    const viewedTask = getViewedTeammateTask(appState);
    if (viewedTask) {
        return { type: 'viewed', task: viewedTask };
    }
    const { viewingAgentTaskId, tasks } = appState;
    if (viewingAgentTaskId) {
        const task = tasks[viewingAgentTaskId];
        if (task?.type === 'local_agent') {
            return { type: 'named_agent', task };
        }
    }
    return { type: 'leader' };
}
