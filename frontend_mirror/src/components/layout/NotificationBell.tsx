/**
 * Inputs :
 *   - props: { notifications: Notification[]; error: ApiError | null; onMarkAllRead: () => void; onSelect: (notification: Notification) => void }
 * Outputs :
 *   - JSX.Element (bell button with unread badge and dropdown containing NotificationPanel; closes on outside click)
 * File explanation : Header bell. Pure presentation: no API calls. Forwards notification polling errors to the dropdown.
 */
