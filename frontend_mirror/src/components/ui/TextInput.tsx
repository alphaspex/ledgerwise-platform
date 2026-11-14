/**
 * Inputs :
 *   - props: { label: string; value: string; onChange: (value: string) => void; type?: 'text' | 'email' | 'password' (default 'text'); multiline?: boolean; rows?: number; placeholder?: string; error?: string | null; maxLength?: number; autoFocus?: boolean; disabled?: boolean }
 * Outputs :
 *   - JSX.Element (labeled single-line input or textarea; focus ring in gold; red error text under it when error is set)
 * File explanation : The only text field in the app (also used as the multi-line editor). Content is plain text only.
 */
