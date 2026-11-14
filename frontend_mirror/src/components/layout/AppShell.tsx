/**
 * Inputs :
 *   - props: { children: ReactNode }
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(listNotifications) -> Notification[]; markNotificationsRead(body: MarkReadRequest): Promise<OkResponse> (from api/notificationsApi.ts)
 *   - logout(): Promise<OkResponse> (from api/authApi.ts)
 * Outputs :
 *   - JSX.Element (desktop: Sidebar left + top bar + scrollable content; mobile: top bar + content + BottomBar)
 *   - top bar contains NotificationBell, the user's email and a Log out button (calls logout() then context.signOut())
 * File explanation : Layout of every signed-in screen. Owns the notifications polling (5s) and passes data to NotificationBell. Bell item click navigates: unsure_answer and do_not_contact -> goTo('chat', company_id); contact_missing -> goTo('contacts_needed'); booking_conflict -> goTo('bookings').
 */
