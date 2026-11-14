/**
 * Inputs :
 *   - props: {} (no props)
 *   - useApp(): AppContextValue (from shared/AppContext.tsx)
 *   - usePolling(listUsers) -> UserSummary[]; inviteUser(body: InviteRequest): Promise<UserSummary>; removeUser(id: number): Promise<OkResponse> (api/adminApi.ts)
 *   - useAuthGuard({ requireAdmin: true }), useAsync, useToast hooks
 * Outputs :
 *   - JSX.Element (PageHeader 'Team', InviteForm, grid of Cards (email, Admin/Member pill, joined date, Remove Button hidden for the current user); Remove opens a confirmation Modal; Skeleton / EmptyState / ErrorState for loading / empty / failed)
 * File explanation : Admin-only user management.
 */

import { useCallback, useEffect, useState } from 'react';
import { Trash2, Users } from 'lucide-react';
import { inviteUser, listUsers, removeUser } from '../api/adminApi';
import { InviteForm } from '../components/features/InviteForm';
import { PageHeader } from '../components/layout/PageHeader';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { Modal } from '../components/ui/Modal';
import { Skeleton } from '../components/ui/Skeleton';
import { StatusPill } from '../components/ui/StatusPill';
import { useAsync } from '../hooks/useAsync';
import { useAuthGuard } from '../hooks/useAuthGuard';
import { usePolling } from '../hooks/usePolling';
import { useToast } from '../hooks/useToast';
import { useApp } from '../shared/AppContext';
import type { StatusTone, UserSummary } from '../shared/types';

const ROLE_LABEL: Record<'admin' | 'member', string> = {
  admin: 'Admin',
  member: 'Member',
};

const ROLE_TONE: Record<'admin' | 'member', StatusTone> = {
  admin: 'info',
  member: 'neutral',
};

export function AdminUsersPage() {
  useAuthGuard({ requireAdmin: true });
  const { user: currentUser } = useApp();
  const toast = useToast();

  const fetchUsers = useCallback(() => listUsers(), []);
  const { data: users, loading, error, refresh } = usePolling<UserSummary[]>(fetchUsers);

  const inviteAction = useAsync(inviteUser);
  const removeAction = useAsync(removeUser);
  const [confirmTarget, setConfirmTarget] = useState<UserSummary | null>(null);

  useEffect(() => {
    if (inviteAction.error) {
      toast.error(inviteAction.error.detail);
    }
  }, [inviteAction.error, toast]);

  useEffect(() => {
    if (removeAction.error) {
      toast.error(removeAction.error.detail);
    }
  }, [removeAction.error, toast]);

  const handleInvite = async (email: string) => {
    const created = await inviteAction.run({ email });
    if (created) {
      toast.success(`Invite sent to ${created.email}`);
      await refresh();
    }
  };

  const handleConfirmRemove = async () => {
    if (!confirmTarget) return;
    const res = await removeAction.run(confirmTarget.id);
    if (res?.ok) {
      toast.success(`Removed ${confirmTarget.email}`);
      setConfirmTarget(null);
      await refresh();
    }
  };

  if (loading && !users) {
    return (
      <div className="space-y-6">
        <PageHeader title="Team" />
        <Skeleton variant="card" count={3} />
      </div>
    );
  }

  if (error && !users) {
    return (
      <div className="space-y-6">
        <PageHeader title="Team" />
        <ErrorState message={error.detail} onRetry={() => void refresh()} />
      </div>
    );
  }

  const list = users ?? [];

  return (
    <div className="space-y-6">
      <PageHeader title="Team" subtitle="Invite teammates and manage access" />

      <InviteForm busy={inviteAction.loading} onInvite={handleInvite} />

      {list.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No team members"
          message="Invite your first teammate using the form above."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {list.map((u, idx) => {
            const roleKey = u.is_admin ? 'admin' : 'member';
            const isSelf = currentUser?.id === u.id;
            const joined = new Date(u.created_at).toLocaleDateString();

            return (
              <Card key={u.id} index={idx} className="flex flex-col justify-between gap-4">
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="text-sm font-semibold text-navy break-all">{u.email}</div>
                    <StatusPill label={ROLE_LABEL[roleKey]} tone={ROLE_TONE[roleKey]} />
                  </div>
                  <div className="text-xs text-navy-mute">Joined {joined}</div>
                </div>

                {!isSelf ? (
                  <div className="pt-2 border-t border-line flex justify-end">
                    <Button
                      variant="danger"
                      icon={Trash2}
                      disabled={removeAction.loading}
                      onClick={() => setConfirmTarget(u)}
                    >
                      Remove
                    </Button>
                  </div>
                ) : null}
              </Card>
            );
          })}
        </div>
      )}

      <Modal
        open={confirmTarget !== null}
        title="Remove team member"
        onClose={() => {
          if (!removeAction.loading) {
            setConfirmTarget(null);
          }
        }}
        footer={
          <>
            <Button
              variant="secondary"
              disabled={removeAction.loading}
              onClick={() => setConfirmTarget(null)}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              icon={Trash2}
              loading={removeAction.loading}
              onClick={() => void handleConfirmRemove()}
            >
              Remove
            </Button>
          </>
        }
      >
        <p>
          Are you sure you want to remove{' '}
          <span className="font-semibold text-navy">{confirmTarget?.email}</span> from Ledgerwise?
          They will immediately lose access.
        </p>
      </Modal>
    </div>
  );
}
