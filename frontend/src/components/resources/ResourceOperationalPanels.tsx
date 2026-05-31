"use client";

import { useEffect, useState } from "react";
import {
  CheckCircle2,
  FileText,
  RefreshCcw,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from "lucide-react";

import {
  fetchContractDiotaliVerification,
  fetchContractDocuments,
  fetchContractIssueReadiness,
  fetchQuoteSummary,
} from "@/lib/api";
import { displayValue, formatDate, formatMoney } from "@/lib/format";
import type {
  ApiRecord,
  ContractDocumentItem,
  ContractDocumentsPayload,
  DiotaliVerificationPayload,
  GuaranteeSummary,
  IssueReadinessPayload,
  QuoteSummary,
} from "@/types/api";

export function ResourceOperationalPanels({
  record,
  resourceSlug,
}: {
  record: ApiRecord;
  resourceSlug: string;
}) {
  const id = record.id;
  if (id === undefined) {
    return null;
  }
  if (resourceSlug === "quotes") {
    return <QuoteSummaryPanel quoteId={id} />;
  }
  if (resourceSlug === "contracts") {
    return <ContractOperationalPanel contractId={id} />;
  }
  return null;
}

function QuoteSummaryPanel({ quoteId }: { quoteId: number | string }) {
  const [summary, setSummary] = useState<QuoteSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadSummary() {
    setLoading(true);
    setError("");
    try {
      setSummary(await fetchQuoteSummary(quoteId));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Resume indisponible");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSummary();
  }, [quoteId]);

  return (
    <section className="operational-section" aria-busy={loading}>
      <div className="section-title-row">
        <div>
          <p className="eyebrow">Resume proposition</p>
          <h2>Avant validation</h2>
        </div>
        <button className="icon-button" onClick={loadSummary} title="Actualiser" type="button">
          <RefreshCcw size={16} />
        </button>
      </div>

      {error ? <p className="form-error">{error}</p> : null}
      {!summary && !error ? <p className="empty-panel">Chargement du resume...</p> : null}

      {summary ? (
        <div className="operational-stack">
          <div className="summary-grid compact">
            <Metric label="Client" value={String(summary.client.display_name ?? "-")} />
            <Metric
              label="Vehicule"
              value={`${displayValue(summary.vehicle.registration_number)} - ${displayValue(
                summary.vehicle.brand,
              )}`}
            />
            <Metric label="Produit" value={summary.references.product.label} />
            <Metric
              label="Validite"
              value={`${displayValue(summary.validity.effective_date)} -> ${displayValue(
                summary.validity.expiration_date,
              )}`}
            />
            <Metric label="RC" value={formatMoney(summary.amounts.civil_liability_amount)} />
            <Metric label="Frais" value={formatMoney(summary.amounts.fees_amount)} />
            <Metric label="Commission" value={formatMoney(summary.amounts.commission_total_amount)} />
            <Metric label="Total a verser" value={formatMoney(summary.amounts.total_to_pay)} />
          </div>

          <ReferenceLine summary={summary} />
          <GuaranteeList
            guarantees={summary.guarantees.mandatory}
            title="Garanties obligatoires"
          />
          <GuaranteeList guarantees={summary.guarantees.optional} title="Garanties optionnelles" />
          <DocumentList documents={summary.expected_documents} title="Documents attendus" />

          <div className={summary.can_issue.allowed ? "readiness-banner ok" : "readiness-banner warn"}>
            {summary.can_issue.allowed ? <ShieldCheck size={17} /> : <ShieldAlert size={17} />}
            <span>
              {summary.can_issue.allowed
                ? "Emission possible apres paiement et creation du contrat."
                : summary.can_issue.reasons.join(" ")}
            </span>
          </div>

          <div className="readiness-banner">
            <FileText size={17} />
            <span>
              Remorque: {summary.trailer_rule.visible ? "section visible" : "section masquee"} (
              {summary.trailer_rule.source})
            </span>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function ContractOperationalPanel({ contractId }: { contractId: number | string }) {
  const [documents, setDocuments] = useState<ContractDocumentsPayload | null>(null);
  const [readiness, setReadiness] = useState<IssueReadinessPayload | null>(null);
  const [verification, setVerification] = useState<DiotaliVerificationPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [verificationLoading, setVerificationLoading] = useState(false);
  const [error, setError] = useState("");
  const [verificationError, setVerificationError] = useState("");

  async function loadContractContext() {
    setLoading(true);
    setError("");
    try {
      const [readinessPayload, documentsPayload] = await Promise.all([
        fetchContractIssueReadiness(contractId),
        fetchContractDocuments(contractId),
      ]);
      setReadiness(readinessPayload);
      setDocuments(documentsPayload);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Controle contrat indisponible");
    } finally {
      setLoading(false);
    }
  }

  async function runDiotaliVerification() {
    setVerificationLoading(true);
    setVerificationError("");
    try {
      setVerification(await fetchContractDiotaliVerification(contractId));
    } catch (caughtError) {
      setVerificationError(
        caughtError instanceof Error ? caughtError.message : "Verification Diotali impossible",
      );
    } finally {
      setVerificationLoading(false);
    }
  }

  useEffect(() => {
    void loadContractContext();
  }, [contractId]);

  return (
    <section className="operational-section" aria-busy={loading}>
      <div className="section-title-row">
        <div>
          <p className="eyebrow">Emission et documents</p>
          <h2>Controles Diotali</h2>
        </div>
        <div className="toolbar">
          <button className="icon-button" onClick={loadContractContext} title="Actualiser" type="button">
            <RefreshCcw size={16} />
          </button>
          <button
            className="secondary-button"
            disabled={verificationLoading}
            onClick={runDiotaliVerification}
            type="button"
          >
            <ShieldCheck size={16} />
            {verificationLoading ? "Verification..." : "Verifier Diotali"}
          </button>
        </div>
      </div>

      {error ? <p className="form-error">{error}</p> : null}

      {readiness ? (
        <div className={readiness.ready ? "readiness-banner ok" : "readiness-banner warn"}>
          {readiness.ready ? <CheckCircle2 size={17} /> : <ShieldAlert size={17} />}
          <span>
            {readiness.ready
              ? "Contrat pret pour emission locale."
              : "Corrections requises avant emission."}
          </span>
        </div>
      ) : null}

      {readiness?.checks.length ? (
        <div className="check-list">
          {readiness.checks.map((check) => (
            <div className="check-row" key={check.code}>
              {check.passed ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
              <span>{check.passed ? check.success : check.failure}</span>
            </div>
          ))}
        </div>
      ) : null}

      {documents ? (
        <>
          <DocumentList documents={documents.documents} title="Documents contrat" />
          {documents.trailer_documents.applies ? (
            <div
              className={
                documents.trailer_documents.complete
                  ? "readiness-banner ok"
                  : "readiness-banner warn"
              }
            >
              <FileText size={17} />
              <span>
                Remorque: {documents.trailer_documents.complete ? "4 documents disponibles" : "4 documents attendus"}.
                Tracteur {displayValue(documents.trailer_documents.reference_vehicle)}.
              </span>
            </div>
          ) : null}
        </>
      ) : null}

      {verificationError ? <p className="form-error">{verificationError}</p> : null}
      {verification ? <DiotaliResult verification={verification} /> : null}
    </section>
  );
}

function ReferenceLine({ summary }: { summary: QuoteSummary }) {
  const references = [
    ["Marque", summary.references.brand],
    ["Genre", summary.references.genre],
    ["Energie", summary.references.energy],
    ["Produit", summary.references.product],
    ["Duree", summary.references.duration],
  ] as const;

  return (
    <div className="tag-row">
      {references.map(([label, reference]) => (
        <span className="tag" key={label}>
          {label}: {displayValue(reference.label)} ({displayValue(reference.source)})
        </span>
      ))}
    </div>
  );
}

function GuaranteeList({
  guarantees,
  title,
}: {
  guarantees: GuaranteeSummary[];
  title: string;
}) {
  if (!guarantees.length) {
    return null;
  }
  return (
    <div>
      <h3 className="subheading">{title}</h3>
      <div className="tag-row">
        {guarantees.map((guarantee) => (
          <span
            className={guarantee.selected ? "tag ok" : "tag"}
            key={`${title}-${guarantee.code}`}
          >
            {guarantee.label}
            {guarantee.is_readonly ? " readonly" : ""}
          </span>
        ))}
      </div>
    </div>
  );
}

function DocumentList({
  documents,
  title,
}: {
  documents: ContractDocumentItem[];
  title: string;
}) {
  if (!documents.length) {
    return null;
  }
  return (
    <div>
      <h3 className="subheading">{title}</h3>
      <div className="document-list">
        {documents.map((document) => (
          <div className="document-row" key={`${document.code}-${document.vehicle_role}`}>
            <div>
              <strong>{document.label}</strong>
              <span>
                {document.vehicle_role} - {document.document_kind}
              </span>
            </div>
            <span className={document.available ? "availability ok" : "availability"}>
              {document.available ? "Disponible" : "Attendu"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DiotaliResult({ verification }: { verification: DiotaliVerificationPayload }) {
  const details = verification.verification;
  const blocksIssue = Boolean(details.blocks_issue);
  return (
    <div className={blocksIssue ? "readiness-banner warn" : "readiness-banner ok"}>
      {blocksIssue ? <ShieldAlert size={17} /> : <CheckCircle2 size={17} />}
      <span>
        Diotali {displayValue(details.status)} - {displayValue(details.message)}
        {details.suggested_effective_date
          ? ` Date conseillee: ${formatDate(details.suggested_effective_date)}.`
          : ""}
      </span>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="summary-cell">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
