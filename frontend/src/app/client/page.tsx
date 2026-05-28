import { Suspense } from "react";

import { ClientPortalPage } from "@/components/client-portal/ClientPortalPage";

export default function ClientPage() {
  return (
    <Suspense fallback={<main className="client-portal-shell">Chargement</main>}>
      <ClientPortalPage />
    </Suspense>
  );
}
