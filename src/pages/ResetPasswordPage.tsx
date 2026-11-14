/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - resetPassword(body: ResetPasswordRequest): Promise<OkResponse> (api/authApi.ts)
 *   - PASSWORD_MIN_LEN: number, CODE_LENGTH: number (shared/constants.ts)
 *   - useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (AuthCardLayout with email, 6-digit code, new password and confirm TextInputs; client check: password length >= PASSWORD_MIN_LEN and both passwords equal; on success toast 'Password updated' and goTo('login'); shows 400/410 detail inline)
 * File explanation : Step 2 of resetting a forgotten password.
 */

import { useState, type FormEvent } from 'react';
import { KeyRound } from 'lucide-react';
import { resetPassword } from '../api/authApi';
import { AuthCardLayout } from '../components/features/AuthCardLayout';
import { Button } from '../components/ui/Button';
import { TextInput } from '../components/ui/TextInput';
import { useAsync } from '../hooks/useAsync';
import { useToast } from '../hooks/useToast';
import { useApp } from '../shared/AppContext';
import { CODE_LENGTH, PASSWORD_MIN_LEN } from '../shared/constants';

export function ResetPasswordPage() {
  const { goTo } = useApp();
  const toast = useToast();
  const { run, loading, error } = useAsync(resetPassword);

  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    if (code.trim().length !== CODE_LENGTH) {
      setValidationError(`Code must be ${CODE_LENGTH} characters.`);
      return;
    }
    if (newPassword.length < PASSWORD_MIN_LEN) {
      setValidationError(`Password must be at least ${PASSWORD_MIN_LEN} characters.`);
      return;
    }
    if (newPassword !== confirmPassword) {
      setValidationError('Passwords do not match.');
      return;
    }

    const res = await run({
      email: email.trim(),
      code: code.trim(),
      new_password: newPassword,
      new_password_confirm: confirmPassword,
    });
    if (res?.ok) {
      toast.success('Password updated');
      goTo('login');
    }
  };

  return (
    <AuthCardLayout
      title="Reset password"
      subtitle="Enter the 6-digit code sent to your email"
      footer={
        <div className="text-xs">
          <button
            type="button"
            onClick={() => goTo('login')}
            className="font-medium text-slateblue-600 hover:underline"
          >
            Back to log in
          </button>
        </div>
      }
    >
      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
        <TextInput
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          placeholder="you@company.com"
          autoFocus
          disabled={loading}
        />
        <TextInput
          label="6-digit code"
          type="text"
          value={code}
          onChange={setCode}
          placeholder="123456"
          maxLength={CODE_LENGTH}
          disabled={loading}
        />
        <TextInput
          label="New password"
          type="password"
          value={newPassword}
          onChange={setNewPassword}
          placeholder={`At least ${PASSWORD_MIN_LEN} characters`}
          disabled={loading}
        />
        <TextInput
          label="Confirm password"
          type="password"
          value={confirmPassword}
          onChange={setConfirmPassword}
          placeholder="Repeat your new password"
          disabled={loading}
        />

        {validationError ? (
          <p role="alert" className="text-xs text-bad">
            {validationError}
          </p>
        ) : null}
        {error ? (
          <p role="alert" className="text-xs text-bad">
            {error.detail}
          </p>
        ) : null}

        <Button
          type="submit"
          variant="primary"
          icon={KeyRound}
          loading={loading}
          disabled={!email.trim() || !code.trim() || !newPassword || !confirmPassword}
          fullWidth
        >
          Reset password
        </Button>
      </form>
    </AuthCardLayout>
  );
}
