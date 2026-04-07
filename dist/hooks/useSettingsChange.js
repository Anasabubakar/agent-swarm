import { useCallback, useEffect } from 'react';
import { settingsChangeDetector } from '../utils/settings/changeDetector.js';
import { getSettings_DEPRECATED } from '../utils/settings/settings.js';
export function useSettingsChange(onChange) {
    const handleChange = useCallback((source) => {
        // Cache is already reset by the notifier (changeDetector.fanOut) —
        // resetting here caused N-way thrashing with N subscribers: each
        // cleared the cache, re-read from disk, then the next cleared again.
        const newSettings = getSettings_DEPRECATED();
        onChange(source, newSettings);
    }, [onChange]);
    useEffect(() => settingsChangeDetector.subscribe(handleChange), [handleChange]);
}
