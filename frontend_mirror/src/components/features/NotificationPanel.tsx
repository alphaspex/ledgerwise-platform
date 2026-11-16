/**
 * Inputs :
 *   - props: { notifications: Notification[]; error: ApiError | null; onMarkAllRead: () => void; onSelect: (notification: Notification) => void }
 *   - NOTIFICATION_REASON_LABEL (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (scrollable notification list; error banner on failed polling; empty state only after a successful empty response)
 * File explanation : Content of the bell dropdown. Shows polling failures separately from an empty result and retains stale notifications.
 */
