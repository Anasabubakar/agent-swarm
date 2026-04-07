import { getSkillToolCommands } from '../../commands.js';
import { logEvent, } from '../../services/analytics/index.js';
import { getCharBudget } from '../../tools/SkillTool/prompt.js';
/**
 * Logs a tengu_skill_loaded event for each skill available at session startup.
 * This enables analytics on which skills are available across sessions.
 */
export async function logSkillsLoaded(cwd, contextWindowTokens) {
    const skills = await getSkillToolCommands(cwd);
    const skillBudget = getCharBudget(contextWindowTokens);
    for (const skill of skills) {
        if (skill.type !== 'prompt')
            continue;
        logEvent('tengu_skill_loaded', {
            // _PROTO_skill_name routes to the privileged skill_name BQ column.
            // Unredacted names don't go in additional_metadata.
            _PROTO_skill_name: skill.name,
            skill_source: skill.source,
            skill_loaded_from: skill.loadedFrom,
            skill_budget: skillBudget,
            ...(skill.kind && {
                skill_kind: skill.kind,
            }),
        });
    }
}
