/**
 * Billing settings — arch §1.1.
 *
 * Stripe Customer Portal embed for self-service billing.
 */

export default function BillingPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-foreground">Billing</h1>
      <p className="mt-2 text-muted">
        Manage your payment methods and view invoices.
      </p>
      <div className="mt-8 rounded-lg border p-6">
        <p className="text-muted">
          Stripe Customer Portal will be embedded here.
        </p>
      </div>
    </div>
  );
}
