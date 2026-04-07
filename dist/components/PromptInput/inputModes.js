export function prependModeCharacterToInput(input, mode) {
    switch (mode) {
        case 'bash':
            return `!${input}`;
        default:
            return input;
    }
}
export function getModeFromInput(input) {
    if (input.startsWith('!')) {
        return 'bash';
    }
    return 'prompt';
}
export function getValueFromInput(input) {
    const mode = getModeFromInput(input);
    if (mode === 'prompt') {
        return input;
    }
    return input.slice(1);
}
export function isInputModeCharacter(input) {
    return input === '!';
}
