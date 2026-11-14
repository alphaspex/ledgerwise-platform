/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - requestPasswordChange(body: ChangePasswordRequest): Promise<OkResponse>, confirmPasswordChange(body: ChangePasswordConfirmRequest): Promise<OkResponse> (api/authApi.ts)
 *   - useAuthGuard(), useAsync, useToast hooks
 *   - PASSWORD_MIN_LEN, CODE_LENGTH (shared/constants.ts)
 * Outputs :
 *   - JSX.Element (PageHeader + Card with two steps: step 1 old password -> requestPasswordChange; step 2 code + new password + confirm -> confirmPasswordChange; step switch animated; on 410 returns to step 1 with 'Code expired, request a new one'; on success toast and goTo('dashboard'))
 * File explanation : Logged-in password change with an emailed code.
 */

import { useEffect, useState, type FormEvent } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { KeyRound, ShieldCheck } from 'lucide-react';
import { confirmPasswordChange, requestPasswordChange } from '../api/authApi';
import { PageHeader } from '../components/layout/PageHeader';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { TextInput } from '../components/ui/TextInput';
import { useAsync } from '../hooks/useAsync';
import { useAuthGuard } from '../hooks/useAuthGuard';
import { useToast } from '../hooks/useToast';
import { useApp } from '../shared/AppContext';
import { CODE_LENGTH, PASSWORD_MIN_LEN } from '../shared/constants';

export function ChangePasswordPage() {
  useAuthGuard();
  const { goTo } = useApp();
  const toast = useToast();

  const step1Action = useAsync(requestPasswordChange);
  const step2Action = useAsync(confirmPasswordChange);

  const [step, setStep] = useState<1 | 2>(1);
  const [oldPassword, setOldPassword] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [inlineError, setInlineError] = useState<string | null>(null);

  useEffect(() => {
    if (step1Action.error) {
      setInlineError(step1Action.error.detail);
    }
  }, [step1Action.error]);

  useEffect(() => {
    if (!step2Action.error) return;
    if (step2Action.error.status === 410) {
      setStep(1);
      setCode('');
      setInlineError('Code expired, request a new one');
    } else {
      setInlineError(step2Action.error.detail);
    }
  }, [step2Action.error]);

  const handleStep1 = async (e: FormEvent) => {
    e.preventDefault();
    setInlineError(null);
    const res = await step1Action.run({ old_password: oldPassword });
    if (res?.ok) {
      setStep(2);
      toast.info('Verification code sent to your email');
    }
  };

  const handleStep2 = async (e: FormEvent) => {
    e.preventDefault();
    setInlineError(null);
    if (code.trim().length !== CODE_LENGTH) {
      setInlineError(`Code must be ${CODE_LENGTH} characters.`);
      return;
    }
    if (newPassword.length < PASSWORD_MIN_LEN) {
      setInlineError(`Password must be at least ${PASSWORD_MIN_LEN} characters.`);
      return;
    }
    if (newPassword !== confirmPassword) {
      setInlineError('Passwords do not match.');
      return;
    }

    const res = await step2Action.run({
      code: code.trim(),
      new_password: newPassword,
      new_password_confirm: confirmPassword,
    });
    if (res?.ok) {
      toast.success('Password updated');
      goTo('dashboard');
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Change password"
        subtitle="Verify your current password, then enter the 6-digit code sent to your email"
      />

      <Card className="max-w-lg">
        <AnimatePresence mode="wait">
          {step === 1 ? (
            <motion.form
              key="step-1"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              onSubmit={(e) => void handleStep1(e)}
              className="space-y-4"
            >
              <TextInput
                label="Current password"
                type="password"
                value={oldPassword}
                onChange={setOldPassword}
                placeholder="Enter your current password"
                autoFocus
                disabled={step1Action.loading}
              />

              {inlineError ? (
                <p role="alert" className="text-xs text-bad">
                  {inlineError}
                </p>
              ) : null}

              <Button
                type="submit"
                variant="primary"
                icon={ShieldCheck}
                loading={step1Action.loading}
                disabled={!oldPassword}
              >
                Send verification code
              </Button>
            </motion.form>
          ) : (
            <motion.form
              key="step-2"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              onSubmit={(e) => void handleStep2(e)}
              className="space-y-4"
            >
              <TextInput
                label="6-digit verification code"
                type="text"
                value={code}
                onChange={setCode}
                placeholder="123456"
                maxLength={CODE_LENGTH}
                autoFocus
                disabled={step2Action.loading}
              />
              <TextInput
                label="New password"
                type="password"
                value={newPassword}
                onChange={setNewPassword}
                placeholder={`At least ${PASSWORD_MIN_LEN} characters`}
                disabled={step2Action.loading}
              />
              <TextInput
                label="Confirm new password"
                type="password"
                value={confirmPassword}
                onChange={setConfirmPassword}
                placeholder="Repeat your new password"
                disabled={step2Action.loading}
              />

              {inlineError ? (
                <p role="alert" className="text-xs text-bad">
                  {inlineError}
                </p>
              ) : null}

              <div className="flex flex-wrap items-center gap-3">
                <Button
                  type="submit"
                  variant="primary"
                  icon={KeyRound}
                  loading={step2Action.loading}
                  disabled={!code.trim() || !newPassword || !confirmPassword}
                >
                  Update password
                </Button>
                <Button
                  variant="secondary"
                  disabled={step2Action.loading}
                  onClick={() => {
                    setStep(1);
                    setInlineError(null);
                  }}
                >
                  Back
                </Button>
              </div>
            </motion.form>
          )}
        </AnimatePresence>
      </Card>
    </div>
  );
}
