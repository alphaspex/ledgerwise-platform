/**
 * Inputs :
 *   - props: { onStart: (selection: string) => Promise<void>; disabled: boolean; loading: boolean }
 *   - RESEARCH_TARGET: number (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (empty multi-line TextInput for the selection text, fixed line 'Target: 30 approved companies', Start Button; Start is disabled when disabled is true or the text is blank; calls onStart(trimmed text))
 * File explanation : Form to start a research run.
 */
