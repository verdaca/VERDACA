/**
 * Team management — arch §1.1, §4.3 RBAC.
 */

export default function TeamPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-foreground">Team</h1>
      <p className="mt-2 text-muted">
        Invite members and manage workspace roles.
      </p>
      <div className="mt-8 rounded-lg border p-6">
        <p className="text-muted">
          Team member management will appear here. Roles: Owner, Member, Viewer.
        </p>
      </div>
    </div>
  );
}
