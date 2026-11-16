/**
 * Inputs :
 *   - props: { children: React.ReactNode }
 *   - getStoredToken(): string | null, setStoredToken(token: string | null): void, registerClientHandlers(h: { onUnauthorized: () => void; onRateLimited: () => void }): void (from api/client.ts)
 *   - sessionStorage key ledgerwise.navigation.v1: { userId: number; screen: ScreenName; selectedCompanyId: number | null; selectedThreadCompanyId: number | null }
 * Outputs :
 *   - AppProvider(props: { children: ReactNode }): JSX.Element
 *   - useApp(): AppContextValue (user, screen, selectedCompanyId, selectedThreadCompanyId, toasts, sessionExpired, signIn, signOut, goTo, pushToast, dismissToast)
 * File explanation : Owns global React state. Restores the authenticated user's current screen and selected entity from tab-scoped sessionStorage, validates the saved user and IDs, persists navigation changes, and clears stored navigation on sign-out. JWT validation and 401/429 handlers remain unchanged.
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


const NAVIGATION_STORAGE_KEY = 'ledgerwise.navigation.v1';
interface StoredNavigation {
  userId: number;
  screen: ScreenName;
  selectedCompanyId: number | null;
  selectedThreadCompanyId: number | null;
}
function isScreenName(value: unknown): value is ScreenName {
  const screens: ScreenName[] = ['login','forgot_password','reset_password','accept_invite','change_password','admin_users','auth_events','dashboard','research','companies','company_detail','human_review','contacts_needed','email_review','conversations','chat','bookings'];
  return typeof value === 'string' && screens.includes(value as ScreenName);
}
function validSelectionId(value: unknown): number | null {
  return typeof value === 'number' && Number.isSafeInteger(value) && value > 0 ? value : null;
}
function readInitialNavigation(user: AuthUser | null): StoredNavigation | null {
  if (!user || typeof window === 'undefined') return null;
  try {
    const raw = window.sessionStorage.getItem(NAVIGATION_STORAGE_KEY);
    if (!raw) return null;
    const saved = JSON.parse(raw) as Partial<StoredNavigation>;
    if (saved.userId !== user.id || !isScreenName(saved.screen)) return null;
    let screen = saved.screen;
    const companyId = validSelectionId(saved.selectedCompanyId);
    const threadId = validSelectionId(saved.selectedThreadCompanyId);
    if (screen === 'admin_users' && !user.is_admin) screen = 'dashboard';
    if (screen === 'company_detail' && companyId === null) screen = 'companies';
    if (screen === 'chat' && threadId === null) screen = 'conversations';
    return {
      userId: user.id, screen,
      selectedCompanyId: screen === 'company_detail' ? companyId : null,
      selectedThreadCompanyId: screen === 'chat' ? threadId : null,
    };
  } catch { return null; }
}
function clearStoredNavigation(): void {
  try {
    if (typeof window !== 'undefined') window.sessionStorage.removeItem(NAVIGATION_STORAGE_KEY);
  } catch { /* Storage can be unavailable in restricted browsing contexts. */ }
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [initialUser] = useState<AuthUser | null>(() => readInitialUser());
  const [user, setUser] = useState<AuthUser | null>(initialUser);
  const [initialNavigation] = useState<StoredNavigation | null>(() => readInitialNavigation(initialUser));
  const [screen, setScreen] = useState<ScreenName>(initialNavigation?.screen ?? (initialUser ? 'dashboard' : 'login'));
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(initialNavigation?.selectedCompanyId ?? null);
  const [selectedThreadCompanyId, setSelectedThreadCompanyId] = useState<number | null>(initialNavigation?.selectedThreadCompanyId ?? null);
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
    clearStoredNavigation();
    setStoredToken(null);
    setUser(null);
    setSelectedCompanyId(null);
    setSelectedThreadCompanyId(null);
    setScreen('login');
  }, []);

  const goTo = useCallback((nextScreen: ScreenName, companyId?: number) => {
    setScreen(nextScreen);
    if (nextScreen === 'company_detail') {
      setSelectedCompanyId(validSelectionId(companyId));
      setSelectedThreadCompanyId(null);
    } else if (nextScreen === 'chat') {
      setSelectedThreadCompanyId(validSelectionId(companyId));
      setSelectedCompanyId(null);
    } else {
      setSelectedCompanyId(null);
      setSelectedThreadCompanyId(null);
    }
  }, []);

  useEffect(() => {
    if (!user) {
      clearStoredNavigation();
      return;
    }
    if (['login', 'forgot_password', 'reset_password', 'accept_invite'].includes(screen)) return;
    const navigation: StoredNavigation = { userId: user.id, screen, selectedCompanyId, selectedThreadCompanyId };
    try {
      window.sessionStorage.setItem(NAVIGATION_STORAGE_KEY, JSON.stringify(navigation));
    } catch {
      // Navigation still works for the current page when storage is unavailable.
    }
  }, [user, screen, selectedCompanyId, selectedThreadCompanyId]);

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
