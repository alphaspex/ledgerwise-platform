/**
 * Inputs :
 *   - props: { call: ToolCall }
 * Outputs :
 *   - JSX.Element (small chip with an icon and a friendly label: check_availability -> 'Checked availability', book_slot -> 'Booked a slot', call_human -> 'Called a human')
 * File explanation : Shows what the agent did behind a message.
 */

import { CalendarCheck, CalendarSearch, UserCheck } from 'lucide-react';
import type { ToolCall, ToolName } from '../../shared/types';

const TOOL_META: Record<ToolName, { label: string; Icon: typeof CalendarSearch }> = {
  check_availability: { label: 'Checked availability', Icon: CalendarSearch },
  book_slot: { label: 'Booked a slot', Icon: CalendarCheck },
  call_human: { label: 'Called a human', Icon: UserCheck },
};

export function ToolCallChip({ call }: { call: ToolCall }) {
  const meta = TOOL_META[call.name];
  const Icon = meta.Icon;

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-0.5 text-[11px] font-medium text-navy-soft shadow-card">
      <Icon className="h-3 w-3 text-slateblue-500" aria-hidden="true" />
      <span>{meta.label}</span>
    </span>
  );
}
