/**
 * Inputs :
 *   - props: { children: ReactNode; onClick?: () => void; variant?: 'primary' | 'secondary' | 'danger' | 'ghost' (default 'primary'); type?: 'button' | 'submit' (default 'button'); loading?: boolean; disabled?: boolean; icon?: LucideIcon; fullWidth?: boolean }
 * Outputs :
 *   - JSX.Element (button; primary = gold gradient, secondary = slate outline; tap scale 0.97 and hover lift via Framer Motion; spinner when loading; not clickable when loading or disabled)
 * File explanation : The only button in the app.
 */
