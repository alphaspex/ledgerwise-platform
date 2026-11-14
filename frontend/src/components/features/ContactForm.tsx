/**
 * Inputs :
 *   - props: { initialEmail: string | null; initialRole: ContactRole | null; busy: boolean; onSubmit: (body: ContactRequest) => Promise<void> }
 *   - CONTACT_ROLE_LABEL (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (email TextInput, role chips founder / coo / finance / unknown, Save Button; Save disabled until the email looks valid (contains @ and a dot) and a role is chosen; calls onSubmit({ contact_email, contact_role }))
 * File explanation : Manual contact entry for one company.
 */

import { useState, type FormEvent } from 'react';
import { CONTACT_ROLE_LABEL } from '../../shared/constants';
import type { ContactRequest, ContactRole } from '../../shared/types';
import { Button } from '../ui/Button';
import { TextInput } from '../ui/TextInput';

const ROLES: ContactRole[] = ['founder', 'coo', 'finance', 'unknown'];

export function ContactForm({
  initialEmail,
  initialRole,
  busy,
  onSubmit,
}: {
  initialEmail: string | null;
  initialRole: ContactRole | null;
  busy: boolean;
  onSubmit: (body: ContactRequest) => Promise<void>;
}) {
  const [email, setEmail] = useState(initialEmail ?? '');
  const [role, setRole] = useState<ContactRole | null>(initialRole);

  const trimmed = email.trim();
  const isValidEmail = trimmed.includes('@') && trimmed.includes('.');
  const canSubmit = isValidEmail && role !== null && !busy;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!canSubmit || role === null) return;
    await onSubmit({ contact_email: trimmed, contact_role: role });
  };

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="space-y-3">
      <TextInput
        label="Contact email"
        type="email"
        value={email}
        onChange={setEmail}
        placeholder="name@company.com"
        disabled={busy}
      />

      <div className="flex flex-wrap items-center gap-2">
        {ROLES.map((r) => (
          <button
            key={r}
            type="button"
            disabled={busy}
            onClick={() => setRole(r)}
            className={`rounded-full px-3 py-1 text-xs font-medium border transition-colors whitespace-nowrap ${
              role === r
                ? 'bg-gold/15 text-gold-deep border-gold'
                : 'bg-canvas text-navy-soft border-line hover:text-navy'
            }`}
          >
            {CONTACT_ROLE_LABEL[r]}
          </button>
        ))}
      </div>

      <Button type="submit" variant="primary" loading={busy} disabled={!canSubmit}>
        Save
      </Button>
    </form>
  );
}
