/**
 * Inputs :
 *   - none
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 * Outputs :
 *   - { success: (text: string) => void; error: (text: string) => void; info: (text: string) => void }
 * File explanation : Thin convenience hook over context.pushToast so components call toast.success('Saved').
 */
