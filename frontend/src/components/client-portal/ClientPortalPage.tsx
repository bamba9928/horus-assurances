"use client";

import {
  Bell,
  Download,
  FileCheck2,
  FileText,
  LockKeyhole,
  LogOut,
  RefreshCcw,
  ShieldCheck,
} from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApiError } from "@/lib/api";
import {
  downloadClientDocument,
  fetchClientPortalContracts,
  fetchClientPortalDocuments,
  fetchClientPortalNotifications,
  fetchClientPortalProfile,
  loginClientPortal,
  logoutClientPortal,
  requestClientDocumentOtp,
} from "@/lib/client-portal-api";
import type {
  ClientDocumentKind,
  ClientPortalContract,
  ClientPortalDocuments,
  ClientPortalNotification,
  ClientPortalProfile,
} from "@/types/api";

type OtpState = Record<ClientDocumentKind, string>;

const EMPTY_OTP: OtpState = {
  attestation: "",
  carte_brune: "",
};

export function ClientPortalPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const handledUrlToken = useRef(false);
  const [token, setToken] = useState("");
  const [profile, setProfile] = useState<ClientPortalProfile | null>(null);
  const [contracts, setContracts] = useState<ClientPortalContract[]>([]);
  const [documents, setDocuments] = useState<ClientPortalDocuments | null>(null);
  const [notifications, setNotifications] = useState<ClientPortalNotification[]>([]);
  const [selectedContractId, setSelectedContractId] = useState<number | null>(null);
  const [otpByKind, setOtpByKind] = useState<OtpState>(EMPTY_OTP);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const targetContractId = useMemo(() => {
    const rawValue = searchParams.get("contract");
    const value = rawValue ? Number(rawValue) : 0;
    return Number.isFinite(value) && value > 0 ? value : null;
  }, [searchParams]);

  const selectedContract = useMemo(
    () => contracts.find((contract) => contract.id === selectedContractId) ?? null,
    [contracts, selectedContractId],
  );

  const loadPortal = useCallback(async (preferredContractId: number | null = null) => {
    setLoading(true);
    setError("");
    try {
      const [profilePayload, contractsPayload, notificationsPayload] = await Promise.all([
        fetchClientPortalProfile(),
        fetchClientPortalContracts(),
        fetchClientPortalNotifications(),
      ]);
      setProfile(profilePayload);
      setContracts(contractsPayload);
      setNotifications(notificationsPayload);

      const nextContract =
        contractsPayload.find((contract) => contract.id === preferredContractId) ??
        contractsPayload[0] ??
        null;
      setSelectedContractId(nextContract?.id ?? null);

      if (nextContract) {
        const documentsPayload = await fetchClientPortalDocuments(nextContract.id);
        setDocuments(documentsPayload);
      } else {
        setDocuments(null);
      }
    } catch (caughtError) {
      setProfile(null);
      setContracts([]);
      setNotifications([]);
      setSelectedContractId(null);
      setDocuments(null);
      if (caughtError instanceof ApiError && caughtError.status !== 401) {
        setError(caughtError.message);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const rawToken = searchParams.get("token")?.trim() ?? "";
    if (rawToken && !handledUrlToken.current) {
      handledUrlToken.current = true;
      setToken(rawToken);
      void submitToken(rawToken, targetContractId).then(() => {
        router.replace("/client");
      });
      return;
    }

    void loadPortal(targetContractId);
  }, [loadPortal, router, searchParams, targetContractId]);

  async function submitToken(rawToken: string, preferredContractId: number | null) {
    setWorking(true);
    setError("");
    setNotice("");
    try {
      const profilePayload = await loginClientPortal(rawToken);
      setProfile(profilePayload);
      await loadPortal(preferredContractId);
      setToken("");
      setNotice("Acces client active.");
    } catch (caughtError) {
      setProfile(null);
      setLoading(false);
      setError(caughtError instanceof Error ? caughtError.message : "Jeton invalide.");
    } finally {
      setWorking(false);
    }
  }

  async function handleTokenSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitToken(token, null);
  }

  async function handleContractChange(contractId: number) {
    setSelectedContractId(contractId);
    setDocuments(null);
    setOtpByKind(EMPTY_OTP);
    setError("");
    try {
      const documentsPayload = await fetchClientPortalDocuments(contractId);
      setDocuments(documentsPayload);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Contrat indisponible.");
    }
  }

  async function handleOtpRequest(documentKind: ClientDocumentKind) {
    if (!selectedContractId) {
      return;
    }
    setWorking(true);
    setError("");
    setNotice("");
    try {
      const response = await requestClientDocumentOtp(selectedContractId, documentKind);
      if (response.otp) {
        setOtpByKind((current) => ({ ...current, [documentKind]: response.otp ?? "" }));
      }
      setNotice(
        response.secret_returned
          ? "OTP mock genere pour le developpement."
          : "OTP envoye par le provider configure.",
      );
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "OTP refuse.");
    } finally {
      setWorking(false);
    }
  }

  async function handleDownload(documentKind: ClientDocumentKind) {
    if (!selectedContractId) {
      return;
    }
    const otp = otpByKind[documentKind].trim();
    if (!otp) {
      setError("OTP obligatoire pour ouvrir le document.");
      return;
    }

    setWorking(true);
    setError("");
    setNotice("");
    try {
      const response = await downloadClientDocument(selectedContractId, documentKind, otp);
      window.open(response.download_url, "_blank", "noopener,noreferrer");
      setOtpByKind((current) => ({ ...current, [documentKind]: "" }));
      setNotice("Document autorise.");
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Document refuse.");
    } finally {
      setWorking(false);
    }
  }

  async function handleLogout() {
    setWorking(true);
    try {
      await logoutClientPortal();
    } finally {
      setProfile(null);
      setContracts([]);
      setNotifications([]);
      setSelectedContractId(null);
      setDocuments(null);
      setOtpByKind(EMPTY_OTP);
      setNotice("");
      setWorking(false);
    }
  }

  if (loading) {
    return (
      <main className="client-portal-shell">
        <div className="client-loading">Chargement</div>
      </main>
    );
  }

  if (!profile) {
    return (
      <main className="client-portal-shell compact">
        <section className="client-access-panel">
          <div className="client-brand">
            <span className="brand-mark">H</span>
            <div>
              <p className="eyebrow">Horus Assurances</p>
              <h1>Espace client</h1>
            </div>
          </div>
          <form className="form-stack" onSubmit={handleTokenSubmit}>
            <label htmlFor="client-token">
              Jeton d'acces
              <input
                id="client-token"
                autoComplete="one-time-code"
                value={token}
                onChange={(event) => setToken(event.target.value)}
                placeholder="Jeton client"
              />
            </label>
            {error ? <p className="form-error">{error}</p> : null}
            <button className="primary-button" disabled={working} type="submit">
              <LockKeyhole size={16} aria-hidden />
              Ouvrir
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="client-portal-shell">
      <header className="client-portal-header">
        <div className="client-brand">
          <span className="brand-mark">H</span>
          <div>
            <p className="eyebrow">Horus Assurances</p>
            <h1>{profile.display_name}</h1>
          </div>
        </div>
        <button className="secondary-button" disabled={working} onClick={handleLogout} type="button">
          <LogOut size={16} aria-hidden />
          Fermer
        </button>
      </header>

      {error ? <p className="form-error">{error}</p> : null}
      {notice ? <p className="form-notice">{notice}</p> : null}

      <section className="client-summary-grid">
        <div className="client-summary-tile">
          <ShieldCheck size={18} aria-hidden />
          <span>Groupe</span>
          <strong>{profile.partner_group_name || "Non renseigne"}</strong>
        </div>
        <div className="client-summary-tile">
          <FileText size={18} aria-hidden />
          <span>Contrats</span>
          <strong>{contracts.length}</strong>
        </div>
        <div className="client-summary-tile">
          <Bell size={18} aria-hidden />
          <span>Notifications</span>
          <strong>{notifications.filter((notification) => !notification.is_read).length}</strong>
        </div>
      </section>

      <section className="client-portal-layout">
        <aside className="contract-list-panel">
          <div className="panel-title-row">
            <h2>Contrats</h2>
            <button
              className="icon-button"
              onClick={() => void loadPortal(selectedContractId)}
              title="Actualiser"
              type="button"
            >
              <RefreshCcw size={16} aria-hidden />
            </button>
          </div>
          <div className="contract-list">
            {contracts.length ? (
              contracts.map((contract) => (
                <button
                  className={
                    contract.id === selectedContractId ? "contract-row active" : "contract-row"
                  }
                  key={contract.id}
                  onClick={() => void handleContractChange(contract.id)}
                  type="button"
                >
                  <span>{contract.contract_number}</span>
                  <strong>{contract.vehicle_registration_number || "Vehicule non renseigne"}</strong>
                  <small>{contract.product_type || "Produit non renseigne"}</small>
                </button>
              ))
            ) : (
              <p className="empty-panel">Aucun contrat disponible.</p>
            )}
          </div>
        </aside>

        <section className="client-document-panel">
          {selectedContract && documents ? (
            <>
              <div className="document-heading">
                <div>
                  <p className="eyebrow">Contrat</p>
                  <h2>{selectedContract.contract_number}</h2>
                </div>
                <span className="status-pill">{selectedContract.status}</span>
              </div>

              <dl className="document-meta-grid">
                <div>
                  <dt>Vehicule</dt>
                  <dd>
                    {selectedContract.vehicle_brand} {selectedContract.vehicle_model}
                  </dd>
                </div>
                <div>
                  <dt>Immatriculation</dt>
                  <dd>{selectedContract.vehicle_registration_number || "Non renseignee"}</dd>
                </div>
                <div>
                  <dt>Reference attestation</dt>
                  <dd>{selectedContract.attestation_reference || "Non renseignee"}</dd>
                </div>
                <div>
                  <dt>Montant</dt>
                  <dd>{selectedContract.total_amount || "0.00"}</dd>
                </div>
              </dl>

              <div className="document-action-grid">
                <DocumentAction
                  available={documents.attestation_available}
                  documentKind="attestation"
                  label="Attestation"
                  onDownload={handleDownload}
                  onOtpRequest={handleOtpRequest}
                  otp={otpByKind.attestation}
                  setOtp={(value) =>
                    setOtpByKind((current) => ({ ...current, attestation: value }))
                  }
                  working={working}
                />
                <DocumentAction
                  available={documents.carte_brune_available}
                  documentKind="carte_brune"
                  label="Carte brune"
                  onDownload={handleDownload}
                  onOtpRequest={handleOtpRequest}
                  otp={otpByKind.carte_brune}
                  setOtp={(value) =>
                    setOtpByKind((current) => ({ ...current, carte_brune: value }))
                  }
                  working={working}
                />
              </div>
            </>
          ) : (
            <p className="empty-panel">Selectionnez un contrat.</p>
          )}
        </section>
      </section>
    </main>
  );
}

