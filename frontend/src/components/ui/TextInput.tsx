/**
 * Inputs :
 *   - props: { label: string; value: string; onChange: (value: string) => void; type?: 'text' | 'email' | 'password' (default 'text'); multiline?: boolean; rows?: number; placeholder?: string; error?: string | null; maxLength?: number; autoFocus?: boolean; disabled?: boolean }
 * Outputs :
 *   - JSX.Element (labeled single-line input or textarea; focus ring in gold; red error text under it when error is set)
 * File explanation : The only text field in the app (also used as the multi-line editor). Content is plain text only.
 */

import { useId } from 'react';

export function TextInput({
  label,
  value,
  onChange,
  type = 'text',
  multiline = false,
  rows = 4,
  placeholder,
  error,
  maxLength,
  autoFocus = false,
  disabled = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: 'text' | 'email' | 'password';
  multiline?: boolean;
  rows?: number;
  placeholder?: string;
  error?: string | null;
  maxLength?: number;
  autoFocus?: boolean;
  disabled?: boolean;
}) {
  const inputId = useId();
  const baseClasses = [
    'w-full rounded-lg border bg-surface px-3.5 py-2.5 text-sm text-navy placeholder:text-navy-mute transition-colors',
    'focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold',
    error ? 'border-bad' : 'border-line',
    disabled ? 'opacity-60 cursor-not-allowed bg-canvas' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="w-full space-y-1.5">
      <label htmlFor={inputId} className="block text-xs font-medium text-navy-soft">
        {label}
      </label>
      {multiline ? (
        <textarea
          id={inputId}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={rows}
          placeholder={placeholder}
          maxLength={maxLength}
          autoFocus={autoFocus}
          disabled={disabled}
          className={baseClasses}
        />
      ) : (
        <input
          id={inputId}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          maxLength={maxLength}
          autoFocus={autoFocus}
          disabled={disabled}
          className={baseClasses}
        />
      )}
      {error ? (
        <p className="text-xs text-bad" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
