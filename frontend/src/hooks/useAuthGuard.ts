/**
 * Inputs :
 *   - options?: { requireAdmin?: boolean }
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 * Outputs :
 *   - { user: AuthUser | null; isAdmin: boolean }
 * File explanation : Used by protected pages. If user is null it calls goTo('login'). If requireAdmin is true and the user is not an admin it pushes an error toast and calls goTo('dashboard').
 */

import { useEffect } from 'react';
import { useApp } from '../shared/AppContext';
import type { AuthUser } from '../shared/types';

export function useAuthGuard(options?: { requireAdmin?: boolean }): {
  user: AuthUser | null;
  isAdmin: boolean;
} {
  const { user, goTo, pushToast } = useApp();
  const requireAdmin = options?.requireAdmin ?? false;
  const isAdmin = Boolean(user?.is_admin);

  useEffect(() => {
    if (!user) {
      goTo('login');
      return;
    }
    if (requireAdmin && !user.is_admin) {
      pushToast('error', 'Admin access required');
      goTo('dashboard');
    }
  }, [user, requireAdmin, goTo, pushToast]);

  return { user, isAdmin };
}
