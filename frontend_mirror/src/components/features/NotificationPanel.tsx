/**
 * Inputs :
 *   - props: { notifications: Notification[]; onMarkAllRead: () => void; onSelect: (notification: Notification) => void }
 *   - NOTIFICATION_REASON_LABEL (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (scrollable list, newest first; each row: reason label, domain, body text (plain text), time, unread dot; header with a 'Mark all read' Button; EmptyState text when the list is empty)
 * File explanation : Content of the bell dropdown.
 */
