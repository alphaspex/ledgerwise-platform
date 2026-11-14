/**
 * Inputs :
 *   - props: { draft: EmailDraft; index: number; busy: boolean; onApprove: (messageId: number) => Promise<void>; onEdit: (messageId: number, body: string) => Promise<void>; onReject: (messageId: number) => Promise<void> }
 *   - FactList component
 * Outputs :
 *   - JSX.Element (Card with domain, recipient email + role, the draft body as plain text, 'Edit' toggling an inline TextInput (multiline) with Save & approve / Cancel, Approve and Reject Buttons, and the FactList of draft.facts underneath)
 * File explanation : One first-email draft waiting for review. Holds only local state for the inline editor.
 */
