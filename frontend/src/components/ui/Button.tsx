/**
 * Inputs :
 *   - props: { children: ReactNode; onClick?: () => void; variant?: 'primary' | 'secondary' | 'danger' | 'ghost' (default 'primary'); type?: 'button' | 'submit' (default 'button'); loading?: boolean; disabled?: boolean; icon?: LucideIcon; fullWidth?: boolean }
 * Outputs :
 *   - JSX.Element (button; primary = gold gradient, secondary = slate outline; tap scale 0.97 and hover lift via Framer Motion; spinner when loading; not clickable when loading or disabled)
 * File explanation : The only button in the app.
 */

import type { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { Loader2, type LucideIcon } from 'lucide-react';

export function Button({
  children,
  onClick,
  variant = 'primary',
  type = 'button',
  loading = false,
  disabled = false,
  icon: Icon,
  fullWidth = false,
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  type?: 'button' | 'submit';
  loading?: boolean;
  disabled?: boolean;
  icon?: LucideIcon;
  fullWidth?: boolean;
}) {
  const isDisabled = disabled || loading;

  const variantClasses: Record<'primary' | 'secondary' | 'danger' | 'ghost', string> = {
    primary: 'bg-gold-gradient text-white shadow-card hover:shadow-lift',
    secondary: 'bg-surface text-navy border border-slateblue-400 hover:bg-canvas',
    danger: 'bg-bad text-white shadow-card hover:opacity-95',
    ghost: 'bg-transparent text-navy-soft hover:bg-canvas hover:text-navy',
  };

  return (
    <motion.button
      type={type}
      disabled={isDisabled}
      onClick={() => {
        if (!isDisabled && onClick) {
          onClick();
        }
      }}
      whileTap={isDisabled ? undefined : { scale: 0.97 }}
      whileHover={isDisabled ? undefined : { y: -1 }}
      transition={{ duration: 0.15 }}
      className={[
        'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium whitespace-nowrap shrink-0 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold',
        variantClasses[variant],
        fullWidth ? 'w-full' : '',
        isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      ) : Icon ? (
        <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
      ) : null}
      <span>{children}</span>
    </motion.button>
  );
}
