/**
 * Inputs :
 *   - props: { thread: ThreadSummary; index: number; onOpen: (companyId: number) => void }
 *   - THREAD_STATE_LABEL, THREAD_STATE_TONE (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (interactive Card with domain, thread-state StatusPill, last message preview (plain text, one line), who sent it and the time; click calls onOpen(thread.company_id))
 * File explanation : One conversation in the conversations list.
 */

import { THREAD_STATE_LABEL, THREAD_STATE_TONE } from '../../shared/constants';
import type { MessageSender, ThreadSummary } from '../../shared/types';
import { Card } from '../ui/Card';
import { StatusPill } from '../ui/StatusPill';

const SENDER_LABEL: Record<MessageSender, string> = {
  agent: 'Agent',
  prospect: 'Prospect',
  human: 'Human',
};

export function ThreadCard({
  thread,
  index,
  onOpen,
}: {
  thread: ThreadSummary;
  index: number;
  onOpen: (companyId: number) => void;
}) {
  const timeText = new Date(thread.last_message_at).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <Card
      interactive
      index={index}
      onClick={() => onOpen(thread.company_id)}
      className="space-y-2.5"
    >
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-base font-semibold text-navy truncate">{thread.domain}</h3>
        <StatusPill
          label={THREAD_STATE_LABEL[thread.thread_state]}
          tone={THREAD_STATE_TONE[thread.thread_state]}
        />
      </div>

      <p className="text-sm text-navy-soft truncate">{thread.last_message_preview}</p>

      <div className="flex items-center justify-between text-xs text-navy-mute">
        <span>
          {SENDER_LABEL[thread.last_message_sender]}
          {thread.contact_email ? ` · ${thread.contact_email}` : ''}
        </span>
        <span className="tabular-nums shrink-0">{timeText}</span>
      </div>
    </Card>
  );
}
