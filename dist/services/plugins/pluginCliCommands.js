/**
 * CLI command wrappers for plugin operations
 *
 * This module provides thin wrappers around the core plugin operations
 * that handle CLI-specific concerns like console output and process exit.
 *
 * For the core operations (without CLI side effects), see pluginOperations.ts
 */
import figures from 'figures';
import { errorMessage } from '../../utils/errors.js';
import { gracefulShutdown } from '../../utils/gracefulShutdown.js';
import { logError } from '../../utils/log.js';
import { getManagedPluginNames } from '../../utils/plugins/managedPlugins.js';
import { parsePluginIdentifier } from '../../utils/plugins/pluginIdentifier.js';
import { writeToStdout } from '../../utils/process.js';
import { buildPluginTelemetryFields, classifyPluginCommandError, } from '../../utils/telemetry/pluginTelemetry.js';
import { logEvent, } from '../analytics/index.js';
import { disableAllPluginsOp, disablePluginOp, enablePluginOp, installPluginOp, uninstallPluginOp, updatePluginOp, VALID_INSTALLABLE_SCOPES, VALID_UPDATE_SCOPES, } from './pluginOperations.js';
export { VALID_INSTALLABLE_SCOPES, VALID_UPDATE_SCOPES };
/**
 * Generic error handler for plugin CLI commands. Emits
 * tengu_plugin_command_failed before exit so dashboards can compute a
 * success rate against the corresponding success events.
 */
function handlePluginCommandError(error, command, plugin) {
    logError(error);
    const operation = plugin
        ? `${command} plugin "${plugin}"`
        : command === 'disable-all'
            ? 'disable all plugins'
            : `${command} plugins`;
    // biome-ignore lint/suspicious/noConsole:: intentional console output
    console.error(`${figures.cross} Failed to ${operation}: ${errorMessage(error)}`);
    const telemetryFields = plugin
        ? (() => {
            const { name, marketplace } = parsePluginIdentifier(plugin);
            return {
                _PROTO_plugin_name: name,
                ...(marketplace && {
                    _PROTO_marketplace_name: marketplace,
                }),
                ...buildPluginTelemetryFields(name, marketplace, getManagedPluginNames()),
            };
        })()
        : {};
    logEvent('tengu_plugin_command_failed', {
        command: command,
        error_category: classifyPluginCommandError(error),
        ...telemetryFields,
    });
    // eslint-disable-next-line custom-rules/no-process-exit
    process.exit(1);
}
/**
 * CLI command: Install a plugin non-interactively
 * @param plugin Plugin identifier (name or plugin@marketplace)
 * @param scope Installation scope: user, project, or local (defaults to 'user')
 */
export async function installPlugin(plugin, scope = 'user') {
    try {
        // biome-ignore lint/suspicious/noConsole:: intentional console output
        console.log(`Installing plugin "${plugin}"...`);
        const result = await installPluginOp(plugin, scope);
        if (!result.success) {
            throw new Error(result.message);
        }
        // biome-ignore lint/suspicious/noConsole:: intentional console output
        console.log(`${figures.tick} ${result.message}`);
        // _PROTO_* routes to PII-tagged plugin_name/marketplace_name BQ columns.
        // Unredacted plugin_id was previously logged to general-access
        // additional_metadata for all users — dropped in favor of the privileged
        // column route.
        const { name, marketplace } = parsePluginIdentifier(result.pluginId || plugin);
        logEvent('tengu_plugin_installed_cli', {
            _PROTO_plugin_name: name,
            ...(marketplace && {
                _PROTO_marketplace_name: marketplace,
            }),
            scope: (result.scope ||
                scope),
            install_source: 'cli-explicit',
            ...buildPluginTelemetryFields(name, marketplace, getManagedPluginNames()),
        });
        // eslint-disable-next-line custom-rules/no-process-exit
        process.exit(0);
    }
    catch (error) {
        handlePluginCommandError(error, 'install', plugin);
    }
}
/**
 * CLI command: Uninstall a plugin non-interactively
 * @param plugin Plugin name or plugin@marketplace identifier
 * @param scope Uninstall from scope: user, project, or local (defaults to 'user')
 */
