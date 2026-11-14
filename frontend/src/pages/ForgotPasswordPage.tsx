/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - forgotPassword(body: ForgotPasswordRequest): Promise<OkResponse> (api/authApi.ts)
 *   - useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (AuthCardLayout with an email TextInput and Send code Button; on success shows toast 'If that email exists, a code was sent' and goTo('reset_password'); link back to login)
 * File explanation : Step 1 of resetting a forgotten password.
 */

import { useEffect, useState, type FormEvent } from 'react';
import { Mail } from 'lucide-react';
import { forgotPassword } from '../api/authApi';
import { AuthCardLayout } from '../components/features/AuthCardLayout';
import { Button } from '../components/ui/Button';
import { TextInput } from '../components/ui/TextInput';
import { useAsync } from '../hooks/useAsync';
import { useToast } from '../hooks/useToast';
import { useApp } from '../shared/AppContext';

export function ForgotPasswordPage() {
  const { goTo } = useApp();
  const toast = useToast();
  const { run, loading, error } = useAsync(forgotPassword);

  const [email, setEmail] = useState('');

  useEffect(() => {
    if (error) {
      toast.error(error.detail);
    }
  }, [error, toast]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const res = await run({ email: email.trim() });
    if (res?.ok) {
      toast.success('If that email exists, a code was sent');
      goTo('reset_password');
    }
  };

  return (
    <AuthCardLayout
      title="Forgot password"
      subtitle="Enter your email to receive a reset code"
      footer={
        <div className="flex items-center justify-between text-xs">
          <button
            type="button"
            onClick={() => goTo('login')}
            className="font-medium text-slateblue-600 hover:underline"
          >
            Back to log in
          </button>
          <button
            type="button"
            onClick={() => goTo('reset_password')}
            className="font-medium text-slateblue-600 hover:underline"
          >
            Already have a code
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

        {error ? (
          <p role="alert" className="text-xs text-bad">
            {error.detail}
          </p>
        ) : null}

        <Button
          type="submit"
          variant="primary"
          icon={Mail}
          loading={loading}
          disabled={!email.trim()}
          fullWidth
        >
          Send code
        </Button>
      </form>
    </AuthCardLayout>
  );
}
