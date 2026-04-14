import { createContext } from 'react';
/**
`AppContext` is a React context that exposes lifecycle methods for the app.
*/
// eslint-disable-next-line @typescript-eslint/naming-convention
const AppContext = createContext({
    exit() { },
    async waitUntilRenderFlush() { },
});
AppContext.displayName = 'InternalAppContext';
export default AppContext;
//# sourceMappingURL=AppContext.js.map