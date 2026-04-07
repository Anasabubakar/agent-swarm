import { useState } from 'react';
import { major, minor, patch } from 'semver';
export function getSemverPart(version) {
    return `${major(version, { loose: true })}.${minor(version, { loose: true })}.${patch(version, { loose: true })}`;
}
export function shouldShowUpdateNotification(updatedVersion, lastNotifiedSemver) {
    const updatedSemver = getSemverPart(updatedVersion);
    return updatedSemver !== lastNotifiedSemver;
}
export function useUpdateNotification(updatedVersion, initialVersion = MACRO.VERSION) {
    const [lastNotifiedSemver, setLastNotifiedSemver] = useState(() => getSemverPart(initialVersion));
    if (!updatedVersion) {
        return null;
    }
    const updatedSemver = getSemverPart(updatedVersion);
    if (updatedSemver !== lastNotifiedSemver) {
        setLastNotifiedSemver(updatedSemver);
        return updatedSemver;
    }
    return null;
}
