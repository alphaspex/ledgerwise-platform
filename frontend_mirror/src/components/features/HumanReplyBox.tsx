/**
 * Inputs :
 *   - props: { threadState: ThreadState; busy: boolean; onTakeover: () => Promise<void>; onSend: (body: string) => Promise<void> }
 * Outputs :
 *   - JSX.Element (threadState 'human_taken_over': multi-line TextInput + Send Button calling onSend(trimmed body), cleared after success; 'closed': disabled note 'This thread is closed'; any other state: a bar 'The agent is handling this thread' with a Take over Button calling onTakeover)
 * File explanation : Bottom bar of the chat screen: takeover and human reply.
 */
