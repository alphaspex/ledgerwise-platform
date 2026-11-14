/**
 * Inputs :
 *   - props: { title: string; subtitle?: string; children: ReactNode; footer?: ReactNode }
 * Outputs :
 *   - JSX.Element (full-screen slate-gradient background with a centered white card, 'Ledgerwise' wordmark, title, subtitle, children and footer; card animates in)
 * File explanation : Shared frame for Login, ForgotPassword, ResetPassword, AcceptInvite.
 */

import type { ReactNode } from 'react';
import { motion } from 'framer-motion';

export function AuthCardLayout({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-gradient flex items-center justify-center p-4 sm:p-6">
      <motion.div
        initial={{ opacity: 0, y: 16, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.28, ease: 'easeOut' }}
        className="w-full max-w-md rounded-2xl bg-surface border border-line shadow-lift p-6 sm:p-8 text-navy"
      >
        <div className="mb-6">
          <div className="text-sm font-bold tracking-wide text-gold-deep uppercase mb-2">
            Ledgerwise
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-navy">{title}</h1>
          {subtitle ? <p className="text-sm text-navy-mute mt-1">{subtitle}</p> : null}
        </div>

        <div className="space-y-4">{children}</div>

        {footer ? (
          <div className="mt-6 pt-5 border-t border-line text-sm text-navy-soft">{footer}</div>
        ) : null}
      </motion.div>
    </div>
  );
}
