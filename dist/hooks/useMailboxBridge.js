import { useCallback, useEffect, useMemo, useSyncExternalStore } from 'react';
import { useMailbox } from '../context/mailbox.js';
export function useMailboxBridge({ isLoading, onSubmitMessage }) {
    const mailbox = useMailbox();
    const subscribe = useMemo(() => mailbox.subscribe.bind(mailbox), [mailbox]);
    const getSnapshot = useCallback(() => mailbox.revision, [mailbox]);
    const revision = useSyncExternalStore(subscribe, getSnapshot);
    useEffect(() => {
        if (isLoading)
            return;
        const msg = mailbox.poll();
        if (msg)
            onSubmitMessage(msg.content);
    }, [isLoading, revision, mailbox, onSubmitMessage]);
}
