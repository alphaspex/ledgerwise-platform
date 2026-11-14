/**
 * Inputs :
 *   - props: { draft: EmailDraft; index: number; busy: boolean; onApprove: (messageId: number) => Promise<void>; onEdit: (messageId: number, body: string) => Promise<void>; onReject: (messageId: number) => Promise<void> }
 *   - FactList component
 * Outputs :
 *   - JSX.Element (Card with domain, recipient email + role, the draft body as plain text, 'Edit' toggling an inline TextInput (multiline) with Save & approve / Cancel, Approve and Reject Buttons, and the FactList of draft.facts underneath)
 * File explanation : One first-email draft waiting for review. Holds only local state for the inline editor.
 */

import { useState } from 'react';
import { Check, Pencil, X } from 'lucide-react';
import type { EmailDraft } from '../../shared/types';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { TextInput } from '../ui/TextInput';
import { FactList } from './FactList';

export function EmailDraftCard({
  draft,
  index,
  busy,
  onApprove,
  onEdit,
  onReject,
}: {
  draft: EmailDraft;
  index: number;
  busy: boolean;
  onApprove: (messageId: number) => Promise<void>;
  onEdit: (messageId: number, body: string) => Promise<void>;
  onReject: (messageId: number) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [body, setBody] = useState(draft.body);

  return (
    <Card index={index} className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-base font-semibold text-navy">{draft.domain}</h3>
          <p className="text-xs text-navy-mute">
            {draft.contact_email} · {draft.contact_role}
          </p>
        </div>
      </div>

      {editing ? (
        <div className="space-y-3">
          <TextInput
            label="Email body"
            multiline
            rows={6}
            value={body}
            onChange={setBody}
            disabled={busy}
          />
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="primary"
              icon={Check}
              loading={busy}
              disabled={busy || body.trim().length === 0}
              onClick={() => void onEdit(draft.message_id, body.trim())}
            >
              Save &amp; approve
            </Button>
            <Button
              variant="secondary"
              disabled={busy}
              onClick={() => {
                setBody(draft.body);
                setEditing(false);
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <>
          <div className="rounded-lg border border-line bg-canvas/60 p-4 text-sm text-navy whitespace-pre-wrap break-words leading-relaxed">
            {draft.body}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="primary"
              icon={Check}
              loading={busy}
              disabled={busy}
              onClick={() => void onApprove(draft.message_id)}
            >
              Approve
            </Button>
            <Button
              variant="secondary"
              icon={Pencil}
              disabled={busy}
              onClick={() => {
                setBody(draft.body);
                setEditing(true);
              }}
            >
              Edit
            </Button>
            <Button
              variant="danger"
              icon={X}
              loading={busy}
              disabled={busy}
              onClick={() => void onReject(draft.message_id)}
            >
              Reject
            </Button>
          </div>
        </>
      )}

      <FactList facts={draft.facts} />
    </Card>
  );
}
