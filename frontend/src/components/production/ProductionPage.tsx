"use client";

import { type FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  ChevronLeft,
  ChevronRight,
  FileText,
  RefreshCcw,
  Search,
  ShieldCheck,
  Truck,
} from "lucide-react";

import { fetchProduction } from "@/lib/api";
import { displayValue, formatDate, formatMoney } from "@/lib/format";
import {
  buildProductionSearchParams,
  DEFAULT_PRODUCTION_FILTERS,
  type ProductionFilters,
} from "@/lib/production";
import type { ProductionPayload, ProductionRow } from "@/types/api";

const productOptions = ["AUTO", "MOTO", "TRAILER", "SCHOOL_BUS", "GARAGE", "FLEET"];
const contractStatusOptions = ["ISSUED", "READY_TO_ISSUE", "DRAFT", "CANCELLED"];
const paymentStatusOptions = ["CONFIRMED", "PENDING", "FAILED", "CANCELLED"];

export function ProductionPage() {
  const [filters, setFilters] = useState<ProductionFilters>(DEFAULT_PRODUCTION_FILTERS);
  const [payload, setPayload] = useState<ProductionPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const params = useMemo(() => buildProductionSearchParams(filters), [filters]);

  async function loadProduction(nextFilters = filters) {
    setLoading(true);
    setError("");
    try {
      setPayload(await fetchProduction(buildProductionSearchParams(nextFilters)));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Production indisponible");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadProduction();
  }, [filters.page]);

  function updateFilter<K extends keyof ProductionFilters>(
    key: K,
    value: ProductionFilters[K],
  ) {
    setFilters((current) => ({
      ...current,
      [key]: value,
      page: key === "page" ? Number(value) : 1,
    }));
  }

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextFilters = { ...filters, page: 1 };
    setFilters(nextFilters);
    void loadProduction(nextFilters);
  }

  const summary = payload?.summary;

  return (
    <main className="page production-page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Production {payload?.scope ?? "-"}</p>
          <h1>Production</h1>
        </div>
        <div className="toolbar">
          <button className="secondary-button" onClick={() => loadProduction()} type="button">
            <RefreshCcw size={16} />
            Actualiser
          </button>
        </div>
      </div>

      <form className="filter-panel" onSubmit={applyFilters}>
        <label>
          Jour
          <select
            value={filters.today ? "true" : ""}
            onChange={(event) => updateFilter("today", event.target.value === "true")}
          >
            <option value="">Tous</option>
            <option value="true">Aujourd'hui</option>
          </select>
        </label>
        <label>
          Mois
          <input
            type="month"
            value={filters.month}
            onChange={(event) => updateFilter("month", event.target.value)}
          />
        </label>
        <label>
          Debut
          <input
            type="date"
            value={filters.date_debut}
            onChange={(event) => updateFilter("date_debut", event.target.value)}
          />
        </label>
        <label>
          Fin
          <input
            type="date"
            value={filters.date_fin}
            onChange={(event) => updateFilter("date_fin", event.target.value)}
          />
        </label>
        <label>
          Produit
          <select
            value={filters.product}
            onChange={(event) => updateFilter("product", event.target.value)}
          >
            <option value="">Tous</option>
            {productOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
        <label>
          Statut contrat
          <select
            value={filters.contract_status}
            onChange={(event) => updateFilter("contract_status", event.target.value)}
          >
            <option value="">Tous</option>
            {contractStatusOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
        <label>
          Statut paiement
          <select
            value={filters.payment_status}
            onChange={(event) => updateFilter("payment_status", event.target.value)}
          >
            <option value="">Tous</option>
            {paymentStatusOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
        <label>
          Emis
          <select
            value={filters.issued}
            onChange={(event) => updateFilter("issued", event.target.value)}
          >
            <option value="">Tous</option>
            <option value="true">Emis</option>
            <option value="false">Non emis</option>
          </select>
        </label>
        <label>
          Remorque
          <select
            value={filters.with_trailer}
            onChange={(event) => updateFilter("with_trailer", event.target.value)}
          >
            <option value="">Tous</option>
            <option value="true">Avec remorque</option>
            <option value="false">Sans remorque</option>
          </select>
        </label>
        <label>
          Immatriculation
          <input
            autoComplete="off"
            value={filters.registration_number}
            onChange={(event) => updateFilter("registration_number", event.target.value)}
            placeholder="DK-1234"
          />
        </label>
        <label>
          Client
          <input
            autoComplete="off"
            value={filters.client}
            onChange={(event) => updateFilter("client", event.target.value)}
            placeholder="Nom ou telephone"
          />
        </label>
        <label>
          Apporteur
          <input
            autoComplete="off"
            value={filters.contributor}
            onChange={(event) => updateFilter("contributor", event.target.value)}
            placeholder="ID ou login"
          />
        </label>
        <label>
          Groupe
          <input
            autoComplete="off"
            value={filters.group}
            onChange={(event) => updateFilter("group", event.target.value)}
            placeholder="ID, slug ou nom"
          />
        </label>
        <button className="primary-button filter-submit" type="submit">
          <Search size={16} />
          Filtrer
        </button>
      </form>

      {error ? <p className="form-error">{error}</p> : null}

      {summary ? (
        <section className="metrics-grid">
          <SummaryTile icon={<FileText size={19} />} label="Total lignes" value={summary.total_items} />
          <SummaryTile icon={<ShieldCheck size={19} />} label="Contrats emis" value={summary.issued_contracts} />
          <SummaryTile icon={<BarChart3 size={19} />} label="Montant paye" value={formatMoney(summary.total_paid_amount)} />
          <SummaryTile icon={<BarChart3 size={19} />} label="Commissions" value={formatMoney(summary.total_commission_amount)} />
          <SummaryTile icon={<Truck size={19} />} label="Avec remorque" value={summary.contracts_with_trailer} />
        </section>
      ) : null}

      <section className="table-frame" aria-busy={loading}>
        <table>
          <thead>
            <tr>
              <th>Reference</th>
              <th>Client</th>
              <th>Vehicule</th>
              <th>Produit</th>
              <th>Contrat</th>
              <th>Paiement</th>
              <th>Montant</th>
              <th>Commission</th>
              <th>Apporteur</th>
              <th>Groupe</th>
              <th>Creation</th>
              <th>Docs</th>
            </tr>
          </thead>
          <tbody>
            {payload?.results.length ? (
              payload.results.map((row) => <ProductionRowView key={row.entry_id} row={row} />)
            ) : (
              <tr>
                <td className="empty-cell" colSpan={12}>
                  {loading ? "Chargement..." : "Aucune production"}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <div className="pagination">
        <button
          className="icon-button text-button"
          disabled={!payload?.pagination.has_previous}
          onClick={() => updateFilter("page", Math.max(1, filters.page - 1))}
          type="button"
        >
          <ChevronLeft size={16} />
          Precedent
        </button>
        <span>
          Page {payload?.pagination.page ?? filters.page} / {payload?.pagination.total_pages ?? 1}
        </span>
        <button
          className="icon-button text-button"
          disabled={!payload?.pagination.has_next}
          onClick={() => updateFilter("page", filters.page + 1)}
          type="button"
        >
          Suivant
          <ChevronRight size={16} />
        </button>
      </div>

      {payload ? <Breakdowns payload={payload} /> : null}

      <p className="api-hint">Filtres actifs: {params.toString() || "aucun"}</p>
    </main>
  );
}

function ProductionRowView({ row }: { row: ProductionRow }) {
  return (
    <tr>
      <td>{row.contract_reference || row.entry_id}</td>
      <td>
        <strong>{row.client}</strong>
        <br />
        <span className="muted-text">{row.client_phone}</span>
      </td>
      <td>
        {row.registration_number}
        <br />
        <span className="muted-text">{row.vehicle}</span>
      </td>
      <td>{row.product}</td>
      <td>
        <span className="status-pill">{row.contract_status}</span>
      </td>
      <td>{row.payment_status ? <span className="status-pill">{row.payment_status}</span> : "-"}</td>
      <td>{formatMoney(row.amount)}</td>
      <td>{formatMoney(row.commission)}</td>
      <td>{displayValue(row.contributor.display_name || row.contributor.username)}</td>
      <td>{row.group.name}</td>
      <td>{formatDate(row.created_at)}</td>
      <td>
        {row.documents_available_count}
        {row.has_trailer ? " / remorque" : ""}
      </td>
    </tr>
  );
}

function SummaryTile({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: number | string;
}) {
  return (
    <article className="metric-tile">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function Breakdowns({ payload }: { payload: ProductionPayload }) {
  return (
    <section className="production-breakdowns">
      <BreakdownList
        items={payload.breakdowns.daily.slice(0, 7).map((item) => ({
          key: item.date,
          label: item.date,
          value: item.total_items,
        }))}
        title="Journalier"
      />
      <BreakdownList
        items={payload.breakdowns.monthly.slice(0, 6).map((item) => ({
          key: item.month,
          label: item.month,
          value: item.total_amount,
        }))}
        money
        title="Mensuel"
      />
      <BreakdownList
        items={payload.breakdowns.by_contributor.slice(0, 8).map((item) => ({
          key: String(item.id ?? item.username),
          label: item.display_name || item.username,
          value: item.total_items,
        }))}
        title="Par apporteur"
      />
    </section>
  );
}

function BreakdownList({
  items,
  money,
  title,
}: {
  items: Array<{ key: string; label: string; value: number | string }>;
  money?: boolean;
  title: string;
}) {
  return (
    <div className="breakdown-panel">
      <h2>{title}</h2>
      {items.length ? (
        <div className="mini-list">
          {items.map((item) => (
            <div key={item.key}>
              <span>{item.label}</span>
              <strong>{money ? formatMoney(item.value) : item.value}</strong>
            </div>
          ))}
        </div>
      ) : (
        <p className="empty-panel">Aucune donnee</p>
      )}
    </div>
  );
}
