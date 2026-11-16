/**
 * Inputs :
 *   - props: { children: ReactNode }
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(listNotifications) -> { data: Notification[] | null; error: ApiError | null }
 *   - markNotificationsRead(body: MarkReadRequest): Promise<OkResponse>; logout(): Promise<OkResponse>
 * Outputs :
 *   - JSX.Element (desktop Sidebar + top bar + content; mobile top bar + content + BottomBar)
 *   - top bar contains NotificationBell, user email and Log out
 * File explanation : Layout of every signed-in screen. Owns 5s notification polling and passes data plus polling errors to NotificationBell, so failures are not shown as an empty list. Notification clicks navigate to the related screen.
 */
