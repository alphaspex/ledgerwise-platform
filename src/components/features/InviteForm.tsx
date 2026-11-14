/**
 * Inputs :
 *   - props: { busy: boolean; onInvite: (email: string) => Promise<void> }
 * Outputs :
 *   - JSX.Element (email TextInput + Invite Button; clears after onInvite resolves; disabled until the email looks valid)
 * File explanation : Admin form to invite a teammate.
 */

import { useState, type FormEvent } from 'react';
import { UserPlus } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { TextInput } from '../ui/TextInput';

export function InviteForm({
  busy,
  onInvite,
}: {
  busy: boolean;
  onInvite: (email: string) => Promise<void>;
}) {
  const [email, setEmail] = useState('');
  const trimmed = email.trim();
  const isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!isValid || busy) return;
    await onInvite(trimmed);
    setEmail('');
  };

  return (
    <Card>
      <form onSubmit={(e) => void handleSubmit(e)} className="flex flex-col sm:flex-row sm:items-end gap-3">
        <div className="flex-1 min-w-0">
          <TextInput
            label="Invite teammate by email"
            type="email"
            value={email}
            onChange={setEmail}
            placeholder="teammate@company.com"
            disabled={busy}
          />
        </div>
        <Button type="submit" variant="primary" icon={UserPlus} loading={busy} disabled={!isValid}>
          Invite
        </Button>
      </form>
    </Card>
  );
}
