/**
 * Inputs :
 *   - props: { screenKey: ScreenName; children: ReactNode }
 *   - PAGE_TRANSITION_SECONDS: number (from shared/constants.ts)
 * Outputs :
 *   - JSX.Element (AnimatePresence wrapper: old screen fades out, new screen fades in and slides up 12px, keyed by screenKey)
 * File explanation : Animates screen changes.
 */

import type { ReactNode } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { PAGE_TRANSITION_SECONDS } from '../../shared/constants';
import type { ScreenName } from '../../shared/types';

export function PageTransition({
  screenKey,
  children,
}: {
  screenKey: ScreenName;
  children: ReactNode;
}) {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={screenKey}
        initial={{ opacity: 0, y: 12 }}
        animate={{
          opacity: 1,
          y: 0,
          transition: { duration: PAGE_TRANSITION_SECONDS, ease: 'easeOut' },
        }}
        exit={{
          opacity: 0,
          y: -6,
          transition: { duration: Math.max(0.12, PAGE_TRANSITION_SECONDS * 0.6), ease: 'easeIn' },
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
