/**
 * Inputs :
 *   - props: { notifications: Notification[]; onMarkAllRead: () => void; onSelect: (notification: Notification) => void }
 * Outputs :
 *   - JSX.Element (bell icon button with animated unread-count badge (read === false); click toggles an animated dropdown containing NotificationPanel; closes on outside click)
 * File explanation : Header bell. Pure presentation: no API calls.
 */
