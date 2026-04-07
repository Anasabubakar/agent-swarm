export function sortLogs(logs) {
    return logs.sort((a, b) => {
        // Sort by modified date (newest first)
        const modifiedDiff = b.modified.getTime() - a.modified.getTime();
        if (modifiedDiff !== 0) {
            return modifiedDiff;
        }
        // If modified dates are equal, sort by created date (newest first)
        return b.created.getTime() - a.created.getTime();
    });
}
