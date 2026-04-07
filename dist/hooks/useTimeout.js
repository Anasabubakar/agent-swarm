import { useEffect, useState } from 'react';
export function useTimeout(delay, resetTrigger) {
    const [isElapsed, setIsElapsed] = useState(false);
    useEffect(() => {
        setIsElapsed(false);
        const timer = setTimeout(setIsElapsed, delay, true);
        return () => clearTimeout(timer);
    }, [delay, resetTrigger]);
    return isElapsed;
}
