/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - context.selectedThreadCompanyId: number | null
 *   - usePolling(() => getThread(id)) -> ThreadDetail; takeoverThread(companyId: number): Promise<ThreadSummary>; sendHumanReply(companyId: number, body: HumanReplyRequest): Promise<ThreadMessage> (api/outreachApi.ts)
 *   - useAuthGuard(), useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (conversation history and controls plus conversation-specific AI usage totals; 404 returns to 'conversations')
 * File explanation : Reads, takes over, and replies to one conversation; shows token and cost usage attributed to its automated replies.
 */

import { useCallback, useEffect, useRef } from 'react';
import { getThread, sendHumanReply, takeoverThread } from '../api/outreachApi';
import { ChatBubble } from '../components/features/ChatBubble';
import { HumanReplyBox } from '../components/features/HumanReplyBox';
import { PageHeader } from '../components/layout/PageHeader';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { StatusPill } from '../components/ui/StatusPill';
import { useAsync } from '../hooks/useAsync';
import { useAuthGuard } from '../hooks/useAuthGuard';
import { usePolling } from '../hooks/usePolling';
import { useToast } from '../hooks/useToast';
import { useApp } from '../shared/AppContext';
import { THREAD_STATE_LABEL, THREAD_STATE_TONE } from '../shared/constants';
import type { ThreadDetail } from '../shared/types';

export function ChatPage() {
  useAuthGuard();
  const { selectedThreadCompanyId, goTo } = useApp();
  const toast = useToast();
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (selectedThreadCompanyId === null) {
      goTo('conversations');
    }
  }, [selectedThreadCompanyId, goTo]);

  const fetchThread = useCallback(() => {
    if (selectedThreadCompanyId === null) {
      return Promise.reject(new Error('No thread selected'));
    }
    return getThread(selectedThreadCompanyId);
  }, [selectedThreadCompanyId]);

  const { data: thread, loading, error, refresh } = usePolling<ThreadDetail>(fetchThread, {
    enabled: selectedThreadCompanyId !== null,
  });

  useEffect(() => {
    if (error?.status === 404) goTo('conversations');
  }, [error, goTo]);

  const takeoverAction = useAsync(takeoverThread);
  const sendAction = useAsync(sendHumanReply);

  useEffect(() => {
    if (takeoverAction.error) toast.error(takeoverAction.error.detail);
  }, [takeoverAction.error, toast]);

  useEffect(() => {
    if (sendAction.error) toast.error(sendAction.error.detail);
  }, [sendAction.error, toast]);

  const messageCount = thread?.messages.length ?? 0;
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messageCount]);

  const handleTakeover = async () => {
    if (selectedThreadCompanyId === null) return;
    const res = await takeoverAction.run(selectedThreadCompanyId);
    if (res) {
      toast.success('Thread taken over');
      await refresh();
    }
  };

  const handleSend = async (body: string) => {
    if (selectedThreadCompanyId === null) return;
    const res = await sendAction.run(selectedThreadCompanyId, { body });
    if (res) {
      toast.success('Reply sent');
      await refresh();
    }
  };

  if (selectedThreadCompanyId === null) {
    return null;
  }

  if (loading && !thread) {
    return (
      <div className="space-y-6">
        <PageHeader title="Conversation" onBack={() => goTo('conversations')} />
        <Skeleton variant="block" count={4} />
      </div>
    );
  }

  if (error && !thread) {
    return (
      <div className="space-y-6">
        <PageHeader title="Conversation" onBack={() => goTo('conversations')} />
        <ErrorState message={error.detail} onRetry={() => void refresh()} />
      </div>
    );
  }

  if (!thread) {
    return null;
  }

  const usageCostLabel = thread.usage.cost_complete && thread.usage.cost_usd !== null
    ? `${thread.usage.cost_usd.toFixed(6)}`
    : 'Unavailable (pricing not set for all calls)';

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <PageHeader
        title={thread.summary.domain}
        subtitle={thread.summary.contact_email ?? undefined}
        onBack={() => goTo('conversations')}
        actions={
          <StatusPill
            label={THREAD_STATE_LABEL[thread.summary.thread_state]}
            tone={THREAD_STATE_TONE[thread.summary.thread_state]}
          />
        }
      />

      <div className="flex flex-wrap gap-x-4 gap-y-1 border-b border-line py-2 text-xs text-navy-mute">
        <span>AI calls: {thread.usage.calls.toLocaleString()}</span>
        <span>Input: {thread.usage.input_tokens.toLocaleString()}</span>
        <span>Output: {thread.usage.output_tokens.toLocaleString()}</span>
        <span>Reasoning: {thread.usage.reasoning_tokens.toLocaleString()}</span>
        <span>Total: {thread.usage.total_tokens.toLocaleString()} tokens</span>
        <span>Cost: {usageCostLabel}</span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 pr-1 py-2">
        {thread.messages.map((message) => (
          <ChatBubble key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="pt-3 border-t border-line">
        <HumanReplyBox
          threadState={thread.summary.thread_state}
          busy={takeoverAction.loading || sendAction.loading}
          onTakeover={handleTakeover}
          onSend={handleSend}
        />
      </div>
    </div>
  );
}
