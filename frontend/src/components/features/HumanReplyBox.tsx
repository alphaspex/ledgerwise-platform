/**
 * Inputs :
 *   - props: { threadState: ThreadState; busy: boolean; onTakeover: () => Promise<void>; onSend: (body: string) => Promise<void> }
 * Outputs :
 *   - JSX.Element (threadState 'human_taken_over': multi-line TextInput + Send Button calling onSend(trimmed body), cleared after success; 'closed': disabled note 'This thread is closed'; any other state: a bar 'The agent is handling this thread' with a Take over Button calling onTakeover)
 * File explanation : Bottom bar of the chat screen: takeover and human reply.
 */

import { useState, type FormEvent } from 'react';
import { Send, UserCheck } from 'lucide-react';
import type { ThreadState } from '../../shared/types';
import { Button } from '../ui/Button';
import { TextInput } from '../ui/TextInput';

export function HumanReplyBox({
  threadState,
  busy,
  onTakeover,
  onSend,
}: {
  threadState: ThreadState;
  busy: boolean;
  onTakeover: () => Promise<void>;
  onSend: (body: string) => Promise<void>;
}) {
  const [body, setBody] = useState('');
  const trimmed = body.trim();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!trimmed || busy) return;
    await onSend(trimmed);
    setBody('');
  };

  if (threadState === 'closed') {
    return (
      <div className="rounded-xl border border-line bg-canvas px-4 py-3 text-sm text-navy-mute text-center">
        This thread is closed
      </div>
    );
  }

  if (threadState === 'human_taken_over') {
    return (
      <form
        onSubmit={(e) => void handleSubmit(e)}
        className="rounded-xl border border-line bg-surface p-4 shadow-card space-y-3"
      >
        <TextInput
          label="Reply to prospect"
          multiline
          rows={3}
          value={body}
          onChange={setBody}
          placeholder="Write your reply..."
          disabled={busy}
        />
        <div className="flex justify-end">
          <Button type="submit" variant="primary" icon={Send} loading={busy} disabled={!trimmed || busy}>
            Send
          </Button>
        </div>
      </form>
    );
  }

  return (
    <div className="rounded-xl border border-line bg-surface p-4 shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <span className="text-sm text-navy-soft">The agent is handling this thread</span>
      <Button
        variant="secondary"
        icon={UserCheck}
        loading={busy}
        disabled={busy}
        onClick={() => void onTakeover()}
      >
        Take over
      </Button>
    </div>
  );
}
