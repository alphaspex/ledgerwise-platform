/**
 * Inputs :
 *   - props: { open: boolean; title: string; onClose: () => void; children: ReactNode; footer?: ReactNode }
 * Outputs :
 *   - JSX.Element (dimmed backdrop + centered panel, scale/fade animated with AnimatePresence; closes on backdrop click and Escape; renders nothing when open is false)
 * File explanation : Generic dialog used for confirmations and the mobile 'More' menu.
 */