function DocumentAction({
  available,
  documentKind,
  label,
  onDownload,
  onOtpRequest,
  otp,
  setOtp,
  working,
}: {
  available: boolean;
  documentKind: ClientDocumentKind;
  label: string;
  onDownload: (documentKind: ClientDocumentKind) => Promise<void>;
  onOtpRequest: (documentKind: ClientDocumentKind) => Promise<void>;
  otp: string;
  setOtp: (value: string) => void;
  working: boolean;
}) {
  return (
    <div className="document-action">
      <div className="document-action-title">
        <FileCheck2 size={18} aria-hidden />
        <strong>{label}</strong>
        <span className={available ? "availability ok" : "availability"}>
          {available ? "Disponible" : "Indisponible"}
        </span>
      </div>
      <div className="otp-row">
        <input
          aria-label={`OTP ${label}`}
          disabled={!available || working}
          inputMode="numeric"
          maxLength={8}
          onChange={(event) => setOtp(event.target.value)}
          placeholder="OTP"
          value={otp}
        />
        <button
          className="secondary-button"
          disabled={!available || working}
          onClick={() => void onOtpRequest(documentKind)}
          type="button"
        >
          <ShieldCheck size={16} aria-hidden />
          OTP
        </button>
        <button
          className="primary-button"
          disabled={!available || working}
          onClick={() => void onDownload(documentKind)}
          type="button"
        >
          <Download size={16} aria-hidden />
          Ouvrir
        </button>
      </div>
    </div>
  );
}
