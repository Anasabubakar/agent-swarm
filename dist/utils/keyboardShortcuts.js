// Special characters that macOS Option+key produces, mapped to their
// keybinding equivalents. Used to detect Option+key shortcuts on macOS
// terminals that don't have "Option as Meta" enabled.
export const MACOS_OPTION_SPECIAL_CHARS = {
    '†': 'alt+t', // Option+T -> thinking toggle
    π: 'alt+p', // Option+P -> model picker
    ø: 'alt+o', // Option+O -> fast mode
};
export function isMacosOptionChar(char) {
    return char in MACOS_OPTION_SPECIAL_CHARS;
}
