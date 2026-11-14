/**
 * Inputs :
 *   - none
 *   - context.toasts: Toast[] and context.dismissToast(id: number): void via useApp()
 *   - TOAST_DURATION_MS: number (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (fixed stack of toasts; each slides in, auto-dismisses after TOAST_DURATION_MS, colored by ToastKind)
 * File explanation : Displays toast notifications. Mounted once in App.tsx.
 */
