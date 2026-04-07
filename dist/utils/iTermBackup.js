import { copyFile, stat } from 'fs/promises';
import { homedir } from 'os';
import { join } from 'path';
import { getGlobalConfig, saveGlobalConfig } from './config.js';
import { logError } from './log.js';
export function markITerm2SetupComplete() {
    saveGlobalConfig(current => ({
        ...current,
        iterm2SetupInProgress: false,
    }));
}
function getIterm2RecoveryInfo() {
    const config = getGlobalConfig();
    return {
        inProgress: config.iterm2SetupInProgress ?? false,
        backupPath: config.iterm2BackupPath || null,
    };
}
function getITerm2PlistPath() {
    return join(homedir(), 'Library', 'Preferences', 'com.googlecode.iterm2.plist');
}
export async function checkAndRestoreITerm2Backup() {
    const { inProgress, backupPath } = getIterm2RecoveryInfo();
    if (!inProgress) {
        return { status: 'no_backup' };
    }
    if (!backupPath) {
        markITerm2SetupComplete();
        return { status: 'no_backup' };
    }
    try {
        await stat(backupPath);
    }
    catch {
        markITerm2SetupComplete();
        return { status: 'no_backup' };
    }
    try {
        await copyFile(backupPath, getITerm2PlistPath());
        markITerm2SetupComplete();
        return { status: 'restored' };
    }
    catch (restoreError) {
        logError(new Error(`Failed to restore iTerm2 settings with: ${restoreError}`));
        markITerm2SetupComplete();
        return { status: 'failed', backupPath };
    }
}
