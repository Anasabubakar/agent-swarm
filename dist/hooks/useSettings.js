import { useAppState } from '../state/AppState.js';
/**
 * React hook to access current settings from AppState.
 * Settings automatically update when files change on disk via settingsChangeDetector.
 *
 * Use this instead of getSettings_DEPRECATED() in React components for reactive updates.
 */
export function useSettings() {
    return useAppState(s => s.settings);
}
