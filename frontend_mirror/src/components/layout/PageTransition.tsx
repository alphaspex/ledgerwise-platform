/**
 * Inputs :
 *   - props: { screenKey: ScreenName; children: ReactNode }
 *   - PAGE_TRANSITION_SECONDS: number (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (AnimatePresence wrapper: old screen fades out, new screen fades in and slides up 12px, keyed by screenKey)
 * File explanation : Animates screen changes.
 */
