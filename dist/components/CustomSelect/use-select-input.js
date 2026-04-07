import { useMemo } from 'react';
import { useRegisterOverlay } from '../../context/overlayContext.js';
import { useInput } from '../../ink.js';
import { useKeybindings } from '../../keybindings/useKeybinding.js';
import { normalizeFullWidthDigits, normalizeFullWidthSpace, } from '../../utils/stringUtils.js';
export const useSelectInput = ({ isDisabled = false, disableSelection = false, state, options, isMultiSelect = false, onUpFromFirstItem, onDownFromLastItem, onInputModeToggle, inputValues, imagesSelected = false, onEnterImageSelection, }) => {
    // Automatically register as an overlay when onCancel is provided.
    // This ensures CancelRequestHandler won't intercept Escape when the select is active.
    useRegisterOverlay('select', !!state.onCancel);
    // Determine if the focused option is an input type
    const isInInput = useMemo(() => {
        const focusedOption = options.find(opt => opt.value === state.focusedValue);
        return focusedOption?.type === 'input';
    }, [options, state.focusedValue]);
    // Core navigation via keybindings (up/down/enter/escape)
    // When in input mode, exclude navigation/accept keybindings so that
    // j/k/enter pass through to the TextInput instead of being intercepted.
    const keybindingHandlers = useMemo(() => {
        const handlers = {};
        if (!isInInput) {
            handlers['select:next'] = () => {
                if (onDownFromLastItem) {
                    const lastOption = options[options.length - 1];
                    if (lastOption && state.focusedValue === lastOption.value) {
                        onDownFromLastItem();
                        return;
                    }
                }
                state.focusNextOption();
            };
            handlers['select:previous'] = () => {
                if (onUpFromFirstItem && state.visibleFromIndex === 0) {
                    const firstOption = options[0];
                    if (firstOption && state.focusedValue === firstOption.value) {
                        onUpFromFirstItem();
                        return;
                    }
                }
                state.focusPreviousOption();
            };
            handlers['select:accept'] = () => {
                if (disableSelection === true)
                    return;
                if (state.focusedValue === undefined)
                    return;
                const focusedOption = options.find(opt => opt.value === state.focusedValue);
                if (focusedOption?.disabled === true)
                    return;
                state.selectFocusedOption?.();
                state.onChange?.(state.focusedValue);
            };
        }
        if (state.onCancel) {
            handlers['select:cancel'] = () => {
                state.onCancel();
            };
        }
        return handlers;
    }, [
        options,
        state,
        onDownFromLastItem,
        onUpFromFirstItem,
        isInInput,
        disableSelection,
    ]);
    useKeybindings(keybindingHandlers, {
        context: 'Select',
        isActive: !isDisabled,
    });
    // Remaining keys that stay as useInput: number keys, pageUp/pageDown, tab, space,
    // and arrow key navigation when in input mode
    useInput((input, key, event) => {
        const normalizedInput = normalizeFullWidthDigits(input);
        const focusedOption = options.find(opt => opt.value === state.focusedValue);
        const currentIsInInput = focusedOption?.type === 'input';
        // Handle Tab key for input mode toggling
        if (key.tab && onInputModeToggle && state.focusedValue !== undefined) {
            onInputModeToggle(state.focusedValue);
            return;
        }
        if (currentIsInInput) {
            // When in image selection mode, suppress all input handling so
            // Attachments keybindings can handle navigation/deletion instead
            if (imagesSelected)
                return;
            // DOWN arrow enters image selection mode if images exist
            if (key.downArrow && onEnterImageSelection?.()) {
                event.stopImmediatePropagation();
                return;
            }
            // Arrow keys still navigate the select even while in input mode
            if (key.downArrow || (key.ctrl && input === 'n')) {
                if (onDownFromLastItem) {
                    const lastOption = options[options.length - 1];
                    if (lastOption && state.focusedValue === lastOption.value) {
                        onDownFromLastItem();
                        event.stopImmediatePropagation();
                        return;
                    }
                }
                state.focusNextOption();
                event.stopImmediatePropagation();
                return;
            }
            if (key.upArrow || (key.ctrl && input === 'p')) {
                if (onUpFromFirstItem && state.visibleFromIndex === 0) {
                    const firstOption = options[0];
                    if (firstOption && state.focusedValue === firstOption.value) {
                        onUpFromFirstItem();
                        event.stopImmediatePropagation();
                        return;
                    }
                }
                state.focusPreviousOption();
                event.stopImmediatePropagation();
                return;
            }
            // All other keys (including digits) pass through to TextInput.
            // Digits should type literally into the input rather than select
            // options — the user has focused a text field and expects typing
            // to insert characters, not jump to a different option.
            return;
        }
        if (key.pageDown) {
            state.focusNextPage();
        }
        if (key.pageUp) {
            state.focusPreviousPage();
        }
        if (disableSelection !== true) {
            // Space for multi-select toggle
            if (isMultiSelect &&
                normalizeFullWidthSpace(input) === ' ' &&
                state.focusedValue !== undefined) {
                const isFocusedOptionDisabled = focusedOption?.disabled === true;
                if (!isFocusedOptionDisabled) {
                    state.selectFocusedOption?.();
                    state.onChange?.(state.focusedValue);
                }
            }
            if (disableSelection !== 'numeric' &&
                /^[0-9]+$/.test(normalizedInput)) {
                const index = parseInt(normalizedInput) - 1;
                if (index >= 0 && index < state.options.length) {
                    const selectedOption = state.options[index];
                    if (selectedOption.disabled === true) {
                        return;
                    }
                    if (selectedOption.type === 'input') {
                        const currentValue = inputValues?.get(selectedOption.value) ?? '';
                        if (currentValue.trim()) {
                            // Pre-filled input: auto-submit (user can Tab to edit instead)
                            state.onChange?.(selectedOption.value);
                            return;
                        }
                        if (selectedOption.allowEmptySubmitToCancel) {
                            state.onChange?.(selectedOption.value);
                            return;
                        }
                        state.focusOption(selectedOption.value);
                        return;
                    }
                    state.onChange?.(selectedOption.value);
                    return;
                }
            }
        }
    }, { isActive: !isDisabled });
};
