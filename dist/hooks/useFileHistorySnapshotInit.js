import { useEffect, useRef } from 'react';
import { fileHistoryEnabled, fileHistoryRestoreStateFromLog, } from '../utils/fileHistory.js';
export function useFileHistorySnapshotInit(initialFileHistorySnapshots, fileHistoryState, onUpdateState) {
    const initialized = useRef(false);
    useEffect(() => {
        if (!fileHistoryEnabled() || initialized.current) {
            return;
        }
        initialized.current = true;
        if (initialFileHistorySnapshots) {
            fileHistoryRestoreStateFromLog(initialFileHistorySnapshots, onUpdateState);
        }
    }, [fileHistoryState, initialFileHistorySnapshots, onUpdateState]);
}
