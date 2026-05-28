import { Suspense } from "react";

import { ClientPortalPage } from "@/components/client-portal/ClientPortalPage";

export default function ClientSpaceAccessPage() {
  return (
    <Suspense fallback={<main className="client-portal-shell">Chargement</main>}>
      <ClientPortalPage />
    </Suspense>
  );
}
