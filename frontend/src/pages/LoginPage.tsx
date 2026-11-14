/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - login(body: LoginRequest): Promise<LoginResponse> (api/authApi.ts)
 *   - useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (AuthCardLayout with email + password TextInputs and Log in Button; links 'Forgot password' -> goTo('forgot_password') and 'Have an invite code' -> goTo('accept_invite'); shows the SESSION_EXPIRED_TEXT notice when context.sessionExpired is true; on success calls signIn(token, user) then goTo('dashboard'); on failure shows the error detail under the form)
 * File explanation : Login screen.
 */

import { useState, type FormEvent } from 'react';
import { LogIn } from 'lucide-react';
import { login } from '../api/authApi';
import { AuthCardLayout } from '../components/features/AuthCardLayout';
import { Button } from '../components/ui/Button';
import { TextInput } from '../components/ui/TextInput';
import { useAsync } from '../hooks/useAsync';
import { useToast } from '../hooks/useToast';
import { useApp } from '../shared/AppContext';
import { SESSION_EXPIRED_TEXT } from '../shared/constants';

export function LoginPage() {
  const { sessionExpired, signIn, goTo } = useApp();
  const toast = useToast();
  const { run, loading, error } = useAsync(login);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const res = await run({ email: email.trim(), password });
    if (res) {
      toast.success('Signed in');
      signIn(res.token, res.user);
      goTo('dashboard');
    }
  };

  return (
    <AuthCardLayout
      title="Log in"
      subtitle="Sign in to Ledgerwise"
      footer={
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
          <button
            type="button"
            onClick={() => goTo('forgot_password')}
            className="font-medium text-slateblue-600 hover:underline"
          >
            Forgot password
          </button>
          <button
            type="button"
            onClick={() => goTo('accept_invite')}
            className="font-medium text-slateblue-600 hover:underline"
          >
            Have an invite code
          </button>
        </div>
      }
    >
      {sessionExpired ? (
        <div
          role="status"
          className="rounded-lg border border-warn/40 bg-warn/10 px-3.5 py-2.5 text-xs font-medium text-navy"
        >
          {SESSION_EXPIRED_TEXT}
        </div>
      ) : null}

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
          label="Password"
          type="password"
          value={password}
          onChange={setPassword}
          placeholder="Enter your password"
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
          icon={LogIn}
          loading={loading}
          disabled={!email.trim() || !password}
          fullWidth
        >
          Log in
        </Button>
      </form>
    </AuthCardLayout>
  );
}
