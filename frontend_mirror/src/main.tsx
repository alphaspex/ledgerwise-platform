/**
 * Inputs :
 *   - document.getElementById('root'): HTMLElement | null (from index.html)
 *   - ./index.css (side-effect import)
 * Outputs :
 *   - no exports; mounts <AppProvider><App /></AppProvider> into #root with createRoot
 * File explanation : Entry point of the app. Imports the global CSS, then renders the context provider wrapping App.
 */
