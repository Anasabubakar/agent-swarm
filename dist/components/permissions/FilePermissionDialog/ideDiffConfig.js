export function createSingleEditDiffConfig(filePath, oldString, newString, replaceAll) {
    return {
        filePath,
        edits: [
            {
                old_string: oldString,
                new_string: newString,
                replace_all: replaceAll,
            },
        ],
        editMode: 'single',
    };
}
