/**
 * Inputs :
 *   - props: { children: React.ReactNode }
 *   - getStoredToken(): string | null, setStoredToken(token: string | null): void, registerClientHandlers(h: { onUnauthorized: () => void; onRateLimited: () => void }): void (from api/client.ts)
 *   - RATE_LIMIT_TOAST: string, SESSION_EXPIRED_TEXT: string, TOKEN_STORAGE_KEY: string (from shared/constants.ts)
 * Outputs :
 *   - AppProvider(props: { children: ReactNode }): JSX.Element
 *   - useApp(): AppContextValue  (user, screen, selectedCompanyId, selectedThreadCompanyId, toasts, sessionExpired, signIn, signOut, goTo, pushToast, dismissToast)
 * File explanation : The ONLY global state (React Context + useState). On load it restores the user by decoding the JWT payload {user_id, email, is_admin, exp} from localStorage (expired or malformed token => signed out). signIn stores the token and user. signOut clears the token, sets screen 'login'. goTo(screen, companyId?) sets screen and, when companyId is given, selectedCompanyId (screen 'company_detail') or selectedThreadCompanyId (screen 'chat'). Registers client handlers: 401 => signOut + sessionExpired=true + SESSION_EXPIRED_TEXT; 429 => pushToast('error', RATE_LIMIT_TOAST). Toasts get an incrementing id; auto-removal is done by ToastHost.
 */

import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { getStoredToken, registerClientHandlers, setStoredToken } from '../api/client';
import { RATE_LIMIT_TOAST, SESSION_EXPIRED_TEXT, TOKEN_STORAGE_KEY } from './constants';
import type { AppContextValue, AuthUser, ScreenName, Toast, ToastKind } from './types';

interface JwtPayload {
  user_id?: number;
  email?: string;
  is_admin?: boolean;
  exp?: number;
}

function restoreUserFromToken(token: string | null): AuthUser | null {
  if (!token) return null;
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
    const json = atob(padded);
    const payload = JSON.parse(json) as JwtPayload;
    if (
      typeof payload.user_id !== 'number' ||
      typeof payload.email !== 'string' ||
      typeof payload.exp !== 'number'
    ) {
      return null;
    }
    if (payload.exp * 1000 <= Date.now()) {
      return null;
    }
    return {
      id: payload.user_id,
      email: payload.email,
      is_admin: Boolean(payload.is_admin),
    };
  } catch {
    return null;
  }
}

function readInitialUser(): AuthUser | null {
  void TOKEN_STORAGE_KEY;
  const token = getStoredToken();
  const restored = restoreUserFromToken(token);
  if (token && !restored) {
    setStoredToken(null);
  }
  return restored;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [initialUser] = useState<AuthUser | null>(() => readInitialUser());
  const [user, setUser] = useState<AuthUser | null>(initialUser);
  const [screen, setScreen] = useState<ScreenName>(initialUser ? 'dashboard' : 'login');
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);
  const [selectedThreadCompanyId, setSelectedThreadCompanyId] = useState<number | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [sessionExpired, setSessionExpired] = useState(false);
  const nextToastId = useRef(1);

  const pushToast = useCallback((kind: ToastKind, text: string) => {
    const id = nextToastId.current++;
    setToasts((prev) => [...prev, { id, kind, text }]);
  }, []);

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const signIn = useCallback((token: string, nextUser: AuthUser) => {
    setStoredToken(token);
    setUser(nextUser);
    setSessionExpired(false);
  }, []);

  const signOut = useCallback(() => {
    setStoredToken(null);
    setUser(null);
    setSelectedCompanyId(null);
    setSelectedThreadCompanyId(null);
    setScreen('login');
  }, []);

  const goTo = useCallback((nextScreen: ScreenName, companyId?: number) => {
    setScreen(nextScreen);
    if (companyId !== undefined) {
      if (nextScreen === 'company_detail') {
        setSelectedCompanyId(companyId);
      } else if (nextScreen === 'chat') {
        setSelectedThreadCompanyId(companyId);
      }
    }
  }, []);

  useEffect(() => {
    registerClientHandlers({
      onUnauthorized: () => {
        signOut();
        setSessionExpired(true);
        pushToast('error', SESSION_EXPIRED_TEXT);
      },
      onRateLimited: () => {
        pushToast('error', RATE_LIMIT_TOAST);
      },
    });
  }, [signOut, pushToast]);

  const value: AppContextValue = {
    user,
    screen,
    selectedCompanyId,
    selectedThreadCompanyId,
    toasts,
    sessionExpired,
    signIn,
    signOut,
    goTo,
    pushToast,
    dismissToast,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error('useApp must be used inside AppProvider');
  }
  return ctx;
}
