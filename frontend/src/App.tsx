/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 * Outputs :
 *   - default export App(): JSX.Element
 *   - if user is null: renders ONE auth screen chosen by context.screen ('login' | 'forgot_password' | 'reset_password' | 'accept_invite') inside nothing else
 *   - if user exists: renders <AppShell> containing <PageTransition screenKey={screen}> containing the page for context.screen; also renders <ToastHost /> in both cases
 * File explanation : The screen switcher (there is no router). Maps ScreenName -> page component. Unknown/inaccessible screen falls back to 'dashboard' (or 'login' when signed out). Also guards 'admin_users' for non-admins.
 */

import type { ReactNode } from 'react';
import { AppShell } from './components/layout/AppShell';
import { PageTransition } from './components/layout/PageTransition';
import { ToastHost } from './components/ui/ToastHost';
import { AcceptInvitePage } from './pages/AcceptInvitePage';
import { AdminUsersPage } from './pages/AdminUsersPage';
import { AuthEventsPage } from './pages/AuthEventsPage';
import { BookingsPage } from './pages/BookingsPage';
import { ChangePasswordPage } from './pages/ChangePasswordPage';
import { ChatPage } from './pages/ChatPage';
import { CompaniesPage } from './pages/CompaniesPage';
import { CompanyDetailPage } from './pages/CompanyDetailPage';
import { ContactsNeededPage } from './pages/ContactsNeededPage';
import { ConversationsPage } from './pages/ConversationsPage';
import { DashboardPage } from './pages/DashboardPage';
import { EmailReviewPage } from './pages/EmailReviewPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { HumanReviewPage } from './pages/HumanReviewPage';
import { LoginPage } from './pages/LoginPage';
import { ResearchPage } from './pages/ResearchPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { useApp } from './shared/AppContext';
import type { ScreenName } from './shared/types';

const AUTH_SCREENS: ScreenName[] = [
  'login',
  'forgot_password',
  'reset_password',
  'accept_invite',
];

function renderAuthScreen(screen: ScreenName): ReactNode {
  switch (screen) {
    case 'forgot_password':
      return <ForgotPasswordPage />;
    case 'reset_password':
      return <ResetPasswordPage />;
    case 'accept_invite':
      return <AcceptInvitePage />;
    case 'login':
    default:
      return <LoginPage />;
  }
}

function renderSignedInScreen(screen: ScreenName): ReactNode {
  switch (screen) {
    case 'change_password':
      return <ChangePasswordPage />;
    case 'admin_users':
      return <AdminUsersPage />;
    case 'auth_events':
      return <AuthEventsPage />;
    case 'research':
      return <ResearchPage />;
    case 'companies':
      return <CompaniesPage />;
    case 'company_detail':
      return <CompanyDetailPage />;
    case 'human_review':
      return <HumanReviewPage />;
    case 'contacts_needed':
      return <ContactsNeededPage />;
    case 'email_review':
      return <EmailReviewPage />;
    case 'conversations':
      return <ConversationsPage />;
    case 'chat':
      return <ChatPage />;
    case 'bookings':
      return <BookingsPage />;
    case 'dashboard':
    default:
      return <DashboardPage />;
  }
}

export default function App() {
  const { user, screen } = useApp();

  if (!user) {
    const authScreen: ScreenName = AUTH_SCREENS.includes(screen) ? screen : 'login';
    return (
      <>
        {renderAuthScreen(authScreen)}
        <ToastHost />
      </>
    );
  }

  const resolvedScreen: ScreenName =
    screen === 'admin_users' && !user.is_admin
      ? 'dashboard'
      : AUTH_SCREENS.includes(screen)
        ? 'dashboard'
        : screen;

  return (
    <>
      <AppShell>
        <PageTransition screenKey={resolvedScreen}>
          {renderSignedInScreen(resolvedScreen)}
        </PageTransition>
      </AppShell>
      <ToastHost />
    </>
  );
}
