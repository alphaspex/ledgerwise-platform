/**
 * Inputs :
 *   - props: { children: ReactNode; onClick?: () => void; interactive?: boolean (hover lift); index?: number (stagger position, default 0); className?: string }
 * Outputs :
 *   - JSX.Element (surface card with shadow-card; fades and rises on mount with delay index * STAGGER_SECONDS)
 * File explanation : Base container for every card in the app (companies, drafts, threads, summary blocks).
 */

import type { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { STAGGER_SECONDS } from '../../shared/constants';

export function Card({
  children,
  onClick,
  interactive = false,
  index = 0,
  className = '',
}: {
  children: ReactNode;
  onClick?: () => void;
  interactive?: boolean;
  index?: number;
  className?: string;
}) {
  const isClickable = Boolean(onClick);
  const hoverMotion = interactive || isClickable ? { y: -2 } : undefined;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{
        opacity: 1,
        y: 0,
        transition: {
          duration: 0.22,
          delay: Math.min(index, 12) * STAGGER_SECONDS,
          ease: 'easeOut',
        },
      }}
      exit={{
        opacity: 0,
        y: -8,
        scale: 0.98,
        transition: { duration: 0.16, ease: 'easeIn' },
      }}
      whileHover={
        hoverMotion
          ? { ...hoverMotion, transition: { duration: 0.15, ease: 'easeOut' } }
          : undefined
      }
      transition={{ layout: { duration: 0.22, ease: 'easeOut' } }}
      onClick={onClick}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={
        isClickable
          ? (e) => {
              if ((e.key === 'Enter' || e.key === ' ') && onClick) {
                e.preventDefault();
                onClick();
              }
            }
          : undefined
      }
      className={[
        'bg-surface rounded-xl border border-line shadow-card p-5 text-navy',
        interactive || isClickable
          ? 'cursor-pointer transition-shadow hover:shadow-lift focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold'
          : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {children}
    </motion.div>
  );
}
