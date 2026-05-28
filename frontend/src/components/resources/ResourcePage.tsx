"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Edit3,
  Plus,
  RefreshCcw,
  Search,
  Trash2,
  X,
} from "lucide-react";

import {
  createResource,
  deleteResource,
  listResource,
  runResourceAction,
  updateResource,
} from "@/lib/api";
import { displayValue, formatDate, formatMoney } from "@/lib/format";
import {
  getResource,
  resourcesForRole,
  type ResourceAction,
  actionDisabledReason,
  canCreate,
  canDelete,
  canEdit,
} from "@/lib/resources";
import type { ApiRecord, PaginatedResponse } from "@/types/api";
import { useAuth } from "@/components/auth/AuthProvider";
import { ResourceDetails } from "@/components/resources/ResourceDetails";
import { ResourceForm } from "@/components/resources/ResourceForm";

type EditorState =
  | { mode: "create"; title: string; id?: never; record?: never }
  | { mode: "edit"; title: string; id: number | string; record: ApiRecord };

type GuardDialogState = {
  action: ResourceAction;
  confirmationInput: string;
  error: string;
  preview: unknown;
  previewLoading: boolean;
  record: ApiRecord;
  working: boolean;
};

export function ResourcePage({ slug }: { slug: string }) {
  const router = useRouter();
  const { user } = useAuth();
  const resource = getResource(slug);
  const isAllowed = useMemo(
    () => Boolean(resource && resourcesForRole(user?.role).some((item) => item.slug === slug)),
    [resource, slug, user?.role],
  );
  const [payload, setPayload] = useState<PaginatedResponse<ApiRecord> | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<ApiRecord | null>(null);
  const [editor, setEditor] = useState<EditorState | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [guardDialog, setGuardDialog] = useState<GuardDialogState | null>(null);

  async function load() {
    if (!resource || !isAllowed) {
      return;
    }

    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ page: String(page) });
      if (search.trim()) {
        params.set("search", search.trim());
      }
      setPayload(await listResource<ApiRecord>(resource.endpoint, params));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Chargement impossible");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [page, resource?.slug]);

  if (!resource) {
    return (
      <main className="page">
        <h1>Ressource introuvable</h1>
      </main>
    );
  }

  if (!isAllowed) {
    return (
      <main className="page">
        <h1>Acces non autorise</h1>
        <button className="secondary-button" onClick={() => router.replace("/dashboard")} type="button">
          Retour dashboard
        </button>
      </main>
    );
  }

  const activeResource = resource;
  const totalPages = payload ? Math.max(1, Math.ceil(payload.count / 20)) : 1;
  const canCreateResource = canCreate(activeResource);
  const canEditResource = canEdit(activeResource);
  const canDeleteResource = canDelete(activeResource);

  function openCreate() {
    if (!canCreateResource) {
      return;
    }
    setEditor({
      mode: "create",
      title: `Nouveau ${activeResource.singular}`,
    });
  }

  function openEdit(record: ApiRecord) {
    if (!canEditResource || record.id === undefined) {
      return;
    }
    setEditor({
      mode: "edit",
      id: record.id,
      record,
      title: `Modifier ${activeResource.singular} #${record.id}`,
    });
  }

  async function submitForm(formPayload: ApiRecord) {
    if (!editor) {
      return;
    }

    setError("");
    setNotice("");

    if (editor.mode === "create") {
      const saved = await createResource<ApiRecord>(activeResource.endpoint, formPayload);
      setSelectedRecord(saved);
      setNotice(`${activeResource.singular} cree.`);
    } else {
      const saved = await updateResource<ApiRecord>(
        activeResource.endpoint,
        editor.id,
        formPayload,
      );
      setSelectedRecord(saved);
      setNotice(`${activeResource.singular} mis a jour.`);
    }
    setEditor(null);
    await load();
  }

  async function handleDelete(record: ApiRecord) {
    if (!canDeleteResource || record.id === undefined) {
      return;
    }
    if (!window.confirm(`Supprimer ${activeResource.singular} #${record.id} ?`)) {
      return;
    }

    setError("");
    setNotice("");
    try {
      await deleteResource(activeResource.endpoint, record.id);
      setNotice(`${activeResource.singular} supprime.`);
      await load();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Suppression impossible");
    }
  }

  async function handleAction(record: ApiRecord, action: ResourceAction) {
    if (record.id === undefined) {
      return;
    }
    if (actionDisabledReason(record, action)) {
      return;
    }
    if (action.guard) {
      openGuardDialog(record, action);
      return;
    }
    if (action.confirm && !window.confirm(action.confirm)) {
      return;
    }

    await executeAction(record, action);
  }

  async function executeAction(record: ApiRecord, action: ResourceAction) {
    if (record.id === undefined) {
      return;
    }
    setError("");
    setNotice("");
    try {
      const actionResult = await runResourceAction<ApiRecord>(
        activeResource.endpoint,
        record.id,
        action.action,
      );
      setSelectedRecord(actionResult);
      setNotice(`${action.label} effectue.`);
      await load();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Action impossible");
    }
  }

  function openGuardDialog(record: ApiRecord, action: ResourceAction) {
    setError("");
    setNotice("");
    setGuardDialog({
      action,
      confirmationInput: "",
      error: "",
      preview: null,
      previewLoading: Boolean(action.guard?.preflightAction),
      record,
      working: false,
    });

    if (record.id === undefined || !action.guard?.preflightAction) {
      return;
    }

    void runResourceAction<unknown>(
      activeResource.endpoint,
      record.id,
      action.guard.preflightAction,
    )
      .then((preview) => {
        setGuardDialog((current) =>
          current?.record === record && current.action === action
            ? { ...current, preview, previewLoading: false }
            : current,
        );
      })
      .catch((caughtError) => {
        setGuardDialog((current) =>
          current?.record === record && current.action === action
            ? {
                ...current,
                error:
                  caughtError instanceof Error
                    ? caughtError.message
                    : "Previsualisation impossible.",
                previewLoading: false,
              }
            : current,
        );
      });
  }

  async function confirmGuardedAction() {
    if (!guardDialog) {
      return;
    }
    const { action, record } = guardDialog;
    if (!canConfirmGuardedAction(guardDialog)) {
      return;
    }

    setGuardDialog((current) =>
      current ? { ...current, error: "", working: true } : current,
    );
    setError("");
    setNotice("");
    try {
      const actionResult = await runResourceAction<ApiRecord>(
        activeResource.endpoint,
        record.id as number | string,
        action.action,
      );
      setSelectedRecord(actionResult);
      setNotice(`${action.label} effectue.`);
      setGuardDialog(null);
      await load();
    } catch (caughtError) {
      setGuardDialog((current) =>
        current
          ? {
              ...current,
              error: caughtError instanceof Error ? caughtError.message : "Action impossible",
              working: false,
            }
          : current,
      );
    }
  }

  function applySearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (page === 1) {
      load();
    } else {
      setPage(1);
    }
  }

  return (
    <main className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">
            {canCreateResource || canEditResource ? "Gestion" : "Consultation"}
          </p>
          <h1>{activeResource.label}</h1>
        </div>
        <div className="toolbar">
          <button className="secondary-button" onClick={load} type="button">
            <RefreshCcw size={16} />
            Actualiser
          </button>
          {canCreateResource ? (
            <button className="primary-button" onClick={openCreate} type="button">
              <Plus size={17} />
              Nouveau
            </button>
          ) : null}
        </div>
      </div>

      <form className="search-bar" onSubmit={applySearch}>
        <Search size={17} />
        <input
          placeholder="Recherche"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <button className="secondary-button" type="submit">
          Filtrer
        </button>
      </form>

      {error ? <p className="form-error">{error}</p> : null}
      {notice ? <p className="form-notice">{notice}</p> : null}

      <section className="table-frame" aria-busy={loading}>
        <table>
          <thead>
            <tr>
              {activeResource.columns.map((column) => (
                <th key={column.key}>{column.label}</th>
              ))}
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {payload?.results.length ? (
              payload.results.map((record) => (
                <tr key={String(record.id ?? JSON.stringify(record))}>
                  {activeResource.columns.map((column) => (
                    <td key={column.key}>{renderCell(record[column.key], column.kind)}</td>
                  ))}
                  <td className="row-actions">
                    <button className="tiny-button" onClick={() => setSelectedRecord(record)} type="button">
                      Details
                    </button>
                    {canEditResource || canDeleteResource ? (
                      <>
                        {canEditResource ? (
                          <button className="icon-button" onClick={() => openEdit(record)} title="Modifier" type="button">
                            <Edit3 size={15} />
                          </button>
                        ) : null}
                        {canDeleteResource ? (
                          <button className="icon-button danger" onClick={() => handleDelete(record)} title="Supprimer" type="button">
                            <Trash2 size={15} />
                          </button>
                        ) : null}
                      </>
                    ) : null}
                    {activeResource.actions?.map((action) => {
                      const disabledReason = actionDisabledReason(record, action);
                      return (
                        <button
                          className={action.guard ? "tiny-button danger" : "tiny-button"}
                          disabled={Boolean(disabledReason)}
                          key={action.action}
                          onClick={() => handleAction(record, action)}
                          title={disabledReason || action.label}
                          type="button"
                        >
                          {action.label}
                        </button>
                      );
                    })}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="empty-cell" colSpan={activeResource.columns.length + 1}>
                  {loading ? "Chargement..." : "Aucune donnee"}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <div className="pagination">
        <button
          className="icon-button text-button"
          disabled={page <= 1}
          onClick={() => setPage((current) => Math.max(1, current - 1))}
          type="button"
        >
          <ChevronLeft size={16} />
          Precedent
        </button>
        <span>
          Page {page} / {totalPages}
        </span>
        <button
          className="icon-button text-button"
          disabled={page >= totalPages}
          onClick={() => setPage((current) => current + 1)}
          type="button"
        >
          Suivant
          <ChevronRight size={16} />
        </button>
      </div>

      {editor ? (
        <aside className="side-panel" aria-label={editor.title}>
          <div className="panel-header">
            <strong>{editor.title}</strong>
            <button className="icon-button" onClick={() => setEditor(null)} title="Fermer" type="button">
              <X size={17} />
            </button>
          </div>
          <ResourceForm
            mode={editor.mode}
            onCancel={() => setEditor(null)}
            onSubmit={submitForm}
            record={editor.mode === "edit" ? editor.record : undefined}
            resource={activeResource}
          />
        </aside>
      ) : null}

      {selectedRecord ? (
        <aside className="side-panel" aria-label="Details">
          <div className="panel-header">
            <strong>Details</strong>
            <button className="icon-button" onClick={() => setSelectedRecord(null)} title="Fermer" type="button">
              <X size={17} />
            </button>
          </div>
          <ResourceDetails record={selectedRecord} resource={activeResource} />
        </aside>
      ) : null}

      {guardDialog ? (
        <GuardDialog
          state={guardDialog}
          onCancel={() => setGuardDialog(null)}
          onChange={(confirmationInput) =>
            setGuardDialog((current) =>
              current ? { ...current, confirmationInput } : current,
            )
          }
          onConfirm={confirmGuardedAction}
        />
      ) : null}
    </main>
  );
}

function GuardDialog({
  onCancel,
  onChange,
  onConfirm,
  state,
}: {
  onCancel: () => void;
  onChange: (value: string) => void;
  onConfirm: () => void;
  state: GuardDialogState;
}) {
  const guard = state.action.guard;
  if (!guard) {
    return null;
  }
  const canConfirm = canConfirmGuardedAction(state);

  return (
    <div className="dialog-backdrop">
      <section
        aria-labelledby="guard-dialog-title"
        aria-modal="true"
        className="confirm-dialog"
        role="dialog"
      >
        <div className="dialog-title-row">
          <AlertTriangle size={20} aria-hidden />
          <div>
            <p className="eyebrow">Action sensible</p>
            <h2 id="guard-dialog-title">{guard.title}</h2>
          </div>
        </div>

        <p className="dialog-description">{guard.description}</p>

        {guard.warningItems?.length ? (
          <ul className="guard-list">
            {guard.warningItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : null}

        {guard.preflightAction ? (
          <div className="preview-box">
            <strong>{guard.previewLabel ?? "Previsualisation"}</strong>
            {state.previewLoading ? <p>Chargement de la previsualisation...</p> : null}
            {state.error && !state.working ? <p className="form-error">{state.error}</p> : null}
            {!state.previewLoading && !state.error ? (
              <pre className="inline-json">{JSON.stringify(state.preview, null, 2)}</pre>
            ) : null}
          </div>
        ) : null}

        {!guard.preflightAction && state.error ? (
          <p className="form-error">{state.error}</p>
        ) : null}

        <label>
          Confirmation requise: saisir {guard.confirmationValue}
          <input
            autoComplete="off"
            disabled={state.working}
            onChange={(event) => onChange(event.target.value)}
            value={state.confirmationInput}
          />
        </label>

        <div className="dialog-actions">
          <button
            className="secondary-button"
            disabled={state.working}
            onClick={onCancel}
            type="button"
          >
            Annuler
          </button>
          <button
            className="primary-button danger-button"
            disabled={!canConfirm}
            onClick={onConfirm}
            type="button"
          >
            {state.working ? "Traitement..." : "Confirmer l'action"}
          </button>
        </div>
      </section>
    </div>
  );
}

function canConfirmGuardedAction(state: GuardDialogState) {
  const guard = state.action.guard;
  if (!guard || state.working || state.confirmationInput.trim() !== guard.confirmationValue) {
    return false;
  }
  if (guard.preflightAction) {
    return !state.previewLoading && !state.error && state.preview !== null;
  }
  return true;
}

function renderCell(value: unknown, kind?: "text" | "date" | "money" | "status" | "json") {
  if (kind === "date") {
    return formatDate(value);
  }
  if (kind === "money") {
    return formatMoney(value);
  }
  if (kind === "status") {
    return <span className="status-pill">{displayValue(value)}</span>;
  }
  return displayValue(value);
}
