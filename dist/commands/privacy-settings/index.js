import { isConsumerSubscriber } from '../../utils/auth.js';
const privacySettings = {
    type: 'local-jsx',
    name: 'privacy-settings',
    description: 'View and update your privacy settings',
    isEnabled: () => {
        return isConsumerSubscriber();
    },
    load: () => import('./privacy-settings.js'),
};
export default privacySettings;
