import { useEffect } from 'react';
import { formatTotalCost, saveCurrentSessionCosts } from './cost-tracker.js';
import { hasConsoleBillingAccess } from './utils/billing.js';
export function useCostSummary(getFpsMetrics) {
    useEffect(() => {
        const f = () => {
            if (hasConsoleBillingAccess()) {
                process.stdout.write('\n' + formatTotalCost() + '\n');
            }
            saveCurrentSessionCosts(getFpsMetrics?.());
        };
        process.on('exit', f);
        return () => {
            process.off('exit', f);
        };
    }, []);
}