export async function uninstallPlugin(plugin, scope = 'user', keepData = false) {
    try {
        const result = await uninstallPluginOp(plugin, scope, !keepData);
        if (!result.success) {
            throw new Error(result.message);
        }
        // biome-ignore lint/suspicious/noConsole:: intentional console output
        console.log(`${figures.tick} ${result.message}`);
        const { name, marketplace } = parsePluginIdentifier(result.pluginId || plugin);
        logEvent('tengu_plugin_uninstalled_cli', {
            _PROTO_plugin_name: name,
            ...(marketplace && {
                _PROTO_marketplace_name: marketplace,
            }),
            scope: (result.scope ||
                scope),
            ...buildPluginTelemetryFields(name, marketplace, getManagedPluginNames()),
        });
        // eslint-disable-next-line custom-rules/no-process-exit
        process.exit(0);
    }
    catch (error) {
        handlePluginCommandError(error, 'uninstall', plugin);
    }
}
/**
 * CLI command: Enable a plugin non-interactively
 * @param plugin Plugin name or plugin@marketplace identifier
 * @param scope Optional scope. If not provided, finds the most specific scope for the current project.
 */
export async function enablePlugin(plugin, scope) {
    try {
        const result = await enablePluginOp(plugin, scope);
        if (!result.success) {
            throw new Error(result.message);
        }
        // biome-ignore lint/suspicious/noConsole:: intentional console output
        console.log(`${figures.tick} ${result.message}`);
        const { name, marketplace } = parsePluginIdentifier(result.pluginId || plugin);
        logEvent('tengu_plugin_enabled_cli', {
            _PROTO_plugin_name: name,
            ...(marketplace && {
                _PROTO_marketplace_name: marketplace,
            }),
            scope: result.scope,
            ...buildPluginTelemetryFields(name, marketplace, getManagedPluginNames()),
        });
        // eslint-disable-next-line custom-rules/no-process-exit
        process.exit(0);
    }
    catch (error) {
        handlePluginCommandError(error, 'enable', plugin);
    }
}
/**
 * CLI command: Disable a plugin non-interactively
 * @param plugin Plugin name or plugin@marketplace identifier
 * @param scope Optional scope. If not provided, finds the most specific scope for the current project.
 */
export async function disablePlugin(plugin, scope) {
    try {
        const result = await disablePluginOp(plugin, scope);
        if (!result.success) {
            throw new Error(result.message);
        }
        // biome-ignore lint/suspicious/noConsole:: intentional console output
        console.log(`${figures.tick} ${result.message}`);
        const { name, marketplace } = parsePluginIdentifier(result.pluginId || plugin);
        logEvent('tengu_plugin_disabled_cli', {
            _PROTO_plugin_name: name,
            ...(marketplace && {
                _PROTO_marketplace_name: marketplace,
            }),
            scope: result.scope,
            ...buildPluginTelemetryFields(name, marketplace, getManagedPluginNames()),
        });
        // eslint-disable-next-line custom-rules/no-process-exit
        process.exit(0);
    }
    catch (error) {
        handlePluginCommandError(error, 'disable', plugin);
    }
}
/**
 * CLI command: Disable all enabled plugins non-interactively
 */
export async function disableAllPlugins() {
    try {
        const result = await disableAllPluginsOp();
        if (!result.success) {
            throw new Error(result.message);
        }
        // biome-ignore lint/suspicious/noConsole:: intentional console output
        console.log(`${figures.tick} ${result.message}`);
        logEvent('tengu_plugin_disabled_all_cli', {});
        // eslint-disable-next-line custom-rules/no-process-exit
        process.exit(0);
    }
    catch (error) {
        handlePluginCommandError(error, 'disable-all');
    }
}
/**
 * CLI command: Update a plugin non-interactively
 * @param plugin Plugin name or plugin@marketplace identifier
 * @param scope Scope to update
 */
export async function updatePluginCli(plugin, scope) {
    try {
        writeToStdout(`Checking for updates for plugin "${plugin}" at ${scope} scope…\n`);
        const result = await updatePluginOp(plugin, scope);
        if (!result.success) {
            throw new Error(result.message);
        }
        writeToStdout(`${figures.tick} ${result.message}\n`);
        if (!result.alreadyUpToDate) {
            const { name, marketplace } = parsePluginIdentifier(result.pluginId || plugin);
            logEvent('tengu_plugin_updated_cli', {
                _PROTO_plugin_name: name,
                ...(marketplace && {
                    _PROTO_marketplace_name: marketplace,
                }),
                old_version: (result.oldVersion ||
                    'unknown'),
                new_version: (result.newVersion ||
                    'unknown'),
                ...buildPluginTelemetryFields(name, marketplace, getManagedPluginNames()),
            });
        }
        await gracefulShutdown(0);
    }
    catch (error) {
        handlePluginCommandError(error, 'update', plugin);
    }
}
