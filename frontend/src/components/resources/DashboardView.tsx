"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  Bell,
  Building2,
  Car,
  CheckCircle2,
  Contact,
  CreditCard,
  FileText,
  RefreshCcw,
  ShieldCheck,
  Users,
} from "lucide-react";

import { fetchDashboard } from "@/lib/api";
import { canCreate, canEdit, resourcesForRole } from "@/lib/resources";
import type { DashboardPayload } from "@/types/api";
import { useAuth } from "@/components/auth/AuthProvider";

const metricIcons = {
  groups: Building2,
  users: Users,
  contributors: Users,
  clients: Contact,
  vehicles: Car,
  quotes: FileText,
  payments: CreditCard,
  confirmed_payments: CheckCircle2,
  contracts: ShieldCheck,
  issued_contracts: CheckCircle2,
  commissions: CreditCard,
  wallets: CreditCard,
  audit_logs: AlertCircle,
  unread_notifications: Bell,
};

const metricLabels = {
  groups: "Groupes",
  users: "Utilisateurs",
  contributors: "Apporteurs",
  clients: "Clients",
  vehicles: "Vehicules",
  quotes: "Devis",
  payments: "Paiements",
  confirmed_payments: "Paiements confirmes",
  contracts: "Contrats",
  issued_contracts: "Contrats emis",
  commissions: "Commissions",
  wallets: "Wallets",
  audit_logs: "Audit logs",
  unread_notifications: "Notifications",
};

export function DashboardView() {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const visibleResources = useMemo(() => resourcesForRole(user?.role), [user?.role]);

  async function loadDashboard() {
    setLoading(true);
    setError("");
    try {
      setDashboard(await fetchDashboard());
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Dashboard indisponible");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  return (
    <main className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Perimetre {dashboard?.scope ?? "-"}</p>
          <h1>Dashboard</h1>
        </div>
        <button className="secondary-button" onClick={loadDashboard} type="button">
          <RefreshCcw size={16} />
          Actualiser
        </button>
      </div>

      {error ? <p className="form-error">{error}</p> : null}

      <section className="metrics-grid" aria-busy={loading}>
        {Object.entries(metricLabels).map(([key, label]) => {
          const Icon = metricIcons[key as keyof typeof metricIcons];
          const value = dashboard?.counts[key as keyof DashboardPayload["counts"]] ?? 0;
          return (
            <article className="metric-tile" key={key}>
              <Icon size={19} />
              <span>{label}</span>
              <strong>{loading ? "..." : value}</strong>
            </article>
          );
        })}
      </section>

      <section className="work-grid">
        <Link className="work-link" href="/production">
          <strong>Production</strong>
          <span>Suivi contrats, paiements et emissions</span>
        </Link>
        {visibleResources.map((resource) => (
          <Link className="work-link" href={`/resources/${resource.slug}`} key={resource.slug}>
            <strong>{resource.label}</strong>
            <span>{canCreate(resource) || canEdit(resource) ? "Gestion" : "Consultation"}</span>
          </Link>
        ))}
      </section>
    </main>
  );
}
