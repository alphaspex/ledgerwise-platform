/**
 * Inputs :
 *   - props: { initialEmail: string | null; initialRole: ContactRole | null; busy: boolean; onSubmit: (body: ContactRequest) => Promise<void> }
 *   - CONTACT_ROLE_LABEL (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (email TextInput, role chips founder / coo / finance / unknown, Save Button; Save disabled until the email looks valid (contains @ and a dot) and a role is chosen; calls onSubmit({ contact_email, contact_role }))
 * File explanation : Manual contact entry for one company.
 */
