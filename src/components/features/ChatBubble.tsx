/**
 * Inputs :
 *   - props: { message: ThreadMessage }
 *   - ToolCallChip component
 * Outputs :
 *   - JSX.Element (bubble aligned left for prospect, right for agent/human; sender label (Prospect / Agent / Human), body rendered as PLAIN TEXT only (never dangerouslySetInnerHTML), timestamp, and one ToolCallChip per item of tool_calls under the bubble; entrance animation)
 * File explanation : One message of a conversation.
 */

import { motion } from 'framer-motion';
import type { MessageSender, ThreadMessage } from '../../shared/types';
import { ToolCallChip } from './ToolCallChip';

const SENDER_LABEL: Record<MessageSender, string> = {
  prospect: 'Prospect',
  agent: 'Agent',
  human: 'Human',
};

export function ChatBubble({ message }: { message: ThreadMessage }) {
  const isProspect = message.sender_type === 'prospect';
  const timeText = new Date(message.created_at).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`flex flex-col ${isProspect ? 'items-start' : 'items-end'}`}
    >
      <div
        className={[
          'max-w-xl rounded-2xl px-4 py-3 shadow-card border',
          isProspect
            ? 'bg-surface border-line text-navy rounded-bl-sm'
            : message.sender_type === 'human'
              ? 'bg-gold/15 border-gold/40 text-navy rounded-br-sm'
              : 'bg-slate-gradient border-slateblue-600 text-white rounded-br-sm',
        ].join(' ')}
      >
        <div
          className={`text-[11px] font-semibold mb-1 ${
            isProspect || message.sender_type === 'human' ? 'text-navy-mute' : 'text-white/80'
          }`}
        >
          {SENDER_LABEL[message.sender_type]} · <span className="tabular-nums">{timeText}</span>
        </div>
        <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">{message.body}</p>
      </div>

      {message.tool_calls && message.tool_calls.length > 0 ? (
        <div className="mt-1.5 flex flex-wrap gap-1.5">
          {message.tool_calls.map((call, idx) => (
            <ToolCallChip key={`${message.id}-tc-${idx}`} call={call} />
          ))}
        </div>
      ) : null}
    </motion.div>
  );
}
