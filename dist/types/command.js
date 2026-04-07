/** Resolves the user-visible name, falling back to `cmd.name` when not overridden. */
export function getCommandName(cmd) {
    return cmd.userFacingName?.() ?? cmd.name;
}
/** Resolves whether the command is enabled, defaulting to true. */
export function isCommandEnabled(cmd) {
    return cmd.isEnabled?.() ?? true;
}
