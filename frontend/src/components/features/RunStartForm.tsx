/**
 * Inputs :
 *   - props: { onStart: (selection: string) => Promise<void>; disabled: boolean; loading: boolean }
 *   - RESEARCH_TARGET: number (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (empty multi-line TextInput for the selection text, fixed line 'Target: 30 approved companies', Start Button; Start is disabled when disabled is true or the text is blank; calls onStart(trimmed text))
 * File explanation : Form to start a research run.
 */

import { useState, type FormEvent } from 'react';
import { Play } from 'lucide-react';
import { RESEARCH_TARGET } from '../../shared/constants';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { TextInput } from '../ui/TextInput';

export function RunStartForm({
  onStart,
  disabled,
  loading,
}: {
  onStart: (selection: string) => Promise<void>;
  disabled: boolean;
  loading: boolean;
}) {
  const [selection, setSelection] = useState('');
  const trimmed = selection.trim();
  const canSubmit = !disabled && !loading && trimmed.length > 0;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    await onStart(trimmed);
    setSelection('');
  };

  return (
    <Card>
      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
        <TextInput
          label="Company selection criteria"
          multiline
          rows={4}
          value={selection}
          onChange={setSelection}
          placeholder="Describe target companies, geographies, verticals, or signals to qualify..."
          disabled={disabled || loading}
        />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs font-medium text-navy-soft tabular-nums">
            Target: {RESEARCH_TARGET} approved companies
          </p>
          <Button
            type="submit"
            variant="primary"
            icon={Play}
            loading={loading}
            disabled={disabled || trimmed.length === 0}
          >
            Start
          </Button>
        </div>
      </form>
    </Card>
  );
}
