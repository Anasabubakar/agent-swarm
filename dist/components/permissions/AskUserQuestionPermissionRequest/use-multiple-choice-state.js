import { useCallback, useReducer } from 'react';
function reducer(state, action) {
    switch (action.type) {
        case 'next-question':
            return {
                ...state,
                currentQuestionIndex: state.currentQuestionIndex + 1,
                isInTextInput: false,
            };
        case 'prev-question':
            return {
                ...state,
                currentQuestionIndex: Math.max(0, state.currentQuestionIndex - 1),
                isInTextInput: false,
            };
        case 'update-question-state': {
            const existing = state.questionStates[action.questionText];
            const newState = {
                selectedValue: action.updates.selectedValue ??
                    existing?.selectedValue ??
                    (action.isMultiSelect ? [] : undefined),
                textInputValue: action.updates.textInputValue ?? existing?.textInputValue ?? '',
            };
            return {
                ...state,
                questionStates: {
                    ...state.questionStates,
                    [action.questionText]: newState,
                },
            };
        }
        case 'set-answer': {
            const newState = {
                ...state,
                answers: {
                    ...state.answers,
                    [action.questionText]: action.answer,
                },
            };
            if (action.shouldAdvance) {
                return {
                    ...newState,
                    currentQuestionIndex: newState.currentQuestionIndex + 1,
                    isInTextInput: false,
                };
            }
            return newState;
        }
        case 'set-text-input-mode':
            return {
                ...state,
                isInTextInput: action.isInInput,
            };
    }
}
const INITIAL_STATE = {
    currentQuestionIndex: 0,
    answers: {},
    questionStates: {},
    isInTextInput: false,
};
export function useMultipleChoiceState() {
    const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
    const nextQuestion = useCallback(() => {
        dispatch({ type: 'next-question' });
    }, []);
    const prevQuestion = useCallback(() => {
        dispatch({ type: 'prev-question' });
    }, []);
    const updateQuestionState = useCallback((questionText, updates, isMultiSelect) => {
        dispatch({
            type: 'update-question-state',
            questionText,
            updates,
            isMultiSelect,
        });
    }, []);
    const setAnswer = useCallback((questionText, answer, shouldAdvance = true) => {
        dispatch({
            type: 'set-answer',
            questionText,
            answer,
            shouldAdvance,
        });
    }, []);
    const setTextInputMode = useCallback((isInInput) => {
        dispatch({ type: 'set-text-input-mode', isInInput });
    }, []);
    return {
        currentQuestionIndex: state.currentQuestionIndex,
        answers: state.answers,
        questionStates: state.questionStates,
        isInTextInput: state.isInTextInput,
        nextQuestion,
        prevQuestion,
        updateQuestionState,
        setAnswer,
        setTextInputMode,
    };
}
