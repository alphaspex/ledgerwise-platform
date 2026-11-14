/**
 * Inputs :
 *   - props: { busy: boolean; onInvite: (email: string) => Promise<void> }
 * Outputs :
 *   - JSX.Element (email TextInput + Invite Button; clears after onInvite resolves; disabled until the email looks valid)
 * File explanation : Admin form to invite a teammate.
 */
