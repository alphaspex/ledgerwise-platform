/**
 * Inputs :
 *   - props: { children: ReactNode; onClick?: () => void; interactive?: boolean (hover lift); index?: number (stagger position, default 0); className?: string }
 * Outputs :
 *   - JSX.Element (surface card with shadow-card; fades and rises on mount with delay index * STAGGER_SECONDS)
 * File explanation : Base container for every card in the app (companies, drafts, threads, summary blocks).
 */
