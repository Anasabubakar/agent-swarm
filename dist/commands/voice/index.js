import { isVoiceGrowthBookEnabled, isVoiceModeEnabled, } from '../../voice/voiceModeEnabled.js';
const voice = {
    type: 'local',
    name: 'voice',
    description: 'Toggle voice mode',
    availability: ['claude-ai'],
    isEnabled: () => isVoiceGrowthBookEnabled(),
    get isHidden() {
        return !isVoiceModeEnabled();
    },
    supportsNonInteractive: false,
    load: () => import('./voice.js'),
};
export default voice;
